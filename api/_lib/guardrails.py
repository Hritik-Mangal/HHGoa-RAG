"""Fast, torch-free guardrails — embedding similarity + heuristics."""
from __future__ import annotations
import os
import re
from typing import List, Optional

import numpy as np

from api._lib.schemas import GenerationOutput, GuardrailDecision, PassageChunk

# ---------------------------------------------------------------------------
# Unsafe / off-topic patterns (lightweight heuristics; supplement with threshold)
# ---------------------------------------------------------------------------
_UNSAFE_PATTERNS = re.compile(
    r"\b(bomb|kill|murder|suicide|porn|nude|hack|malware|weapon|explosive|terror)\b"
    r"|बम|बॉम्ब|विस्फोट|हत्या|आत्महत्या|हथियार|आतंक|बंदूक|बारूद|धमाका"
    r"|مار|بم|دھماکہ",  # Urdu variants
    re.IGNORECASE,
)

_OFF_TOPIC_PATTERNS = re.compile(
    r"\b(weather forecast|stock price|cricket score|live score|today.s match|"
    r"movie ticket|restaurant near|driving direction|traffic update|"
    r"lottery number|horoscope|astrology)\b",
    re.IGNORECASE,
)

_MIN_TRANSCRIPT_LEN = 3  # chars
_GROUNDING_SIM_THRESHOLD = 0.25  # cosine between answer embedding and best passage
_EVIDENCE_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.45"))


def check_query(transcript: str) -> GuardrailDecision:
    """Pre-retrieval query safety check."""
    t = transcript.strip()
    if len(t) < _MIN_TRANSCRIPT_LEN:
        return GuardrailDecision.OFF_TOPIC
    if _UNSAFE_PATTERNS.search(t):
        return GuardrailDecision.UNSAFE
    if _OFF_TOPIC_PATTERNS.search(t):
        return GuardrailDecision.OFF_TOPIC
    return GuardrailDecision.PASS


def check_evidence(passages: List[PassageChunk]) -> GuardrailDecision:
    """Post-retrieval evidence sufficiency check."""
    if not passages:
        return GuardrailDecision.NO_EVIDENCE
    best_score = max(p.score or 0.0 for p in passages)
    if best_score < _EVIDENCE_THRESHOLD:
        return GuardrailDecision.NO_EVIDENCE
    return GuardrailDecision.PASS


def verify_grounding(
    output: GenerationOutput,
    passages: List[PassageChunk],
) -> bool:
    """Post-generation grounding: verify model's claimed sources exist in retrieved set."""
    if not output.grounded:
        return False
    if not output.sources:
        return False
    retrieved_ids = {p.chunk_id for p in passages}
    # At least one source must be from what was actually retrieved
    valid_source_count = sum(1 for s in output.sources if s in retrieved_ids)
    return valid_source_count > 0 and output.confidence >= 0.4


# Canned refusal messages keyed by decision
REFUSAL_MESSAGES: dict[GuardrailDecision, str] = {
    GuardrailDecision.UNSAFE: (
        "I'm not able to help with that request."
    ),
    GuardrailDecision.OFF_TOPIC: (
        "That question is outside the scope of this knowledge base. "
        "Try asking about a topic covered in MSMARCO."
    ),
    GuardrailDecision.NO_EVIDENCE: (
        "I couldn't find sufficient evidence in the knowledge base to answer that question reliably."
    ),
}
