from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


# Базовые (вшитые) теги
BUILTIN_TAGS: Dict[str, str] = {
    "petproject": "Личные/экспериментальные проекты.",
    "robots": "Всё, что связано с роботами и робототехникой.",
    "ai": "Идеи и материалы по искусственному интеллекту и ML.",
    "arxiv": "Статьи и материалы с arXiv.",
    "vla": "Заметки про VLA (вероятно, внутренняя аббревиатура, связанная с проектами/инфраструктурой).",
    "leshy": "Мой проект для роботов в Яндексе.",
    "personal": "Личные заметки, не связанные с работой.",
}


_TAGS_FILE = Path(__file__).with_name("tags_store.json")


def _load_user_tags() -> Dict[str, str]:
    if not _TAGS_FILE.exists():
        return {}
    try:
        data = json.loads(_TAGS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        # Принудительно приводим ключи/значения к str
        return {str(k): str(v) for k, v in data.items()}
    except Exception:
        # В случае любой ошибки просто игнорируем пользовательский файл
        return {}


def _save_user_tags(tags: Dict[str, str]) -> None:
    _TAGS_FILE.write_text(json.dumps(tags, ensure_ascii=False, indent=2), encoding="utf-8")


def get_all_tags() -> Dict[str, str]:
    """
    Объединённый словарь встроенных и пользовательских тегов.
    Пользовательские теги могут переопределять встроенные описания.
    """
    tags = dict(BUILTIN_TAGS)
    tags.update(_load_user_tags())
    # Сортировка по имени тега для красивого вывода
    return dict(sorted(tags.items(), key=lambda item: item[0]))


def add_or_update_tag(name: str, description: str) -> None:
    """
    Добавить или обновить пользовательский тег.
    """
    name = name.strip().lstrip("#")
    if not name:
        return

    user_tags = _load_user_tags()
    user_tags[name] = description.strip()
    _save_user_tags(user_tags)


def format_tags_help() -> str:
    tags = get_all_tags()
    lines = ["Известные теги и их описание:"]
    for tag, desc in tags.items():
        lines.append(f"- #{tag} — {desc}")
    return "\n".join(lines)


