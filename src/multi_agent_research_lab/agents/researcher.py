"""Researcher agent that collects sources and creates research notes."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)

RESEARCHER_SYSTEM_PROMPT = (
    "You are a thorough research assistant. Given a query and search results, "
    "produce concise research notes that capture key facts, statistics, and citations. "
    "Always cite sources by title."
)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self._search = SearchClient()
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        logger.info("Researcher searching for: %s", state.request.query)
        sources = self._search.search(state.request.query, max_results=state.request.max_sources)
        state.sources.extend(sources)

        sources_text = "\n\n".join(
            f"Title: {s.title}\nURL: {s.url}\nContent: {s.snippet}" for s in sources
        )
        user_prompt = (
            f"Query: {state.request.query}\n\n"
            f"Search Results:\n{sources_text}\n\n"
            f"Target audience: {state.request.audience}\n\n"
            "Produce concise research notes with citations."
        )
        response = self._llm.complete(RESEARCHER_SYSTEM_PROMPT, user_prompt)
        state.research_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=response.content,
                metadata={
                    "sources_count": len(sources),
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("researcher.run", {"sources_count": len(sources)})
        return state
