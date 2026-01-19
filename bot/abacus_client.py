from __future__ import annotations

import httpx

from .config import ABACUS_API_KEY, ABACUS_BASE_URL, ABACUS_MODEL


class AbacusClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.api_key = api_key or ABACUS_API_KEY
        self.base_url = (base_url or ABACUS_BASE_URL).rstrip("/")

        if not self.api_key:
            raise RuntimeError("ABACUS_API_KEY is not set")

    async def _chat(self, messages: list[dict]) -> str:
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": ABACUS_MODEL,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]

    async def expand_text(self, text: str) -> str:
        """
        Вызывает Abacus RouteLLM (OpenAI-совместимую) для развёртывания мысли.
        """
        system_prompt = (
            "Ты помощник, который помогает пользователю развёртывать краткие мысли "
            "в более подробные и структурированные заметки для персональной базы знаний."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        return await self._chat(messages)

    async def summarize_pdf(self, text: str, target_lang: str = "ru") -> str:
        """
        Перевод и объяснение сути PDF-документа.
        """
        system_prompt = (
            "Ты помощник, который получает текст PDF-документа и должен:\n"
            "1) Кратко и понятно изложить его суть и ключевые идеи.\n"
            f"2) Перевести и объяснить содержание на {target_lang} языке.\n"
            "Ответ дай в виде структурированной заметки (заголовки, списки по необходимости)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        return await self._chat(messages)


