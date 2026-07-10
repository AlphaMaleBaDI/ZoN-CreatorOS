import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    production_engine: str = "template"
    fireworks_api_key: str = ""
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    fireworks_model: str = "accounts/fireworks/models/deepseek-v4-pro"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is not None:
        return _settings
    _settings = Settings(
        production_engine=os.environ.get("PRODUCTION_ENGINE", "template"),
        fireworks_api_key=os.environ.get("FIREWORKS_API_KEY", ""),
        fireworks_base_url=os.environ.get(
            "FIREWORKS_BASE_URL",
            "https://api.fireworks.ai/inference/v1",
        ),
        fireworks_model=os.environ.get(
            "FIREWORKS_MODEL",
            "accounts/fireworks/models/deepseek-v4-pro",
        ),
    )
    return _settings
