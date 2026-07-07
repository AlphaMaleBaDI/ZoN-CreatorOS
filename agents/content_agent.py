import os
import json
import logging
from typing import Optional, Any
from openai import OpenAI
from ollama import Client as OllamaClient
from dotenv import load_dotenv
from core.schemas import ContextObject
from artifacts.content_calendar import ContentCalendar, CalendarWeek, CalendarAction

load_dotenv()
logger = logging.getLogger(__name__)

CONTENT_SYSTEM_PROMPT = """You are an AI content strategist for music artists. Given the creator's profile, campaign strategy, and existing launch plan, generate a structured content calendar.

Respond ONLY with a valid JSON object matching this schema:
{
  "campaign_name": "string — name of the campaign this calendar supports",
  "content_strategy": "string — overall content narrative and approach",
  "weeks": [
    {
      "week": integer,
      "theme": "string — weekly content theme",
      "actions": ["array of specific content actions for this week"]
    }
  ],
  "platform_schedule": ["array of platform-specific posting plans"],
  "post_cadence": "string — description of posting frequency and rhythm",
  "key_announcements": ["array of major announcement descriptions with timing"],
  "milestones": ["array of milestone descriptions"],
  "dependencies": ["array of things that must happen before or during this calendar"],
  "success_metrics": ["array of measurable success metrics"],
  "next_actions": [{"action": "string", "why": "string"}],
  "confidence_score": 0.0 to 1.0
}

IMPORTANT: Make the calendar span 8-16 weeks and include at least 6 weeks with specific themes and actions."""


def _parse_content_response(content: str) -> Optional[ContentCalendar]:
    try:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0].strip()
        data = json.loads(content)
        weeks_data = data.get("weeks", [])
        weeks = [CalendarWeek(**w) for w in weeks_data] if weeks_data else []
        return ContentCalendar(
            campaign_name=data.get("campaign_name", "Untitled Calendar"),
            content_strategy=data.get("content_strategy", ""),
            weeks=weeks,
            platform_schedule=data.get("platform_schedule", []),
            post_cadence=data.get("post_cadence", ""),
            key_announcements=data.get("key_announcements", []),
            milestones=data.get("milestones", []),
            dependencies=data.get("dependencies", []),
            success_metrics=data.get("success_metrics", []),
            next_actions=[CalendarAction(**a) for a in data.get("next_actions", [])],
            confidence_score=data.get("confidence_score"),
        )
    except Exception as e:
        logger.warning(f"Failed to parse content calendar response: {e}")
        return None


def _build_content_prompt(context: ContextObject) -> str:
    profile = context.creator_profile
    recent = context.recent_artifacts

    launch_summary = ""
    campaign_summary = ""
    for art in recent:
        data = art.get("data", {})
        atype = art.get("artifact_type", "")
        if atype == "launch_plan":
            launch_summary = (
                f"Launch Strategy: {data.get('release_strategy', 'N/A')[:200]}\n"
            )
        elif atype == "campaign_plan":
            campaign_summary = (
                f"Campaign Name: {data.get('campaign_name', 'N/A')}\n"
                f"Campaign Objectives: {json.dumps(data.get('campaign_objectives', []))}\n"
                f"Channel Strategy: {json.dumps(data.get('channel_strategy', []))}\n"
                f"Content Themes: {json.dumps(data.get('content_themes', []))}\n"
            )

    return (
        f"Creator: {profile.get('creator_name', 'Unknown')}\n"
        f"Brand Voice: {profile.get('brand_voice', 'N/A')}\n"
        f"Goals: {', '.join(context.goals) if context.goals else 'Not specified'}\n"
        f"Request: {context.user_request}\n"
        f"Vibra: {json.dumps(context.vibra_state)}\n"
        f"{launch_summary}"
        f"{campaign_summary}"
    )


class ContentPlanningAgent:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self._last_provider: Optional[str] = None

    def _try_ollama(self, context: ContextObject) -> Optional[ContentCalendar]:
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            return None
        logger.info("ContentAgent: trying Ollama Cloud")
        try:
            client = OllamaClient(
                host=os.getenv("OLLAMA_CLOUD_HOST", "https://ollama.com"),
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response = client.chat(
                model="minimax-m3",
                messages=[
                    {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_content_prompt(context)}
                ],
                stream=False
            )
            content = response["message"]["content"]
            plan = _parse_content_response(content)
            if plan:
                self._last_provider = "ollama_cloud"
            return plan
        except Exception as e:
            logger.warning(f"ContentAgent: Ollama Cloud failed: {e}")
            return None

    def _try_nvidia(self, context: ContextObject) -> Optional[ContentCalendar]:
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return None
        logger.info("ContentAgent: trying NVIDIA AI Foundations")
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            )
            response = client.chat.completions.create(
                model=os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct"),
                messages=[
                    {"role": "system", "content": CONTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_content_prompt(context)}
                ],
                temperature=0.7,
                max_tokens=1200
            )
            plan = _parse_content_response(response.choices[0].message.content)
            if plan:
                self._last_provider = "nvidia"
            return plan
        except Exception as e:
            logger.warning(f"ContentAgent: NVIDIA failed: {e}")
            return None

    def generate_calendar(self, context: ContextObject) -> ContentCalendar:
        result = self._try_ollama(context)
        if result:
            return result
        result = self._try_nvidia(context)
        if result:
            return result
        self._last_provider = "fallback"
        logger.error("ContentAgent: all providers failed, returning fallback")
        return ContentCalendar(
            campaign_name="Fallback Calendar",
            content_strategy="Complete content planning manually",
            weeks=[CalendarWeek(week=1, theme="Planning", actions=["Define content calendar"])],
            platform_schedule=["TBD"],
            post_cadence="To be determined",
            key_announcements=["TBD"],
            milestones=["TBD"],
            dependencies=["Campaign plan must be finalized first"],
            success_metrics=["TBD"],
            next_actions=[CalendarAction(action="Check API keys", why="Both providers failed")],
            confidence_score=0.0,
        )
