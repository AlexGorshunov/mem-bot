from __future__ import annotations

from typing import Iterable

from telegram import Update
from telegram.ext import ContextTypes

from .abacus_client import AbacusClient
from .mem_client import MemClient
from .state import USER_PENDING_NOTES, PendingNote
from .voice_utils import transcribe_audio


abacus_client = AbacusClient()
mem_client = MemClient()


def _parse_tags(text: str) -> list[str]:
    # Разрешаем разделители: запятая, точка с запятой, перенос строки, пробел
    raw = text.replace(";", ",").replace("\n", ",")
    parts: Iterable[str] = (p.strip() for p in raw.split(","))
    tags: list[str] = []
    for p in parts:
        if not p:
            continue
        if p.startswith("#"):
            p = p.lstrip("#")
        if p:
            tags.append(p)
    return tags


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я бот, который сохраняет твои мысли в Mem.ai.\n\n"
        "Отправь текст, голосовое или фото — я сохраню заметку, "
        "а затем попрошу тебя прислать теги."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    user_id = update.effective_user.id
    text = update.message.text or ""

    # Если для пользователя уже есть ожидающая заметка — воспринимаем текст как теги
    if user_id in USER_PENDING_NOTES:
        await handle_tags(update, context)
        return

    await update.message.reply_text("Обрабатываю текст через Abacus LLM...")
    expanded = await abacus_client.expand_text(text)

    mem_content = expanded
    mem_resp = await mem_client.create_note(mem_content)
    note_id = mem_resp.get("id") or mem_resp.get("noteId") or ""

    USER_PENDING_NOTES[user_id] = PendingNote(
        note_id=note_id,
        original_content=mem_content,
    )

    await update.message.reply_text(
        "Записал мысль в Mem.ai.\n"
        "Теперь отправь сообщение с тегами (через запятую, можно с `#`)."
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    user_id = update.effective_user.id
    voice = update.message.voice or update.message.audio

    if not voice:
        await update.message.reply_text("Не удалось получить голосовое сообщение.")
        return

    file = await voice.get_file()
    file_path = f"/tmp/{voice.file_unique_id}.ogg"
    await file.download_to_drive(file_path)

    await update.message.reply_text("Преобразую голос в текст...")
    transcript = await transcribe_audio(file_path)

    # При желании можно также прогнать transcript через Abacus; пока отправим как есть
    mem_content = transcript
    mem_resp = await mem_client.create_note(mem_content)
    note_id = mem_resp.get("id") or mem_resp.get("noteId") or ""

    USER_PENDING_NOTES[user_id] = PendingNote(
        note_id=note_id,
        original_content=mem_content,
    )

    await update.message.reply_text(
        "Голосовое сохранено в Mem.ai.\n"
        "Теперь отправь сообщение с тегами для этой заметки."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    user_id = update.effective_user.id

    if not update.message.photo:
        await update.message.reply_text("Не удалось получить фото.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_url = file.file_path  # Телеграмовская ссылка на файл
    caption = update.message.caption or ""

    mem_content = f"Фото: {file_url}\n\n{caption}".strip()
    mem_resp = await mem_client.create_note(mem_content)
    note_id = mem_resp.get("id") or mem_resp.get("noteId") or ""

    USER_PENDING_NOTES[user_id] = PendingNote(
        note_id=note_id,
        original_content=mem_content,
    )

    await update.message.reply_text(
        "Фото сохранено в Mem.ai.\n"
        "Теперь отправь сообщение с тегами для этой заметки."
    )


async def handle_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    user_id = update.effective_user.id
    text = update.message.text or ""

    pending = USER_PENDING_NOTES.get(user_id)
    if not pending:
        await update.message.reply_text(
            "Сначала отправь текст, голосовое или фото, чтобы я создал заметку."
        )
        return

    tags = _parse_tags(text)
    tags_str = ", ".join(f"#{t}" for t in tags) if tags else text.strip()

    new_content = f"{pending.original_content}\n\nТеги: {tags_str}".strip()

    await update.message.reply_text("Добавляю теги к заметке в Mem.ai...")
    await mem_client.update_note_content(pending.note_id, new_content)

    USER_PENDING_NOTES.pop(user_id, None)

    await update.message.reply_text("Готово! Теги добавлены. Можешь отправить следующую мысль.")


