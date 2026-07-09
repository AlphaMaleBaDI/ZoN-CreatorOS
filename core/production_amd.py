import logging
import time

from core.config import get_settings
from core.production import ProductionEngine, Artifact
from core.prompts import build_film_prompt
from scripts.fireworks_client import chat

logger = logging.getLogger(__name__)


class AMDEngine(ProductionEngine):
    """AMD/Fireworks-backed production engine.

    Falls back to TemplateEngine on any failure so the demo never breaks.
    """

    def generate(self, candidate, understanding, artifact_type: str = "") -> Artifact:
        settings = get_settings()

        if not settings.fireworks_api_key:
            logger.warning("FIREWORKS_API_KEY not set, falling back to template")
            return self._fallback(candidate, understanding, artifact_type)

        if artifact_type == "film_concept" or not artifact_type:
            prompt = build_film_prompt(understanding)
        else:
            logger.warning("Unsupported artifact_type '%s', falling back to template", artifact_type)
            return self._fallback(candidate, understanding, artifact_type)

        try:
            start = time.time()
            result = chat(
                prompt=prompt,
                system_prompt="You are a film concept writer. Write with emotional depth and specificity.",
                model=settings.fireworks_model,
                log_raw=True,
            )
            elapsed = time.time() - start

            return Artifact(
                type="film_concept",
                title="Film Concept",
                body=result["text"],
                metadata={
                    "engine": "amd",
                    "provider": "fireworks",
                    "model": result["model"],
                    "latency_s": result["latency_s"],
                    "prompt_tokens": result["prompt_tokens"],
                    "completion_tokens": result["completion_tokens"],
                },
            )
        except Exception:
            logger.exception("AMDEngine.generate() failed, falling back to template")
            return self._fallback(candidate, understanding, artifact_type)

    def _fallback(self, candidate, understanding, artifact_type: str) -> Artifact:
        from main import TemplateEngine
        return TemplateEngine().generate(candidate, understanding, artifact_type)
