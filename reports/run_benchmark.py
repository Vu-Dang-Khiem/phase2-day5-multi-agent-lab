"""Run all 4 prompts from test_query.md and generate benchmark report."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from multi_agent_research_lab.cli import _single_agent
from multi_agent_research_lab.core.schemas import ResearchQuery, BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import format_trace_report
from multi_agent_research_lab.services.storage import LocalArtifactStore

configure_logging("INFO")

PROMPTS = {
    "research-agent-bench": """You are part of a university lab designing a benchmark to evaluate AI systems that assist students with research tasks.

Your task is to design a benchmark called ResearchAgentBench.

The benchmark should evaluate whether an AI system can actually help a graduate student complete research work, not just produce fluent text.

You must produce a full benchmark design document that includes:
1. Benchmark goal
2. Core assumptions
3. Task categories
4. At least 12 example tasks across different categories
5. A scoring rubric
6. Baselines to compare against
7. Likely failure modes and gaming risks
8. Human evaluation protocol
9. Limitations of the benchmark
10. Recommendations for version 2 of the benchmark

Constraints:
- The benchmark must be realistic for a small academic lab
- It must not depend on expensive annotation
- It must distinguish between usefulness, correctness, and research judgment
- It must include at least one adversarial or stress-test component
- It must explicitly discuss how systems might game the evaluation

Output format:
Write this as a mini design document suitable for discussion in a research lab meeting.
""",

    "multi-agent-briefing": """You are helping a PhD student prepare a research briefing on the topic:

"Do multi-agent LLM systems actually outperform single-agent systems on complex tasks?"

Your task is not just to summarize the topic. You must produce a structured research briefing that:
1. Defines the main claim precisely
2. Breaks the literature into major positions or schools of thought
3. Identifies arguments supporting the claim
4. Identifies arguments challenging the claim
5. Explains where empirical evidence is weak, incomplete, or confounded
6. Distinguishes between true multi-agent gains and gains caused by other factors such as more tokens, more prompt engineering, or repeated self-reflection
7. Proposes 3 concrete experiments that could better resolve the debate
8. Ends with a balanced final judgment

Constraints:
- Do not write a generic overview
- Explicitly discuss what kinds of evidence would count as convincing
- The final judgment must include uncertainty and unresolved issues
- Organize the answer so it could be used as speaking notes for a research group meeting

Output format:
- Core question
- Main positions
- Evidence for
- Evidence against
- Methodological concerns
- Proposed experiments
- Final judgment
""",

    "experiment-design": """You are designing a research experiment to compare a single-call LLM system with a multi-agent LLM system on complex research tasks.

Your deliverable must be a complete experimental plan.

You must include:
1. The research question
2. Hypotheses
3. Task design
4. Datasets or source materials
5. Fair comparison setup
6. Metrics
7. Human evaluation criteria
8. Statistical or methodological considerations
9. Expected results and alternative interpretations
10. A red-team section explaining how the experiment could be misleading, unfair, or easy to game
11. A revised experiment design after taking the red-team critique seriously

Constraints:
- You must explicitly address token budget fairness
- You must explain how to avoid giving the multi-agent system an unfair advantage
- You must discuss how to separate gains from decomposition vs gains from more inference time
- The red-team critique must be concrete, not superficial

Output format:
Write the answer as a structured internal lab proposal.
""",

    "survey-blueprint": """You are helping prepare a survey paper titled:

"AI Agents for Research Assistance: Capabilities, Evaluation, and Open Problems"

Your task is to create a detailed survey blueprint that a graduate student could actually use to write the paper.

You must produce:
1. A proposed paper title
2. A draft abstract
3. A section-by-section outline with 6 to 8 main sections
4. For each section:
   - purpose of the section
   - key themes
   - questions the section should answer
   - likely pitfalls
   - open problems
5. A final section identifying the most important evaluation gaps in current research
6. A section explaining what a strong future benchmark should measure

Constraints:
- The sections should not overlap too much
- The outline should feel like a real survey, not a blog post
- Open problems must be specific
- The final product should be useful as a writing plan, not just a topic list
""",
}

store = LocalArtifactStore()
all_metrics: list[BenchmarkMetrics] = []

for name, query in PROMPTS.items():
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")

    # Baseline (single-agent)
    print(f"\n--- Baseline: {name} ---")
    try:
        state_base, metrics_base = run_benchmark(
            f"baseline-{name}", query, _single_agent
        )
        all_metrics.append(metrics_base)
        trace_report = format_trace_report(state_base)
        store.write_text(f"traces/baseline-{name}.md", trace_report)
        print(f"  Latency: {metrics_base.latency_seconds:.2f}s")
        print(f"  Cost: {metrics_base.estimated_cost_usd}")
        print(f"  Quality: {metrics_base.quality_score}")
    except Exception as e:
        print(f"  Baseline FAILED: {e}")
    time.sleep(15)

    # Multi-agent
    print(f"\n--- Multi-Agent: {name} ---")
    try:
        def _multi_runner(q: str) -> ResearchState:
            state = ResearchState(request=ResearchQuery(query=q))
            return MultiAgentWorkflow().run(state)

        state_ma, metrics_ma = run_benchmark(f"multi-agent-{name}", query, _multi_runner)
        all_metrics.append(metrics_ma)
        trace_report = format_trace_report(state_ma)
        store.write_text(f"traces/multi-agent-{name}.md", trace_report)
        print(f"  Latency: {metrics_ma.latency_seconds:.2f}s")
        print(f"  Cost: {metrics_ma.estimated_cost_usd}")
        print(f"  Quality: {metrics_ma.quality_score}")
        print(f"  Route: {' -> '.join(state_ma.route_history)}")
    except Exception as e:
        print(f"  Multi-Agent FAILED: {e}")
    time.sleep(15)

# Generate report
report = render_markdown_report(all_metrics)
report_path = store.write_text("benchmark_report.md", report)
print(f"\n{'='*60}")
print(f"Report written to: {report_path}")
print(report)
