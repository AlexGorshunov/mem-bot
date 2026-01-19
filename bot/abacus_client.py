from __future__ import annotations

import httpx

from .config import ABACUS_API_KEY, ABACUS_BASE_URL, ABACUS_MODEL


class AbacusClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or ABACUS_API_KEY
        self.base_url = (base_url or ABACUS_BASE_URL).rstrip("/")

        if not self.api_key:
            raise RuntimeError("ABACUS_API_KEY is not set")

    async def expand_text(self, text: str) -> str:
        """
        Вызывает Abacus RouteLLM (OpenAI-совместимую) для развёртывания мысли.
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        system_prompt = (
            "Ты помощник, который помогает пользователю развёртывать краткие мысли "
            "в более подробные и структурированные заметки для персональной базы знаний."
        )

        payload = {
            "model": ABACUS_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]


