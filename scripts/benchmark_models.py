"""Benchmark Fireworks models for latency and output quality."""
import os
import sys
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
from scripts.fireworks_client import chat

PROMPT = """Create a film concept based on the following creative understanding.

EMOTIONAL CORE
hope

THEME
belonging

MAIN CHARACTER
An AI learning what it means to feel

WORLD
A near future where technology and humanity are no longer separate."""

SYSTEM_PROMPT = "You are a film concept writer. Write with emotional depth and specificity."

MODELS = [
    "accounts/fireworks/models/kimi-k2p7-code",
    "accounts/fireworks/models/deepseek-v4-flash",
]

results = []
for model in MODELS:
    print(f"\n--- {model} ---")
    start = time.time()
    try:
        result = chat(prompt=PROMPT, system_prompt=SYSTEM_PROMPT, model=model, log_raw=False)
        elapsed = time.time() - start
        tok_in = result["prompt_tokens"] or 0
        tok_out = result["completion_tokens"] or 0
        length = len(result["text"])
        preview = result["text"][:150].replace("\n", " ")
        results.append((model, elapsed, tok_in, tok_out, length))
        print(f"  Latency: {elapsed:.1f}s")
        print(f"  Tokens: {tok_in} in -> {tok_out} out ({tok_in + tok_out} total)")
        print(f"  Length: {length} chars")
        print(f"  Preview: {preview}...")
    except Exception as e:
        print(f"  FAILED: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"{'Model':<50} {'Latency':>8} {'Tokens':>8} {'Chars':>6}")
print("-" * 72)
for model, lat, tin, tout, chars in results:
    short = model.split("/")[-1]
    print(f"{short:<50} {lat:>7.1f}s {tin + tout:>7} {chars:>6}")
