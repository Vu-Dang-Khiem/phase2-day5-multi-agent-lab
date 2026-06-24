"""Benchmark report rendering with rich analysis."""

from datetime import datetime

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with comparison analysis."""
    lines = [
        "# Benchmark Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality (0-10) | Notes |",
        "|---|---:|---:|---:|:---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.6f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost}"
            f" | {quality} | {item.notes} |"
        )

    if len(metrics) >= 2:
        lines.extend([
            "",
            "## Comparison",
            "",
        ])
        pairs: dict[str, dict[str, BenchmarkMetrics]] = {}
        for m in metrics:
            key = m.run_name
            if key.startswith("baseline-"):
                kind = "baseline"
                prompt = key[len("baseline-"):]
            elif key.startswith("multi-agent-"):
                kind = "multi-agent"
                prompt = key[len("multi-agent-"):]
            else:
                kind = "other"
                prompt = key
            pairs.setdefault(prompt, {})[kind] = m
        for prompt, pair in sorted(pairs.items()):
            baseline = pair.get("baseline")
            multi = pair.get("multi-agent")
            if not baseline or not multi:
                continue
            bl = baseline.latency_seconds
            lat_diff = ((multi.latency_seconds - bl) / bl) * 100
            lat_str = f"{lat_diff:+.0f}%"
            qual_str = ""
            if baseline.quality_score is not None and multi.quality_score is not None:
                qual_diff = multi.quality_score - baseline.quality_score
                qual_str = f" ({qual_diff:+.1f} multi-agent vs baseline)"
            lines.append(
                f"- **{prompt}**: multi-agent latency {lat_str} vs baseline,"
                f" quality {multi.quality_score or '?'}/10{qual_str}"
            )

    lines.extend([
        "",
        "## Methodology",
        "",
        "- Latency: wall-clock time from query start to final answer.",
        "- Cost: estimated from token usage using provider pricing.",
        "- Quality: LLM-as-judge score (0-10) based on accuracy, completeness, clarity, citations.",
        "- Notes include citation coverage (fraction of sources cited in final answer).",
        "",
    ])
    return "\n".join(lines)
