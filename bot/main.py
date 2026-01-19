from __future__ import annotations

import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import TELEGRAM_BOT_TOKEN, validate_config
from . import handlers


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    validate_config()

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("tags", handlers.show_tags))

    # Фото
    application.add_handler(
        MessageHandler(filters.PHOTO & ~filters.COMMAND, handlers.handle_photo)
    )

    # Голосовые / аудио
    application.add_handler(
        MessageHandler(
            (filters.VOICE | filters.AUDIO) & ~filters.COMMAND,
            handlers.handle_voice,
        )
    )

    # Документы (PDF)
    application.add_handler(
        MessageHandler(
            filters.Document.PDF & ~filters.COMMAND,
            handlers.handle_document,
        )
    )

    # Текст (и основной поток, и теги — роутер внутри handle_text)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text)
    )

    logger.info("Starting Telegram → Abacus → Mem bot (long polling)...")
    application.run_polling()


if __name__ == "__main__":
    main()


