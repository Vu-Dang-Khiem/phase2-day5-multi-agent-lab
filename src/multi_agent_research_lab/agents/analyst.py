"""Analyst agent that turns research notes into structured insights."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

ANALYST_SYSTEM_PROMPT = (
    "You are a critical analyst. Given research notes, extract key claims, "
    "compare viewpoints, flag weak evidence, and identify gaps. "
    "Structure your analysis as: Key Claims, Evidence Quality, Viewpoints, Gaps."
)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes:
            logger.warning("No research notes to analyze; skipping")
            return state

        user_prompt = (
            f"Query: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Target audience: {state.request.audience}\n\n"
            "Provide structured analysis with key claims, evidence quality, "
            "different viewpoints, and gaps or weaknesses."
        )
        response = self._llm.complete(ANALYST_SYSTEM_PROMPT, user_prompt)
        state.analysis_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("analyst.run", {})
        return state
