"""Command-line entrypoint for the lab."""

import logging
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import format_trace_report
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()
logger = logging.getLogger(__name__)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _single_agent(query: str) -> ResearchState:
    """Run a single-agent pipeline: LLM-only research and writing."""
    llm = LLMClient()
    state = ResearchState(request=ResearchQuery(query=query))

    response = llm.complete(
        "You are a knowledgeable research assistant. Answer the query thoroughly.",
        f"Query: {query}\nTarget audience: {state.request.audience}",
    )
    state.research_notes = response.content
    writer = WriterAgent()
    state = writer.run(state)
    state.add_trace_event(
        "baseline.run",
        {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": response.cost_usd,
        },
    )
    return state


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline using a real LLM call."""
    _init()
    state = _single_agent(query)
    display = state.final_answer or state.research_notes or "No output produced."
    console.print(Panel.fit(display, title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    trace: Annotated[bool, typer.Option("--trace", "-t", help="Show trace report")] = False,
) -> None:
    """Run the multi-agent workflow with Supervisor + Researcher + Analyst + Writer."""
    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    display = result.final_answer or "No output produced."
    console.print(Panel.fit(display, title="Multi-Agent Result"))
    console.print(f"Iterations: {result.iteration}")
    for ar in result.agent_results:
        console.print(f"  {ar.agent.value}: {ar.metadata.get('cost_usd', '?')} USD")
    if trace:
        console.print(Panel.fit(format_trace_report(result), title="Trace Report"))


@app.command()
def trace(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run multi-agent and display detailed trace report."""
    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    result = workflow.run(state)
    console.print(Panel.fit(format_trace_report(result), title="Trace Report"))


if __name__ == "__main__":
    app()
