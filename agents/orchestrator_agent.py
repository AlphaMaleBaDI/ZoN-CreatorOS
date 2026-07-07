from typing import Optional, Any
import logging
from core.schemas import ContextObject
from agents.planning_agent import PlanningAgent
from agents.campaign_agent import CampaignPlanningAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.planning_agent = PlanningAgent(config=config)
        self.campaign_agent = CampaignPlanningAgent(config=config)

    def plan_execution(self, context: ContextObject, intent: str = "") -> Any:
        request_lower = context.user_request.lower()
        if intent == "campaign" or any(kw in request_lower for kw in ["campaign", "marketing", "promotion"]):
            logger.info("Routing to CampaignPlanningAgent")
            return self.campaign_agent.generate_campaign(context)
        if any(kw in request_lower for kw in ["launch", "release", "plan", "drop"]):
            logger.info("Routing to PlanningAgent for launch plan generation")
            return self.planning_agent.generate_roadmap(context)
        logger.info("Default routing to PlanningAgent")
        return self.planning_agent.generate_roadmap(context)
