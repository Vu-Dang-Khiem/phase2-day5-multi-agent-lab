"""LangGraph workflow for multi-agent orchestration."""

import logging
from typing import Annotated, Any

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import (
    ROUTE_ANALYST,
    ROUTE_DONE,
    ROUTE_RESEARCHER,
    ROUTE_WRITER,
    SupervisorAgent,
)
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


def _dict_to_state(d: dict[str, Any]) -> ResearchState:
    return ResearchState(**d)


def _state_to_dict(s: ResearchState) -> dict[str, Any]:
    return s.model_dump()


def _replace(left: Any, right: Any) -> Any:
    return right


class WorkflowState(TypedDict):
    request: Annotated[dict[str, Any], _replace]
    iteration: Annotated[int, _replace]
    route_history: Annotated[list[str], _replace]
    sources: Annotated[list[dict[str, Any]], _replace]
    research_notes: Annotated[str | None, _replace]
    analysis_notes: Annotated[str | None, _replace]
    final_answer: Annotated[str | None, _replace]
    agent_results: Annotated[list[dict[str, Any]], _replace]
    trace: Annotated[list[dict[str, Any]], _replace]
    errors: Annotated[list[str], _replace]


def _supervisor_node(state: WorkflowState) -> dict[str, Any]:
    rs = _dict_to_state(state)
    with trace_span("agent.supervisor", {"iteration": rs.iteration}):
        return _state_to_dict(SupervisorAgent().run(rs))


def _researcher_node(state: WorkflowState) -> dict[str, Any]:
    rs = _dict_to_state(state)
    with trace_span("agent.researcher", {"query": rs.request.query}):
        return _state_to_dict(ResearcherAgent().run(rs))


def _analyst_node(state: WorkflowState) -> dict[str, Any]:
    rs = _dict_to_state(state)
    with trace_span("agent.analyst", {}):
        return _state_to_dict(AnalystAgent().run(rs))


def _writer_node(state: WorkflowState) -> dict[str, Any]:
    rs = _dict_to_state(state)
    with trace_span("agent.writer", {}):
        return _state_to_dict(WriterAgent().run(rs))


def _critic_node(state: WorkflowState) -> dict[str, Any]:
    rs = _dict_to_state(state)
    with trace_span("agent.critic", {}):
        return _state_to_dict(CriticAgent().run(rs))


def _router(state: WorkflowState) -> str:
    route_history = state.get("route_history", [])
    if not route_history:
        return END
    last_route = route_history[-1]
    logger.debug("Router: last route = %s", last_route)
    if last_route == ROUTE_DONE:
        return END
    return last_route


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph using LangGraph."""

    def __init__(self) -> None:
        self._graph = self._build()

    def run(self, state: ResearchState) -> ResearchState:
        logger.info("Starting multi-agent workflow")
        initial = _state_to_dict(state)
        with trace_span("workflow.run", {"query": state.request.query}):
            result = self._graph.invoke(initial)
        logger.info(
            "Workflow completed, route=%s",
            result.get("route_history", []),
        )
        return _dict_to_state(result)

    def _build(self) -> StateGraph:
        workflow = StateGraph(WorkflowState)

        workflow.add_node("supervisor", _supervisor_node)
        workflow.add_node("researcher", _researcher_node)
        workflow.add_node("analyst", _analyst_node)
        workflow.add_node("writer", _writer_node)
        workflow.add_node("critic", _critic_node)

        workflow.set_entry_point("supervisor")

        workflow.add_conditional_edges(
            "supervisor",
            _router,
            {
                ROUTE_RESEARCHER: "researcher",
                ROUTE_ANALYST: "analyst",
                ROUTE_WRITER: "writer",
                "critic": "critic",
                END: END,
            },
        )
        for worker in ("researcher", "analyst", "writer", "critic"):
            workflow.add_edge(worker, "supervisor")

        return workflow.compile()

    def get_trace(self, state: ResearchState) -> str:
        from multi_agent_research_lab.observability.tracing import format_trace_report

        return format_trace_report(state)
