from typing import Optional, Any
import logging
from core.schemas import ContextObject
from agents.planning_agent import PlanningAgent

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.planning_agent = PlanningAgent(config=config)

    def plan_execution(self, context: ContextObject) -> Any:
        request_lower = context.user_request.lower()
        if any(kw in request_lower for kw in ["launch", "release", "plan", "campaign", "drop"]):
            logger.info("Routing to PlanningAgent for launch plan generation")
            return self.planning_agent.generate_roadmap(context)
        logger.info("Default routing to PlanningAgent")
        return self.planning_agent.generate_roadmap(context)
