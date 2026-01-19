from __future__ import annotations

import httpx

from .config import MEM_API_KEY, MEM_API_BASE_URL


class MemClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or MEM_API_KEY
        self.base_url = (base_url or MEM_API_BASE_URL).rstrip("/")

        if not self.api_key:
            raise RuntimeError("MEM_API_KEY is not set")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_note(self, content: str) -> dict:
        """
        Создаёт заметку в Mem.ai (v2 /notes).
        Возвращает JSON ответа (где есть id заметки).
        """
        url = f"{self.base_url}/notes"
        payload = {
            "content": content,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def update_note_content(self, note_id: str, content: str) -> dict:
        """
        Обновляет содержимое заметки, чтобы в конец дописать теги.
        """
        url = f"{self.base_url}/notes/{note_id}"
        payload = {
            "content": content,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.patch(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()


