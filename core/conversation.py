import re
from enum import Enum
from typing import Tuple, Optional


class ConversationIntent(str, Enum):
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    PROJECT = "project"
    CORRECTION = "correction"
    APPROVAL = "approval"
    REJECTION = "rejection"
    EMOTION = "emotion"
    UNKNOWN = "unknown"


class ConversationMode(str, Enum):
    SOCIAL = "social"
    PROJECT = "project"
    DECISION = "decision"


_GREETING_PATTERNS = [
    r"^(hi|hello|hey|howdy|yo|sup|good\s*(morning|afternoon|evening)|what'?s\s*up)",
    r"nice\s+(to\s+)?meet",
    r"^(oh\s+)?hey\s",
]
_SMALL_TALK_PATTERNS = [
    r"how\s+(are|'re)\s+(you|things)",
    r"how'?s\s+(your\s+)?day",
    r"^lol\b", r"^haha\b", r"^😂", r"^😊",
    r"thanks?\b", r"thank\s+you",
    r"no\s+problem",
    r"you\s+(too|as well)",
    r"have\s+a\s+good",
    r"see\s+you",
    r"bye\b",
    r"great\b", r"awesome\b", r"cool\b",
]
_EMOTION_PATTERNS = [
    r"^😂", r"^😊", r"^😢", r"^😤", r"^🙏", r"^🔥", r"^💀",
    r"^lol$", r"^lmao$",
    r"that'?s\s+(funny|crazy|wild)",
]
_CORRECTION_PATTERNS = [
    r"^actually[,:]", r"^wait[,:]", r"^hold\s+on[,:]",
    r"^no,\s+", r"^not\s+quite",
    r"^that'?s\s+not", r"^that\s+isn'?t",
    r"^let\s+me\s+clarify",
    r"^to\s+clarify",
    r"^i\s+meant",
    r"^reconsider",
]
_APPROVAL_PATTERNS = [
    r"^yes$", r"^yep$", r"^yeah$", r"^sure$",
    r"^proceed$", r"^go\s+ahead",
    r"^do\s+it", r"^that'?s?\s+(right|correct|perfect)",
    r"looks?\s+good",
    r"^ok$", r"^okay$", r"^alright",
]
_REJECTION_PATTERNS = [
    r"^no$", r"^nope$", r"^nah$",
    r"^not\s+(that|really|yet)",
    r"^i\s+don'?t\s+think",
    r"^that'?s?\s+not\s+right",
]


def classify_intent(message: str) -> Tuple[ConversationIntent, Optional[str]]:
    msg = message.strip()
    if not msg:
        return ConversationIntent.UNKNOWN, None

    if any(re.search(p, msg, re.IGNORECASE) for p in _GREETING_PATTERNS):
        return ConversationIntent.GREETING, None

    if any(re.search(p, msg, re.IGNORECASE) for p in _EMOTION_PATTERNS):
        return ConversationIntent.EMOTION, None

    if any(re.search(p, msg, re.IGNORECASE) for p in _SMALL_TALK_PATTERNS):
        return ConversationIntent.SMALL_TALK, None

    if any(re.search(p, msg, re.IGNORECASE) for p in _CORRECTION_PATTERNS):
        return ConversationIntent.CORRECTION, None

    if any(re.search(p, msg, re.IGNORECASE) for p in _APPROVAL_PATTERNS):
        return ConversationIntent.APPROVAL, None

    if any(re.search(p, msg, re.IGNORECASE) for p in _REJECTION_PATTERNS):
        return ConversationIntent.REJECTION, None

    return ConversationIntent.PROJECT, None


def is_project_relevant(intent: ConversationIntent) -> bool:
    return intent in (
        ConversationIntent.PROJECT,
        ConversationIntent.CORRECTION,
    )


_GREETING_RESPONSES = [
    "Hey there. Good to see you.",
    "Hi. I'm listening when you're ready to talk about your project.",
    "Hello. I'm here whenever you want to dive in.",
]

_SMALL_TALK_RESPONSES = [
    "I'm here and ready when you are.",
    "Whenever you're ready to work, I'm listening.",
    "No rush. I'm here.",
]

_EMOTION_RESPONSES = [
    "I hear you.",
    "Got it.",
    "Understood.",
]


def social_response(intent: ConversationIntent) -> str:
    import random
    if intent == ConversationIntent.GREETING:
        return random.choice(_GREETING_RESPONSES)
    elif intent == ConversationIntent.SMALL_TALK:
        return random.choice(_SMALL_TALK_RESPONSES)
    elif intent == ConversationIntent.EMOTION:
        return random.choice(_EMOTION_RESPONSES)
    return ""
