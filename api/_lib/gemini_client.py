"""Google Gemini generation client (native REST, JSON mode enforced via responseMimeType)."""
from __future__ import annotations
import json
import os
import time
from typing import List

import httpx

from api._lib.errors import GenerationError, GenerationTimeoutError, ProviderRateLimitError
from api._lib.schemas import GenerationOutput, PassageChunk

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_TIMEOUT = float(os.getenv("GENERATION_TIMEOUT_MS", "500")) / 1000
_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_SYSTEM = """You are a precise, grounded question-answering assistant.
Rules:
1. Answer ONLY from the provided context passages. Do not invent facts.
2. If the context passages are unrelated to the query, set grounded=false and answer "I couldn't find relevant information for this question."
3. If context is insufficient, set grounded=false and say so clearly.
4. Keep answers concise (1-3 sentences max).
5. Never repeat phrases or words. If you notice yourself repeating, stop and summarise instead.
6. Return valid JSON matching this exact schema — nothing else, no extra text:
   {"answer": "<string>", "grounded": <bool>, "confidence": <0.0-1.0>, "sources": ["<chunk_id>", ...]}
   sources must be chunk_ids from the context; only include passages you actually used."""

_USER_TMPL = """Query: {query}

Context passages:
{context}

Respond with JSON only."""


class GeminiClient:
    def __init__(self) -> None:
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        self._key = key
        self._model = _MODEL
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def generate(
        self,
        query: str,
        passages: List[PassageChunk],
        model: str = "",
    ) -> GenerationOutput:
        active_model = model or self._model
        context = "\n\n".join(f"[{p.chunk_id}] {p.text}" for p in passages)
        user_msg = _USER_TMPL.format(query=query, context=context)

        url = f"{_BASE}/{active_model}:generateContent?key={self._key}"
        payload = {
            "systemInstruction": {"parts": [{"text": _SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
                "maxOutputTokens": 512,
            },
        }

        t0 = time.perf_counter()
        try:
            resp = await self._client.post(url, json=payload)
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("Gemini timed out") from exc
        except httpx.TransportError as exc:
            raise GenerationError(f"Gemini network error: {exc}") from exc

        if resp.status_code == 429:
            raise ProviderRateLimitError("Gemini rate-limited")
        if resp.status_code != 200:
            raise GenerationError(f"Gemini {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        try:
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise GenerationError(f"Unexpected Gemini response shape: {str(data)[:300]}") from exc

        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GenerationError(f"Gemini returned non-JSON: {raw[:200]}") from exc

        valid_ids = {p.chunk_id for p in passages}
        sources = [s for s in obj.get("sources", []) if s in valid_ids]

        return GenerationOutput(
            answer=str(obj.get("answer", "")).strip() or "No answer produced.",
            grounded=bool(obj.get("grounded", False)),
            confidence=float(max(0.0, min(1.0, obj.get("confidence", 0.5)))),
            sources=sources,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
