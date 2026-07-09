"""
Context Extraction — deterministic inference from freeform text.

Today: keyword matching.
Tomorrow: LLM classification.
Interface stays the same.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ContextExtraction:
    domain: str = ""
    intent: str = ""
    confidence: float = 0.0
    themes: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    timeline: Optional[str] = None
    creator_name: Optional[str] = None
    project_name: Optional[str] = None
    audience: Optional[str] = None


DOMAIN_KEYWORDS = {
    "music": [
        "album", "ep", "lp", "song", "track", "single", "music", "beat",
        "producer", "artist", "release", "record", "studio", "mix", "master",
        "vinyl", "playlist", "spotify", "soundcloud", "bandcamp", "concert",
        "tour", "live show", "session", "collab", "featuring", "remix",
    ],
    "film": [
        "film", "movie", "short film", "documentary", "screenplay", "script",
        "director", "cinema", "scene", "shot", "edit", "post-production",
        "premiere", "festival", "screening",
    ],
    "visual_art": [
        "art", "painting", "sculpture", "exhibition", "gallery", "canvas",
        "illustration", "portrait", "photography", "installations", "mixed media",
    ],
    "fashion": [
        "fashion", "collection", "lookbook", "design", "clothing", "wear",
        "textile", "runway", "brand", "streetwear", "couture",
    ],
    "tech": [
        "app", "platform", "saas", "tool", "software", "startup", "product",
        "mvp", "beta", "launch", "dashboard", "api", "database",
    ],
    "writing": [
        "book", "novel", "poetry", "essay", "blog", "newsletter", "zine",
        "memoir", "anthology", "chapter", "draft",
    ],
    "gaming": [
        "game", "indie game", "unity", "unreal", "gameplay", "npc",
        "world building", "level design", "pixel art",
    ],
}

THEME_KEYWORDS = {
    "afrofuturism": ["afrofutur", "afro futur", "african", "diaspora", "afro"],
    "identity": ["identity", "self", "who am i", "belonging", "roots", "heritage"],
    "technology": ["tech", "digital", "ai", "algorithm", "code", "machine", "cyber"],
    "spirituality": ["spiritual", "ritual", "ancestral", "sacred", "divine", "mystic"],
    "social_impact": ["activism", "justice", "change", "impact", "community", "movement"],
    "love": ["love", "romance", "heart", "relationship", "intimacy"],
    "nature": ["nature", "earth", "ocean", "forest", "climate", "environment"],
    "urban": ["city", "urban", "street", "concrete", "skyline", "nightlife"],
    "memory": ["memory", "nostalgia", "past", "childhood", "remember", "homecoming"],
    "resilience": ["resilience", "overcome", "struggle", "strength", "survive", "thrive"],
    "culture": ["culture", "tradition", "ritual", "ceremony", "folk", "oral"],
    "future": ["future", "tomorrow", "vision", "forward", "next generation"],
}

INTENT_KEYWORDS = {
    "release": ["release", "launch", "drop", "put out", "publish", "debut"],
    "promote": ["promote", "marketing", "campaign", "push", "grow", "audience"],
    "document": ["document", "capture", "record", "chronicle", "story"],
    "explore": ["explore", "experiment", "try", "play with", "investigate"],
    "connect": ["connect", "community", "fans", "audience", "reach"],
    "build": ["build", "create", "make", "develop", "produce"],
}

AUDIENCE_KEYWORDS = {
    "youth": ["young", "youth", "gen z", "gen-z", "next gen", "new generation"],
    "african": ["african", "africa", " continent", "nigerian", "kenyan", "ghanaian", "south african"],
    "diaspora": ["diaspora", "abroad", "overseas", "immigrant", "expat"],
    "creative": ["creative", "artist", "musician", "maker", "creator", "designer"],
    "tech": ["tech", "developer", "engineer", "startup", "founder"],
    "cultural": ["cultural", "conscious", "aware", "progressive"],
    "mainstream": ["mainstream", "general", "pop", "mass market", "everyone"],
    "niche": ["niche", "underground", "indie", "alternative", "cult"],
}

TIMELINE_PATTERNS = [
    (r"next (january|february|march|april|may|june|july|august|september|october|november|december)", "month"),
    (r"(january|february|march|april|may|june|july|august|september|october|november|december) \d{4}", "date"),
    (r"(\d+) (months?|weeks?|days?)", "relative"),
    (r"end of (year|summer|spring|fall|winter)", "season"),
    (r"q[1-4]", "quarter"),
    (r"asap|as soon as possible|right away|immediately", "asap"),
]


class ContextExtractor:
    """Deterministic context extraction from freeform text.

    Returns a ContextExtraction with domain, intent, themes, etc.
    No LLM. Just structured keyword matching with confidence scoring.
    """

    def extract(self, text: str, existing: Optional[ContextExtraction] = None) -> ContextExtraction:
        t = text.lower().strip()
        ext = existing or ContextExtraction()

        if not ext.domain:
            ext.domain = self._extract_domain(t)
        if not ext.intent:
            ext.intent = self._extract_intent(t)
        if not ext.themes:
            ext.themes = self._extract_themes(t)
        if not ext.audience:
            ext.audience = self._extract_audience(t)
        if not ext.timeline:
            ext.timeline = self._extract_timeline(t)
        if not ext.project_name:
            ext.project_name = self._extract_project_name(text)
        if not ext.entities:
            ext.entities = self._extract_entities(t)
        if not ext.goals:
            ext.goals = self._infer_goals(ext)

        ext.confidence = self._compute_confidence(ext)
        return ext

    def _extract_domain(self, text: str) -> str:
        scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[domain] = score
        if not scores:
            return ""
        return max(scores, key=scores.get)

    def _extract_intent(self, text: str) -> str:
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[intent] = score
        if not scores:
            return ""
        return max(scores, key=scores.get)

    def _extract_themes(self, text: str) -> List[str]:
        found = []
        for theme, keywords in THEME_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                found.append(theme)
        return found

    def _extract_audience(self, text: str) -> str:
        scores = {}
        for segment, keywords in AUDIENCE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[segment] = score
        if not scores:
            return ""
        return max(scores, key=scores.get)

    def _extract_timeline(self, text: str) -> Optional[str]:
        for pattern, label in TIMELINE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_project_name(self, text: str) -> Optional[str]:
        patterns = [
            r'(?:called|named|titled)\s+["\']?(.+?)["\']?(?:\s+|$)',
            r'(?:my |the )\b(album|ep|lp|film|project|collection|exhibition|book)\b\s+(?:called|named|titled)\s+["\']?(.+?)["\']?',
            r'\b(album|ep|lp|film|project|collection|exhibition|book)\b\s+(?:called|named|titled)\s+["\']?(.+?)["\']?',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                name = groups[-1].strip().strip("\"'")
                if 2 < len(name) < 60:
                    return name
        return None

    def _extract_entities(self, text: str) -> List[str]:
        entities = []
        capital_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        for match in re.finditer(capital_pattern, text):
            word = match.group(1)
            if word not in ("I", "The", "This", "That", "What", "How", "Tell", "Let"):
                entities.append(word)
        return list(dict.fromkeys(entities))

    def _infer_goals(self, ext: ContextExtraction) -> List[str]:
        goals = []
        if ext.intent == "release":
            goals.append("complete production and release")
        elif ext.intent == "promote":
            goals.append("grow audience and awareness")
        elif ext.intent == "document":
            goals.append("capture and preserve the creative journey")
        elif ext.intent == "connect":
            goals.append("build community around the work")
        elif ext.intent == "build":
            goals.append("develop and ship the project")
        if ext.audience:
            goals.append(f"reach {ext.audience} audience")
        return goals

    def _compute_confidence(self, ext: ContextExtraction) -> float:
        score = 0.0
        if ext.domain:
            score += 0.3
        if ext.intent:
            score += 0.2
        if ext.themes:
            score += min(0.2, len(ext.themes) * 0.07)
        if ext.audience:
            score += 0.15
        if ext.timeline:
            score += 0.1
        if ext.project_name:
            score += 0.05
        return round(min(1.0, score), 2)
