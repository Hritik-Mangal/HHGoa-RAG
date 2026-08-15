"""Groq generation client (OpenAI-compatible, JSON-mode, structured output)."""
from __future__ import annotations
import json
import os
import time
from typing import List

import httpx

from api._lib.errors import GenerationError, GenerationTimeoutError, ProviderRateLimitError
from api._lib.schemas import GenerationOutput, PassageChunk

_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
_TIMEOUT = float(os.getenv("GENERATION_TIMEOUT_MS", "500")) / 1000
_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

_SYSTEM = """You are a precise, grounded question-answering assistant.
Rules:
1. Answer ONLY from the provided context passages. Do not invent facts.
2. If context is insufficient or irrelevant, set grounded=false and say so.
3. Keep answers concise (1-3 sentences max).
4. Return valid JSON matching this exact schema:
   {"answer": "<string>", "grounded": <bool>, "confidence": <0.0-1.0>, "sources": ["<chunk_id>", ...]}
   sources must be chunk_ids from the context; only include passages you actually used."""

_USER_TMPL = """Query: {query}

Context passages:
{context}

Respond with JSON only."""


class GroqClient:
    def __init__(self) -> None:
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is not set")
        self._headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def generate(
        self,
        query: str,
        passages: List[PassageChunk],
        model: str = _MODEL,
    ) -> GenerationOutput:
        context = "\n\n".join(
            f"[{p.chunk_id}] {p.text}" for p in passages
        )
        user_msg = _USER_TMPL.format(query=query, context=context)

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
            "max_tokens": 256,
        }

        t0 = time.perf_counter()
        try:
            resp = await self._client.post(_ENDPOINT, headers=self._headers, json=payload)
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("Groq timed out") from exc
        except httpx.TransportError as exc:
            raise GenerationError(f"Groq network error: {exc}") from exc

        elapsed = (time.perf_counter() - t0) * 1000

        if resp.status_code == 429:
            raise ProviderRateLimitError("Groq rate-limited")
        if resp.status_code != 200:
            raise GenerationError(f"Groq {resp.status_code}: {resp.text[:500]}")

        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GenerationError(f"Groq returned non-JSON: {raw[:200]}") from exc

        # Validate sources are from the provided passages
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
