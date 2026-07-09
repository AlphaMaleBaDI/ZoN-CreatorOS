import json
import os
import sys
import time
from datetime import datetime
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings


_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "fireworks")


def _ensure_log_dir():
    os.makedirs(_LOG_DIR, exist_ok=True)


def _log_raw(prompt: str, response, latency_s: float):
    _ensure_log_dir()
    path = os.path.join(_LOG_DIR, "latest.json")
    usage = response.usage
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": {"prompt": prompt},
        "response": {
            "text": response.choices[0].message.content if response.choices else "",
            "raw": response.model_dump(),
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
            },
        },
        "latency_s": round(latency_s, 2),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)


def create_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        base_url=settings.fireworks_base_url,
        api_key=settings.fireworks_api_key,
    )


def chat(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    log_raw: bool = True,
) -> dict:
    settings = get_settings()
    client = create_client()
    model = model or settings.fireworks_model

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    start = time.time()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    elapsed = time.time() - start

    text = response.choices[0].message.content or ""
    usage = response.usage

    result = {
        "text": text,
        "model": model,
        "latency_s": round(elapsed, 2),
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "completion_tokens": usage.completion_tokens if usage else None,
        "total_tokens": usage.total_tokens if usage else None,
    }

    if log_raw:
        _log_raw(prompt, response, elapsed)

    return result


def print_stats(result: dict, label: str = "Response"):
    print(f"\n{label}")
    print(f"{'Model:':<20} {result['model']}")
    print(f"{'Latency:':<20} {result['latency_s']}s")
    if result["prompt_tokens"] is not None:
        print(f"{'Tokens:':<20} {result['prompt_tokens']} prompt -> {result['completion_tokens']} completion ({result['total_tokens']} total)")
    print(f"{'Response:':<20} {result['text']}")
