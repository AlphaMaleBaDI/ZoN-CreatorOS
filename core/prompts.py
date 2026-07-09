"""Prompt builders for the Production Engine.

Each builder maps a CurrentUnderstanding into a structured prompt
that preserves the CreatorOS artifact schema. Keeps prompt logic
out of the engine implementations.
"""


def _extract_emotion(understanding) -> str:
    beliefs = [b.statement for b in understanding.beliefs if b.lifecycle.value == "active"]
    obs = [o.content for o in understanding.observations if o.confidence >= 0.3]
    emotion = "hope"
    for s in obs + beliefs:
        sl = s.lower()
        for w in ["hope", "fear", "joy", "love", "loss", "loneliness", "belonging", "courage", "redemption"]:
            if w in sl:
                return w
    return emotion


def _extract_theme(understanding) -> str:
    beliefs = [b.statement for b in understanding.beliefs if b.lifecycle.value == "active"]
    obs = [o.content for o in understanding.observations if o.confidence >= 0.3]
    for s in obs + beliefs:
        if "future" in s.lower() or "change" in s.lower():
            return "hope — because the future can still change"
    return "discovering what it means to feel"


def _extract_character(understanding) -> str:
    beliefs = [b.statement for b in understanding.beliefs if b.lifecycle.value == "active"]
    obs = [o.content for o in understanding.observations if o.confidence >= 0.3]
    for s in obs + beliefs:
        if "ai" in s.lower() or "learn" in s.lower():
            return "An AI learning what it means to feel"
    return "A being discovering emotion for the first time"


def build_film_prompt(understanding) -> str:
    """Build a prompt for generating a Film Concept artifact."""
    emotion = _extract_emotion(understanding)
    theme = _extract_theme(understanding)
    character = _extract_character(understanding)

    return f"""Create a film concept based on the following creative understanding.

EMOTIONAL CORE
{emotion}

THEME
{theme}

MAIN CHARACTER
{character}

WORLD
A near future where technology and humanity are no longer separate.

Use the CreatorOS artifact schema below — produce each section as plain text (no JSON):

LOGLINE
A one-sentence summary that captures the emotional core and central conflict.

THEME
How the emotional core and theme manifest in the story.

MAIN CHARACTER
Who the story follows and what they want.

WORLD
The setting and atmosphere.

THREE-ACT ARC
Act 1 — The Awakening
Act 2 — The Choice  
Act 3 — The Becoming

VISUAL STYLE
The look and feel — colors, tone, cinematic influences.

AI GENERATION PROMPT
A brief text-to-video or image generation prompt that captures the film's visual essence.

Write with emotional depth and specificity. Avoid generic descriptions."""
