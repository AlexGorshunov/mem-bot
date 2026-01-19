from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PendingNote:
    note_id: str
    original_content: str


# Простейшее in‑memory состояние: user_id -> PendingNote
USER_PENDING_NOTES: dict[int, PendingNote] = {}


