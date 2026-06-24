"""Supervisor / router that decides which worker runs next."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)

ROUTE_RESEARCHER = "researcher"
ROUTE_ANALYST = "analyst"
ROUTE_WRITER = "writer"
ROUTE_DONE = "done"


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        settings = get_settings()

        if state.iteration >= settings.max_iterations:
            logger.warning("Max iterations (%d) reached; forcing done", settings.max_iterations)
            state.record_route(ROUTE_DONE)
            return state

        if state.final_answer is not None:
            next_route = ROUTE_DONE
        elif state.analysis_notes is None and state.research_notes is not None:
            next_route = ROUTE_ANALYST
        elif state.research_notes is None:
            next_route = ROUTE_RESEARCHER
        else:
            next_route = ROUTE_WRITER

        state.record_route(next_route)
        logger.info("Supervisor routed to %s (iteration %d)", next_route, state.iteration)
        return state
