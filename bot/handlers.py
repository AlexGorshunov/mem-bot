from __future__ import annotations

from typing import Iterable

from telegram import Update
from telegram.ext import ContextTypes

from .abacus_client import AbacusClient
from .mem_client import MemClient
from .state import USER_PENDING_NOTES, PendingNote
from .voice_utils import transcribe_audio
from .pdf_utils import extract_pdf_text
from .tags import format_tags_help, add_or_update_tag


abacus_client = AbacusClient()
mem_client = MemClient()

# Единственный разрешённый username
ALLOWED_USERNAME = "AlexGorshunov"


def _is_authorized(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    return (user.username or "") == ALLOWED_USERNAME


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
    if not _is_authorized(update):
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    await update.message.reply_text(
        "Привет! Я бот, который сохраняет твои мысли в Mem.ai.\n\n"
        "Отправь текст, голосовое, фото или PDF — я сохраню заметку.\n"
        "Теги можешь добавлять прямо в сообщение (например: #petproject #ai).\n"
        "Команда /tags покажет все известные теги с описанием."
    )


async def show_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        assert update.message is not None
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    assert update.message is not None
    await update.message.reply_text(format_tags_help())


async def add_tag_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /addtag <имя_тега> <описание>
    Пример:
      /addtag arxiv Статьи с arXiv по ML и ИИ
    """
    if not _is_authorized(update):
        assert update.message is not None
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    assert update.message is not None
    text = update.message.text or ""

    # Ожидаем как минимум три части: /addtag, имя, описание
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text(
            "Использование: /addtag <имя_тега> <описание>\n"
            "Пример: /addtag arxiv Статьи с arXiv по ML и ИИ"
        )
        return

    _, raw_name, description = parts
    name = raw_name.lstrip("#").strip()
    description = description.strip()

    if not name or not description:
        await update.message.reply_text(
            "Имя тега и описание не должны быть пустыми.\n"
            "Пример: /addtag arxiv Статьи с arXiv по ML и ИИ"
        )
        return

    add_or_update_tag(name, description)
    await update.message.reply_text(
        f"Тег добавлен/обновлён: #{name}\n"
        "Он теперь будет отображаться в списке /tags."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        assert update.message is not None
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    assert update.message is not None
    text = update.message.text or ""

    await update.message.reply_text("Обрабатываю текст через Abacus LLM...")
    expanded = await abacus_client.expand_text(text)

    # Теги ты можешь указывать прямо в сообщении, они останутся в тексте.
    mem_content = expanded
    mem_resp = await mem_client.create_note(mem_content)

    await update.message.reply_text(
        "Записал мысль в Mem.ai.\n"
        "Теги можно указывать прямо в тексте сообщения (например: #project, #idea)."
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        assert update.message is not None
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    assert update.message is not None
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
    # Теги при желании можно проговаривать/обозначать в конце, но они просто попадут в текст.
    mem_content = transcript
    mem_resp = await mem_client.create_note(mem_content)

    await update.message.reply_text(
        "Голосовое (текст) сохранено в Mem.ai.\n"
        "Если хочешь теги, просто включай их в содержание (например: #meeting, #voice)."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update):
        assert update.message is not None
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    assert update.message is not None

    if not update.message.photo:
        await update.message.reply_text("Не удалось получить фото.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_url = file.file_path  # Телеграмовская ссылка на файл
    caption = update.message.caption or ""

    # Теги можешь указать прямо в caption.
    mem_content = f"Фото: {file_url}\n\n{caption}".strip()
    mem_resp = await mem_client.create_note(mem_content)

    await update.message.reply_text(
        "Фото сохранено в Mem.ai.\n"
        "Можешь добавлять теги прямо в подпись к фото."
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработка PDF: скачиваем, вытаскиваем текст, просим LLM перевести и объяснить,
    создаём заметку в Mem и затем просим теги.
    """
    if not _is_authorized(update):
        assert update.message is not None
        await update.message.reply_text("Ты не мой создатель, я тебя не знаю и не дружу с тобой!")
        return

    assert update.message is not None

    doc = update.message.document
    if not doc:
        await update.message.reply_text("Не удалось получить документ.")
        return

    if not (doc.mime_type == "application/pdf" or doc.file_name.lower().endswith(".pdf")):
        await update.message.reply_text("Сейчас я поддерживаю только PDF-документы.")
        return

    file = await doc.get_file()
    file_path = f"/tmp/{doc.file_unique_id}.pdf"
    await file.download_to_drive(file_path)

    await update.message.reply_text("Читаю PDF и отправляю в LLM для перевода и объяснения сути...")
    raw_text = extract_pdf_text(file_path)

    summarized = await abacus_client.summarize_pdf(raw_text, target_lang="ru")

    # В итоговой заметке можешь сразу добавить теги в тексте, если нужно.
    mem_content = summarized
    mem_resp = await mem_client.create_note(mem_content)

    await update.message.reply_text(
        "Создал заметку по PDF в Mem.ai.\n"
        "Теги можешь включать прямо в текст PDF (или добавить в следующем документе/сообщении)."
    )


async def handle_tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Функция больше не используется: теги указываются прямо в сообщении.
    return


