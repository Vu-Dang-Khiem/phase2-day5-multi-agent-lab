"""Search client abstraction for ResearcherAgent."""

import logging

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client. Supports Tavily and a local mock fallback."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        with trace_span("search", {"query": query, "max_results": max_results}):
            settings = get_settings()
            if settings.tavily_api_key:
                return self._search_tavily(query, max_results)
            return self._mock_search(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        from tavily import TavilyClient

        client = TavilyClient(api_key=get_settings().tavily_api_key)
        response = client.search(query=query, max_results=max_results)
        docs: list[SourceDocument] = []
        for result in response.get("results", []):
            docs.append(
                SourceDocument(
                    title=result.get("title", ""),
                    url=result.get("url"),
                    snippet=result.get("content", ""),
                )
            )
        logger.info("Tavily search returned %d results for query=%s", len(docs), query)
        return docs

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        logger.warning("No TAVILY_API_KEY set; returning mock results for query=%s", query)
        return [
            SourceDocument(
                title=f"Mock Result {i + 1} about {query[:30]}",
                url=f"https://example.com/result-{i + 1}",
                snippet=f"This is a mock snippet for result {i + 1} related to: {query}",
            )
            for i in range(max_results)
        ]
