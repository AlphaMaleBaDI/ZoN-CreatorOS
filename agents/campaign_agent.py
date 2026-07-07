import os
import json
import logging
from typing import Optional, Any
from openai import OpenAI
from ollama import Client as OllamaClient
from dotenv import load_dotenv
from core.schemas import ContextObject
from artifacts.campaign_plan import CampaignPlan, CampaignAction

load_dotenv()
logger = logging.getLogger(__name__)

CAMPAIGN_SYSTEM_PROMPT = """You are an AI campaign strategist for music artists. Given a creator's profile, context, and existing launch plan, generate a structured marketing campaign plan.

Respond ONLY with a valid JSON object matching this schema:
{
  "campaign_name": "string — short campaign name",
  "campaign_objectives": ["array of objective strings"],
  "target_segments": ["array of target audience segment descriptions"],
  "channel_strategy": ["array of channel strategy descriptions"],
  "content_themes": ["array of content theme descriptions"],
  "timeline_weeks": integer,
  "budget_notes": "string — budget considerations",
  "kpis": ["array of measurable KPI strings"],
  "next_actions": [{"action": "string", "why": "string"}],
  "confidence_score": 0.0 to 1.0
}"""


def _parse_campaign_response(content: str) -> Optional[CampaignPlan]:
    try:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0].strip()
        data = json.loads(content)
        return CampaignPlan(
            campaign_name=data.get("campaign_name", "Untitled Campaign"),
            campaign_objectives=data.get("campaign_objectives", []),
            target_segments=data.get("target_segments", []),
            channel_strategy=data.get("channel_strategy", []),
            content_themes=data.get("content_themes", []),
            timeline_weeks=data.get("timeline_weeks", 12),
            budget_notes=data.get("budget_notes", ""),
            kpis=data.get("kpis", []),
            next_actions=[CampaignAction(**a) for a in data.get("next_actions", [])],
            confidence_score=data.get("confidence_score"),
        )
    except Exception as e:
        logger.warning(f"Failed to parse campaign response: {e}")
        return None


def _build_campaign_prompt(context: ContextObject) -> str:
    profile = context.creator_profile
    recent = context.recent_artifacts
    launch_summary = ""
    if recent:
        latest = recent[-1]
        data = latest.get("data", {})
        launch_summary = (
            f"Existing Launch Plan Strategy: {data.get('release_strategy', 'N/A')}\n"
            f"Marketing Angles from Launch Plan: {json.dumps(data.get('marketing_angles', []))}\n"
        )
    return (
        f"Creator: {profile.get('creator_name', 'Unknown')}\n"
        f"Brand Voice: {profile.get('brand_voice', 'N/A')}\n"
        f"Goals: {', '.join(context.goals) if context.goals else 'Not specified'}\n"
        f"Request: {context.user_request}\n"
        f"Vibra: {json.dumps(context.vibra_state)}\n"
        f"{launch_summary}"
    )


class CampaignPlanningAgent:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self._last_provider: Optional[str] = None

    def _try_ollama(self, context: ContextObject) -> Optional[CampaignPlan]:
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            return None
        logger.info("CampaignAgent: trying Ollama Cloud")
        try:
            client = OllamaClient(
                host=os.getenv("OLLAMA_CLOUD_HOST", "https://ollama.com"),
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response = client.chat(
                model="minimax-m3",
                messages=[
                    {"role": "system", "content": CAMPAIGN_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_campaign_prompt(context)}
                ],
                stream=False
            )
            content = response["message"]["content"]
            plan = _parse_campaign_response(content)
            if plan:
                self._last_provider = "ollama_cloud"
            return plan
        except Exception as e:
            logger.warning(f"CampaignAgent: Ollama Cloud failed: {e}")
            return None

    def _try_nvidia(self, context: ContextObject) -> Optional[CampaignPlan]:
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return None
        logger.info("CampaignAgent: trying NVIDIA AI Foundations")
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            )
            response = client.chat.completions.create(
                model=os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct"),
                messages=[
                    {"role": "system", "content": CAMPAIGN_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_campaign_prompt(context)}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            plan = _parse_campaign_response(response.choices[0].message.content)
            if plan:
                self._last_provider = "nvidia"
            return plan
        except Exception as e:
            logger.warning(f"CampaignAgent: NVIDIA failed: {e}")
            return None

    def generate_campaign(self, context: ContextObject) -> CampaignPlan:
        result = self._try_ollama(context)
        if result:
            return result
        result = self._try_nvidia(context)
        if result:
            return result
        self._last_provider = "fallback"
        logger.error("CampaignAgent: all providers failed, returning fallback")
        return CampaignPlan(
            campaign_name="Fallback Campaign",
            campaign_objectives=["Complete campaign planning manually"],
            target_segments=[f"Existing audience of {context.creator_profile.get('creator_name', 'the artist')}"],
            channel_strategy=["Social media", "Email", "Community"],
            content_themes=["Core messaging"],
            timeline_weeks=8,
            budget_notes="Budget to be determined",
            kpis=["TBD"],
            next_actions=[CampaignAction(action="Check API keys", why="Both providers failed")],
            confidence_score=0.0,
        )
