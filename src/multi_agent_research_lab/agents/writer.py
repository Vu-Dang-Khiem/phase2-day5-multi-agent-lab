"""Writer agent that produces the final answer."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

WRITER_SYSTEM_PROMPT = (
    "You are a skilled technical writer. Synthesize research notes and analysis "
    "into a clear, well-structured final answer. Include citations from sources. "
    "Adapt the depth and tone for the target audience."
)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        if not state.research_notes:
            logger.warning("No research notes available; writer cannot produce answer")
            return state

        analysis = state.analysis_notes or "No analysis available."

        sources_text = "\n".join(
            f"- {s.title}" + (f" ({s.url})" if s.url else "")
            for s in state.sources
        )

        user_prompt = (
            f"Query: {state.request.query}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Analysis:\n{analysis}\n\n"
            f"Sources:\n{sources_text}\n\n"
            f"Target audience: {state.request.audience}\n\n"
            "Write a comprehensive final answer with proper citations."
        )
        response = self._llm.complete(WRITER_SYSTEM_PROMPT, user_prompt)
        state.final_answer = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("writer.run", {})
        return state
