"""Sarvam AI STT wrapper (Saaras v3 REST API)."""
from __future__ import annotations
import base64
import os
import time
from typing import Optional

import httpx

from api._lib.errors import EmptyTranscriptError, ProviderRateLimitError, STTError
from api._lib.schemas import STTResponse

_ENDPOINT = "https://api.sarvam.ai/speech-to-text"
_TIMEOUT = float(os.getenv("STT_TIMEOUT_MS", "8000")) / 1000


class SarvamSTT:
    def __init__(self) -> None:
        key = os.getenv("SARVAM_API_KEY")
        if not key:
            raise RuntimeError("SARVAM_API_KEY is not set")
        self._key = key
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def transcribe(
        self,
        audio_b64: str,
        fmt: str = "webm",
        language: str = "hi-IN",
        mime_type: Optional[str] = None,
    ) -> STTResponse:
        raw = base64.b64decode(audio_b64)
        filename = f"audio.{fmt}"
        # Strip codec parameters (e.g. "audio/webm;codecs=opus" → "audio/webm")
        # Some multipart servers reject MIME types with semicolons
        base_mime = (mime_type or "").split(";")[0].strip() or _mime(fmt)
        mime = base_mime

        t0 = time.perf_counter()
        try:
            resp = await self._client.post(
                _ENDPOINT,
                headers={"api-subscription-key": self._key},
                files={"file": (filename, raw, mime)},
                data={"model": "saaras:v3", "language_code": language},
            )
        except httpx.TransportError as exc:
            raise STTError(f"Sarvam network error: {exc}") from exc

        latency_ms = (time.perf_counter() - t0) * 1000

        if resp.status_code == 429:
            raise ProviderRateLimitError("Sarvam rate-limited")
        if resp.status_code != 200:
            raise STTError(f"Sarvam {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        transcript: str = data.get("transcript", "").strip()
        if not transcript:
            raise EmptyTranscriptError("Sarvam returned an empty transcript")

        return STTResponse(
            transcript=transcript,
            language=data.get("language_code", language),
            confidence=data.get("confidence"),
            latency_ms=latency_ms,
        )

    async def aclose(self) -> None:
        await self._client.aclose()


def _mime(fmt: str) -> str:
    return {
        "webm": "audio/webm",
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
    }.get(fmt, "application/octet-stream")
