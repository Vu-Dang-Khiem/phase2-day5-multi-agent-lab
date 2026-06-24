"""Benchmark for single-agent vs multi-agent comparison."""

import logging
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

Runner = Callable[[str], ResearchState]

QUALITY_JUDGE_SYSTEM_PROMPT = (
    "You are an impartial judge evaluating research answers. "
    "Rate the following answer on a scale of 0-10 based on: "
    "accuracy, completeness, clarity, and citation use. "
    "Return only a number 0-10."
)


def _score_quality(state: ResearchState) -> float:
    if not state.final_answer:
        return 0.0
    try:
        llm = LLMClient()
        resp = llm.complete(
            QUALITY_JUDGE_SYSTEM_PROMPT,
            f"Query: {state.request.query}\n\nAnswer:\n{state.final_answer}",
        )
        score = float(resp.content.strip())
        return max(0.0, min(10.0, score))
    except Exception as exc:
        logger.warning("Quality scoring failed: %s", exc)
        return 0.0


def _estimate_cost(state: ResearchState) -> float:
    total = 0.0
    for ar in state.agent_results:
        total += ar.metadata.get("cost_usd", 0.0) or 0.0
    return total


def _citation_coverage(state: ResearchState) -> float:
    if not state.final_answer or not state.sources:
        return 0.0
    answer_lower = state.final_answer.lower()
    covered = 0
    for s in state.sources:
        if s.title.lower() in answer_lower or s.snippet and s.snippet.lower()[:50] in answer_lower:
            covered += 1
    return covered / len(state.sources)


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, quality, and citation coverage."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    quality = _score_quality(state)
    cost = _estimate_cost(state)
    coverage = _citation_coverage(state)

    notes = f"citation_coverage={coverage:.0%}"
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=cost,
        quality_score=quality,
        notes=notes,
    )
    pct = coverage * 100
    logger.info(
        "Benchmark %s: latency=%.2fs cost=%.6f quality=%.1f coverage=%.0f pct",
        run_name, latency, cost, quality, pct,
    )
    return state, metrics
