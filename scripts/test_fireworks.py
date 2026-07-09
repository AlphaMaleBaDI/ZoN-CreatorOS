"""Standalone Fireworks connectivity test.

Proves CreatorOS can successfully talk to a Fireworks inference endpoint.
No ProductionEngine, no Observer, no Reasoning — just the API.

Usage:
    python scripts/test_fireworks.py
"""

from fireworks_client import chat, print_stats


def main():
    print("=" * 56)
    print("  Fireworks Connectivity Test")
    print("  Verifying CreatorOS -> Fireworks inference pipeline")
    print("=" * 56)

    # Test 1: Basic connectivity
    result = chat("Say hello from AMD Fireworks in one sentence.")
    print_stats(result, "--- Test 1: Basic connectivity ---")

    # Test 2: Creative writing
    result = chat(
        "Write a haiku about an AI discovering hope.",
        system_prompt="You are a poet who writes with warmth and clarity.",
    )
    print_stats(result, "--- Test 2: Creative writing ---")

    # Test 3: Summarization
    result = chat(
        "Artificial intelligence has made remarkable strides in recent years, "
        "particularly in the domain of creative work. Systems can now compose music, "
        "generate visual art, and even assist in filmmaking. Yet the most profound "
        "advances come not from replacing human creativity, but from augmenting it — "
        "giving creators tools that understand their intent and help them express it "
        "more fully.\n\nSummarize this paragraph in one sentence.",
    )
    print_stats(result, "--- Test 3: Summarization ---")

    print("\n" + "=" * 56)
    print("  All tests complete.")
    print("=" * 56)


if __name__ == "__main__":
    main()
