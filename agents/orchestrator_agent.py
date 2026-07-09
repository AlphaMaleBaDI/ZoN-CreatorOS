from typing import Optional, Any
import logging
from core.schemas import ContextObject
from agents.planning_agent import PlanningAgent
from agents.campaign_agent import CampaignPlanningAgent
from agents.content_agent import ContentPlanningAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self.planning_agent = PlanningAgent(config=config)
        self.campaign_agent = CampaignPlanningAgent(config=config)
        self.content_agent = ContentPlanningAgent(config=config)

    def plan_execution(self, context: ContextObject, artifact_type: str = "launch_plan") -> Any:
        if artifact_type == "publishing_checklist":
            logger.info("Routing to ContentPlanningAgent for publishing checklist")
            return self.content_agent.generate_calendar(context)
        if artifact_type == "release_complete":
            logger.info("Routing to PlanningAgent for release completion")
            return self.planning_agent.generate_roadmap(context)
        if artifact_type == "content_calendar":
            logger.info("Routing to ContentPlanningAgent")
            return self.content_agent.generate_calendar(context)
        if artifact_type == "campaign_plan":
            logger.info("Routing to CampaignPlanningAgent")
            return self.campaign_agent.generate_campaign(context)
        logger.info("Routing to PlanningAgent")
        return self.planning_agent.generate_roadmap(context)
