import os

from dotenv import load_dotenv


load_dotenv()


TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

ABACUS_API_KEY: str | None = os.getenv("ABACUS_API_KEY")
ABACUS_BASE_URL: str = os.getenv("ABACUS_BASE_URL", "https://routellm.abacus.ai/v1")
ABACUS_MODEL: str = os.getenv("ABACUS_MODEL", "route-llm")

MEM_API_KEY: str | None = os.getenv("MEM_API_KEY")
MEM_API_BASE_URL: str = os.getenv("MEM_API_BASE_URL", "https://api.mem.ai/v2")


def validate_config() -> None:
    missing: list[str] = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not ABACUS_API_KEY:
        missing.append("ABACUS_API_KEY")
    if not MEM_API_KEY:
        missing.append("MEM_API_KEY")

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


