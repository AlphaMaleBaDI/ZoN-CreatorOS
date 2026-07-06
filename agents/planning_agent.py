import os
import json
import logging
from typing import Optional, Any
from openai import OpenAI
from ollama import Client as OllamaClient
from dotenv import load_dotenv
from core.schemas import ContextObject
from artifacts.launch_plan import LaunchPlan, ActionItem

load_dotenv()
logger = logging.getLogger(__name__)

LLM_SYSTEM_PROMPT = """You are an AI music release strategist. Given a creator's profile and context, generate a structured launch plan.

Respond ONLY with a valid JSON object matching this schema:
{
  "release_strategy": "string describing the release approach",
  "marketing_angles": ["array of marketing angle strings"],
  "audience_profile": "string describing the target audience",
  "next_actions": [{"action": "string describing what to do", "why": "string explaining why"}],
  "confidence_score": 0.0 to 1.0
}"""


def _parse_llm_response(content: str, context: ContextObject) -> Optional[LaunchPlan]:
    try:
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            content = content.rsplit("```", 1)[0].strip()
        data = json.loads(content)
        return LaunchPlan(
            release_strategy=data.get("release_strategy", ""),
            marketing_angles=data.get("marketing_angles", []),
            audience_profile=data.get("audience_profile", ""),
            next_actions=[ActionItem(**a) for a in data.get("next_actions", [])],
            memory_citations=[],
            creative_state_vibra=context.vibra_state,
            confidence_score=data.get("confidence_score")
        )
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}")
        return None


def _build_user_prompt(context: ContextObject) -> str:
    profile = context.creator_profile
    return (
        f"Creator: {profile.get('creator_name', 'Unknown')}\n"
        f"Brand Voice: {profile.get('brand_voice', 'N/A')}\n"
        f"Writing Style: {profile.get('writing_style', 'N/A')}\n"
        f"Personality: {profile.get('personality', 'N/A')}\n"
        f"Goals: {', '.join(context.goals) if context.goals else 'Not specified'}\n"
        f"Request: {context.user_request}\n"
        f"Vibra: {json.dumps(context.vibra_state)}"
    )


class PlanningAgent:
    def __init__(self, config: Optional[Any] = None):
        self.config = config
        self._last_provider: Optional[str] = None

    def _try_ollama(self, context: ContextObject) -> Optional[LaunchPlan]:
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            return None
        logger.info("Trying Ollama Cloud (minimax-m3)")
        try:
            client = OllamaClient(
                host=os.getenv("OLLAMA_CLOUD_HOST", "https://ollama.com"),
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response = client.chat(
                model="minimax-m3",
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(context)}
                ],
                stream=False
            )
            content = response["message"]["content"]
            plan = _parse_llm_response(content, context)
            if plan:
                self._last_provider = "ollama_cloud"
            return plan
        except Exception as e:
            logger.warning(f"Ollama Cloud call failed: {e}")
            return None

    def _try_nvidia(self, context: ContextObject) -> Optional[LaunchPlan]:
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return None
        logger.info("Trying NVIDIA AI Foundations")
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            )
            response = client.chat.completions.create(
                model=os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct"),
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(context)}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            plan = _parse_llm_response(response.choices[0].message.content, context)
            if plan:
                self._last_provider = "nvidia"
            return plan
        except Exception as e:
            logger.warning(f"NVIDIA call failed: {e}")
            return None

    def generate_roadmap(self, context: ContextObject) -> LaunchPlan:
        result = self._try_ollama(context)
        if result:
            return result
        result = self._try_nvidia(context)
        if result:
            return result
        self._last_provider = "fallback"
        logger.error("All LLM providers failed, returning fallback plan")
        return LaunchPlan(
            release_strategy="Fallback: All LLM providers unavailable",
            marketing_angles=["Rebuild brand narrative", "Focus on core fanbase engagement"],
            audience_profile=f"Existing fans of {context.creator_profile.get('creator_name', 'the artist')}",
            next_actions=[
                ActionItem(action="Verify Ollama Cloud API key and NVIDIA API key", why="Both providers failed"),
                ActionItem(action="Complete launch plan manually", why="AI generation unavailable")
            ],
            confidence_score=0.0
        )
