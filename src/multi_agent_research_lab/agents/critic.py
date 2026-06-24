"""Optional critic agent for fact-checking and safety review."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = (
    "You are a fact-checker and safety reviewer. Review the final answer for: "
    "1) factual accuracy, 2) hallucination risks, 3) citation coverage, "
    "4) safety or bias concerns. Provide a pass/fail and actionable feedback."
)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        if not state.final_answer:
            logger.warning("No final answer to review; skipping critic")
            return state

        sources_text = "\n".join(
            f"- {s.title}" + (f" ({s.url})" if s.url else "")
            for s in state.sources
        )
        user_prompt = (
            f"Query: {state.request.query}\n\n"
            f"Final Answer:\n{state.final_answer}\n\n"
            f"Sources:\n{sources_text}\n\n"
            "Review the answer for factual accuracy, hallucination, "
            "citation coverage, and safety concerns. Provide a verdict."
        )
        response = self._llm.complete(CRITIC_SYSTEM_PROMPT, user_prompt)

        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=response.content,
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("critic.run", {"verdict": response.content[:100]})
        return state
