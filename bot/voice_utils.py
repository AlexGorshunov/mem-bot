from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import whisper

logger = logging.getLogger(__name__)

# Кэш для модели Whisper (загружается один раз)
_whisper_model: whisper.Whisper | None = None
_whisper_model_name = "base"  # Можно использовать "tiny", "base", "small", "medium", "large"


def _get_whisper_model() -> whisper.Whisper:
    """
    Получить модель Whisper (загружается один раз, затем кэшируется).
    """
    global _whisper_model
    if _whisper_model is None:
        logger.info(f"Загрузка модели Whisper: {_whisper_model_name}")
        _whisper_model = whisper.load_model(_whisper_model_name)
        logger.info("Модель Whisper загружена")
    return _whisper_model


async def transcribe_audio(file_path: str) -> str:
    """
    Транскрибация аудио через Whisper.

    Поддерживает различные форматы аудио (OGG, MP3, WAV и др.),
    так как Whisper использует ffmpeg под капотом.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Аудиофайл не найден: {file_path}")

    try:
        # Загружаем модель (кэшируется после первого вызова)
        model = _get_whisper_model()

        # Запускаем транскрибацию в отдельном потоке, чтобы не блокировать event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(file_path, language="ru", task="transcribe"),
        )

        transcript = result.get("text", "").strip()
        if not transcript:
            return "[Не удалось распознать речь]"

        return transcript

    except Exception as e:
        logger.error(f"Ошибка при транскрибации аудио: {e}", exc_info=True)
        return f"[Ошибка транскрибации: {str(e)}]"


