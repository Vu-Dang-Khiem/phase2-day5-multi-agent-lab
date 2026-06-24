"""Tracing hooks with optional LangSmith integration."""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from time import perf_counter
from typing import Any

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)

_has_langsmith = False
_tracer = None

try:
    from langsmith import Client as LangSmithClient

    _has_langsmith = True
except ImportError:
    pass


def _get_tracer() -> Any:
    global _tracer
    settings = get_settings()
    if _tracer is None and _has_langsmith and settings.langsmith_api_key:
        try:
            _tracer = LangSmithClient(api_key=settings.langsmith_api_key)
            logger.info("LangSmith tracing enabled")
        except Exception:
            logger.warning("Failed to initialize LangSmith client")
    return _tracer


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Context manager that records timing and metadata for a named span."""
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    client = _get_tracer()
    run = None
    if client is not None:
        with suppress(Exception):
            run = client.create_run(
                name=name,
                inputs=attributes or {},
                run_type="chain",
            )
    try:
        yield span
    finally:
        elapsed = perf_counter() - started
        span["duration_seconds"] = elapsed
        if run is not None:
            with suppress(Exception):
                client.update_run(run.id, outputs={"duration_seconds": elapsed})
        logger.info("Span [%s] duration=%.3fs attrs=%s", name, elapsed, attributes)


def format_trace_report(state: "ResearchState") -> str:  # noqa: F821
    """Render a readable markdown trace report from the workflow state."""
    lines = [
        "# Trace Report",
        "",
        f"**Query:** {state.request.query}",
        f"**Iterations:** {state.iteration}",
        f"**Route history:** {' → '.join(state.route_history)}",
        f"**Errors:** {len(state.errors)}",
        "",
        "## Agent Results",
        "",
        "| Agent | Tokens (in/out) | Cost (USD) |",
        "|---|---:|---:|",
    ]
    for ar in state.agent_results:
        inp = ar.metadata.get("input_tokens", "?")
        out = ar.metadata.get("output_tokens", "?")
        cost = ar.metadata.get("cost_usd", "?")
        if isinstance(cost, float):
            cost = f"{cost:.6f}"
        lines.append(f"| {ar.agent.value} | {inp} / {out} | {cost} |")

    if state.trace:
        lines.extend(["", "## Event Trace", ""])
        for event in state.trace:
            payload = json.dumps(event.get("payload", {}), indent=2)
            lines.append(f"- **{event['name']}**: {payload}")

    lines.extend(["", "## Final Answer", "", state.final_answer or "(empty)", ""])
    return "\n".join(lines)
