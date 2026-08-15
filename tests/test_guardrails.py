import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from api._lib.guardrails import check_evidence, check_query, verify_grounding
from api._lib.schemas import GenerationOutput, GuardrailDecision, PassageChunk


def _make_passage(chunk_id: str, score: float = 0.5) -> PassageChunk:
    return PassageChunk(
        chunk_id=chunk_id,
        doc_id="d1",
        passage_id="p1",
        text="Some relevant passage text about the topic.",
        lang="en",
        strategy="D",
        score=score,
    )


class TestCheckQuery:
    def test_safe_query_passes(self):
        assert check_query("What is photosynthesis?") == GuardrailDecision.PASS

    def test_unsafe_query_blocked(self):
        assert check_query("How to make a bomb at home?") == GuardrailDecision.UNSAFE

    def test_off_topic_query_blocked(self):
        assert check_query("What is today's weather forecast?") == GuardrailDecision.OFF_TOPIC

    def test_empty_query_blocked(self):
        assert check_query("") == GuardrailDecision.OFF_TOPIC

    def test_very_short_blocked(self):
        assert check_query("hi") == GuardrailDecision.OFF_TOPIC

    def test_hindi_query_passes(self):
        assert check_query("भारत की राजधानी क्या है?") == GuardrailDecision.PASS


class TestCheckEvidence:
    def test_sufficient_evidence(self):
        passages = [_make_passage("c1", score=0.6), _make_passage("c2", score=0.45)]
        assert check_evidence(passages) == GuardrailDecision.PASS

    def test_empty_passages_rejected(self):
        assert check_evidence([]) == GuardrailDecision.NO_EVIDENCE

    def test_low_score_passages_rejected(self):
        passages = [_make_passage("c1", score=0.1), _make_passage("c2", score=0.05)]
        assert check_evidence(passages) == GuardrailDecision.NO_EVIDENCE

    def test_threshold_boundary(self):
        # Exactly at threshold should pass
        passages = [_make_passage("c1", score=0.30)]
        assert check_evidence(passages) == GuardrailDecision.PASS


class TestVerifyGrounding:
    def test_grounded_with_valid_sources(self):
        passages = [_make_passage("c1", 0.7), _make_passage("c2", 0.55)]
        out = GenerationOutput(answer="A.", grounded=True, confidence=0.8, sources=["c1"])
        assert verify_grounding(out, passages) is True

    def test_ungrounded_flag_returns_false(self):
        passages = [_make_passage("c1", 0.7)]
        out = GenerationOutput(answer="A.", grounded=False, confidence=0.8, sources=["c1"])
        assert verify_grounding(out, passages) is False

    def test_hallucinated_source_rejected(self):
        passages = [_make_passage("c1", 0.7)]
        out = GenerationOutput(answer="A.", grounded=True, confidence=0.9, sources=["FAKE_ID"])
        assert verify_grounding(out, passages) is False

    def test_low_confidence_rejected(self):
        passages = [_make_passage("c1", 0.7)]
        out = GenerationOutput(answer="A.", grounded=True, confidence=0.2, sources=["c1"])
        assert verify_grounding(out, passages) is False
