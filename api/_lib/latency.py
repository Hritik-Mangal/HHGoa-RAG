from __future__ import annotations
import logging
import time
from contextlib import contextmanager
from typing import Optional

from api._lib.schemas import PipelineLatencies

_log = logging.getLogger(__name__)


class LatencyTracker:
    def __init__(self) -> None:
        self._marks: dict[str, float] = {}
        self._durations: dict[str, float] = {}
        self._pipeline_start: Optional[float] = None

    def start_pipeline(self) -> None:
        self._pipeline_start = time.perf_counter()

    @contextmanager
    def track(self, stage: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self._durations[stage] = (time.perf_counter() - t0) * 1000

    def record(self, stage: str, ms: float) -> None:
        self._durations[stage] = ms

    def elapsed_ms(self) -> float:
        if self._pipeline_start is None:
            return 0.0
        return (time.perf_counter() - self._pipeline_start) * 1000

    def to_schema(self) -> PipelineLatencies:
        d = self._durations
        if self._pipeline_start is None:
            _log.warning("to_schema called before start_pipeline — total_ms will be None")
            total = d.get("total")
        else:
            total = self.elapsed_ms()

        # Sum both guardrail stages so the schema field reflects the full guardrail cost.
        guardrail_q = d.get("guardrail_query", 0.0)
        guardrail_e = d.get("guardrail_evidence", 0.0)
        combined_guardrail = (guardrail_q + guardrail_e) or None

        return PipelineLatencies(
            stt_ms=d.get("stt"),
            embed_ms=d.get("embed"),
            retrieval_ms=d.get("retrieval"),
            guardrail_ms=combined_guardrail,
            generation_ms=d.get("generation"),
            total_ms=total,
        )
