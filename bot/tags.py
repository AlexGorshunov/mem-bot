from __future__ import annotations

TAGS_DESCRIPTION: dict[str, str] = {
    "petproject": "Личные/экспериментальные проекты.",
    "robot": "Всё, что связано с роботами и робототехникой.",
    "ai": "Идеи и материалы по искусственному интеллекту и ML.",
    "vla": "Заметки про VLA (вероятно, внутренняя аббревиатура, связанная с проектами/инфраструктурой).",
    "leshy": "Мой проект для роботов в Яндексе.",
    "personal": "Личные заметки, не связанные с работой.",
}


def format_tags_help() -> str:
    lines = ["Известные теги и их описание:"]
    for tag, desc in TAGS_DESCRIPTION.items():
        lines.append(f"- #{tag} — {desc}")
    return "\n".join(lines)


