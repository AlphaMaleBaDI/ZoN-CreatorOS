from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import re


class CreativeActivity(str, Enum):
    EXPLORE = "explore"
    BRAINSTORM = "brainstorm"
    RESEARCH = "research"
    PLAN = "plan"
    GENERATE = "generate"
    REVIEW = "review"
    CRITIQUE = "critique"
    REFINE = "refine"
    UNKNOWN = "unknown"


_ACTIVITY_LABELS: dict[CreativeActivity, str] = {
    CreativeActivity.BRAINSTORM: "That's exciting",
    CreativeActivity.EXPLORE: "I'd love to hear more",
    CreativeActivity.RESEARCH: "That's an interesting question",
    CreativeActivity.PLAN: "Let's think about the path forward",
    CreativeActivity.GENERATE: "I can help bring this to life",
    CreativeActivity.REVIEW: "I'd be happy to take a look",
    CreativeActivity.CRITIQUE: "I'll give you my honest thoughts",
    CreativeActivity.REFINE: "Let's make this sharper",
}

_ACTIVITY_RULES: List[Tuple[str, CreativeActivity, int]] = [
    (r"(?:i\s+(?:am|'m)\s+(?:thinking|considering|exploring|planning)\s+(?:about|of)?)", CreativeActivity.BRAINSTORM, 12),
    (r"(?:i\s+want\s+to)", CreativeActivity.BRAINSTORM, 10),
    (r"(?:brainstorm|come up with|concept|idea for|think|thought|imagine|what if)", CreativeActivity.BRAINSTORM, 10),
    (r"(?:not sure what|not sure how|help me with|ideas for|inspiration|guidance|assist\s+(?:me|with)|stuck|unsure|confus(?:ed|ing))", CreativeActivity.BRAINSTORM, 10),
    (r"(?:explore|exploring|explored|wander|wandering|curious about|curious|what\s+is|tell me about)", CreativeActivity.EXPLORE, 10),
    (r"(?:research|researching|researched|investigat|looking into|find out|learn about|study|studying|studied)", CreativeActivity.RESEARCH, 10),
    (r"(?:plan\s+(?:to|for|the|a|an|our|your|my)|planning|planned|strategy|strategic|roadmap|blueprint|outline|outlining|structure|structuring)", CreativeActivity.PLAN, 10),
    (r"(?:generate|generating|generated|create|creating|created|make|making|made|produce|producing|produced)", CreativeActivity.GENERATE, 15),
    (r"(?:write|writing|writes|wrote|build|building|built|record|recording|recorded|design|designing|designed|develop|developing|developed)", CreativeActivity.GENERATE, 8),
    (r"(?:review|reviewing|reviewed|evaluate|evaluating|evaluated|assess|assessing|assessed|check|checking|checked|reflect|reflecting|reflected)", CreativeActivity.REVIEW, 10),
    (r"(?:critique|critiquing|critiqued|feedback|thoughts on|opinion|opinions|what do you think)", CreativeActivity.CRITIQUE, 10),
    (r"(?:refine|refining|refined|improve|improving|improved|polish|polishing|polished|iterate|iterating|iterated|revise|revising|revised|edit|editing|edited)", CreativeActivity.REFINE, 10),
]


def detect_activity(message: str) -> CreativeActivity:
    msg_lower = message.lower().strip()
    scores: dict[CreativeActivity, int] = {}

    for pattern, activity, weight in _ACTIVITY_RULES:
        if re.search(pattern, msg_lower):
            scores[activity] = scores.get(activity, 0) + weight

    if not scores:
        return CreativeActivity.UNKNOWN
    return max(scores, key=scores.get)


class CreativeDomain(str, Enum):
    STORYTELLING = "storytelling"
    MUSIC = "music"
    FILM = "film"
    GAME = "game"
    SOFTWARE = "software"
    BUSINESS = "business"
    EDUCATION = "education"
    RESEARCH = "research"
    VISUAL_ART = "visual_art"
    UNKNOWN = "unknown"


MEDIUM_DOMAINS = {
    CreativeDomain.STORYTELLING,
    CreativeDomain.MUSIC,
    CreativeDomain.FILM,
    CreativeDomain.GAME,
    CreativeDomain.VISUAL_ART,
}


@dataclass
class DiscoveryPriority:
    area: str
    question: str
    follow_up: str = ""
    keywords: List[str] = field(default_factory=list)
    evaluator: Optional[callable] = None


# -------- Requirement Evaluators ------------------------------------------------
# Each evaluator takes (beliefs_list, latest_message) and returns True if
# the creator's latest message (or accumulated beliefs) satisfies that requirement.


def _eval_core_idea(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["about", "follow", "based on", "premise", "story of", "tale of"]
    return any(t in msg for t in triggers)


def _eval_genre(beliefs, latest_message):
    genres = ["fiction", "non-fiction", "nonfiction", "mystery", "romance", "fantasy",
              "sci-fi", "thriller", "horror", "comedy", "drama", "memoir", "historical",
              "biography", "poetry", "adventure", "coming-of-age", "noir", "satire"]
    msg = latest_message.lower()
    if any(g in msg for g in genres):
        return True
    return any(any(g in b.statement.lower() for g in genres) for b in beliefs
               if b.lifecycle.value in ("active", "candidate", "challenged"))


def _eval_character(beliefs, latest_message):
    names = re.findall(r'\b[A-Z][a-z]{2,}\b', latest_message)
    keywords = ["protagonist", "character", "hero", "heroine", "lead", "main character",
                "named", "called", "follows"]
    msg = latest_message.lower()
    has_name = len(names) >= 1
    has_keyword = any(k in msg for k in keywords)
    if has_name or has_keyword:
        return True
    return any(any(k in b.statement.lower() for k in keywords) for b in beliefs
               if b.lifecycle.value in ("active", "candidate", "challenged"))


def _eval_setting(beliefs, latest_message):
    msg = latest_message.lower()
    location_preps = ["in ", "at ", "from ", "born in", "set in", "takes place",
                      "happens in", "located in", "based in", "live in", "lives in",
                      "grew up in", "raised in", "come from", "comes from"]
    time_patterns = [r'\b\d{4}\b', r'\bfuture\b', r'\bpast\b', r'\bpresent\b',
                     r'\bera\b', r'\bcentury\b', r'\bdecade\b', r'\byear\b',
                     r'\btoday\b', r'\bnow\b', r'\bmodern\b', r'\bcurrent\b']
    has_location = any(p in msg for p in location_preps)
    has_time = any(re.search(p, msg) for p in time_patterns)
    place_names = set(re.findall(r'\b[A-Z][a-z]{2,}\b', latest_message))
    if has_location or has_time or len(place_names) >= 2:
        return True
    return any(any(p in b.statement.lower() for p in location_preps) for b in beliefs
               if b.lifecycle.value in ("active", "candidate", "challenged"))


def _eval_conflict(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["conflict", "tension", "struggle", "journey", "goal", "want", "wants",
                "torn between", "must decide", "decided", "choice", "chose",
                "faces", "challenge", "problem",
                "tries to", "attempts to", "seeks to", "determined to"]
    return any(t in msg for t in triggers)


def _eval_theme(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["theme", "message", "meaning", "explore", "lesson", "moral",
                "what it means", "commentary", "reflects", "examines",
                "explores", "deals with", "grapples with"]
    return any(t in msg for t in triggers)


def _eval_audience(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["audience", "reader", "readers", "target", "fans", "listener", "viewer",
                "for ", "aimed at", "written for", "intended for", "demographic",
                "young adult", "children", "teen", "adult", "general"]
    return any(t in msg for t in triggers)


# -------- Film Evaluators ------------------------------------------------------

def _eval_emotional_core(beliefs, latest_message):
    msg = latest_message.lower()
    feelings = ["hope", "fear", "joy", "sad", "love", "grief", "anger", "wonder",
                "curiosity", "nostalgia", "belonging", "loss", "redemption",
                "forgiveness", "courage", "loneliness", "purpose", "meaning",
                "inspired", "moved", "touched", "feeling", "emotion", "feel"]
    return any(f in msg for f in feelings)


def _eval_film_theme(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["theme", "message", "meaning", "explore", "explores", "exploring",
                "lesson", "moral", "what it means", "commentary", "reflects",
                "examines", "deals with", "grapples with", "about"]
    return any(t in msg for t in triggers)


def _eval_film_character(beliefs, latest_message):
    names = re.findall(r'\b[A-Z][a-z]{2,}\b', latest_message)
    keywords = ["protagonist", "character", "hero", "heroine", "lead", "main char",
                "named", "called", "follows", "someone who", "a person",
                "a young", "an old", "a woman", "a man", "a child"]
    msg = latest_message.lower()
    has_name = len(names) >= 1
    has_keyword = any(k in msg for k in keywords)
    return has_name or has_keyword


def _eval_film_conflict(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["conflict", "tension", "struggle", "journey", "goal",
                "torn between", "must decide", "decided", "choice", "chose",
                "faces a", "face a", "challenge", "problem", "obstacle",
                "opposition", "tries to", "attempts to", "seeks to",
                "determined to", "stands in", "in the way", "barrier",
                "confront", "wants to", "want to", "struggles",
                "must choose", "has to decide"]
    return any(t in msg for t in triggers)


def _eval_visual_world(beliefs, latest_message):
    msg = latest_message.lower()
    triggers = ["world", "setting", "place", "visual", "look", "aesthetic",
                "landscape", "city", "future", "past", "era", "atmosphere",
                "mood", "tone", "style", "palette", "color", "environment",
                "universe", "realm", "dimension", "background"]
    return any(t in msg for t in triggers)


@dataclass
class DomainProfile:
    label: str
    discovery_priorities: List[DiscoveryPriority]
    label_question: str = ""


DOMAIN_PROFILES = {
    CreativeDomain.STORYTELLING: DomainProfile(
        label="Storytelling",
        label_question="Tell me about your story.",
        discovery_priorities=[
            DiscoveryPriority("Core Idea", "What's the story about?", keywords=["about", "follow", "set in", "world", "based"], evaluator=_eval_core_idea),
            DiscoveryPriority("Genre", "What kind of story is this — fiction, non-fiction, or something else?", keywords=["genre", "fiction", "mystery", "romance", "fantasy", "sci-fi", "thriller", "horror"], evaluator=_eval_genre),
            DiscoveryPriority("Main Character", "Who's the protagonist?", keywords=["character", "protagonist", "hero", "lead", "main character", "named", "protagonist", "teenager", "named", "character", "follower", "influencer", "girl", "boy"], evaluator=_eval_character),
            DiscoveryPriority("Conflict", "What's the central tension or journey?", keywords=["conflict", "tension", "journey", "struggle", "goal", "decided", "chose", "choice", "wanted", "wants", "influenced", "influence", "tempt", "pressure", "ignore", "ignores", "ignored", "abandon", "drop", "instead", "rather", "despite", "against", "refuse", "dream", "ambition", "obsess", "chasing", "chase"], evaluator=_eval_conflict),
            DiscoveryPriority("Setting", "Where and when does the story take place?", keywords=["setting", "world", "place", "time", "era", "location"], evaluator=_eval_setting),
            DiscoveryPriority("Theme", "What themes are you hoping to explore?", keywords=["theme", "message", "meaning", "explore"], evaluator=_eval_theme),
            DiscoveryPriority("Audience", "Who are you writing this for?", keywords=["audience", "reader", "fan"], evaluator=_eval_audience),
        ],
    ),
    CreativeDomain.MUSIC: DomainProfile(
        label="Music",
        label_question="What kind of music are you imagining?",
        discovery_priorities=[
            DiscoveryPriority("Emotion", "What emotion or feeling do you want this music to carry?", keywords=["emotion", "feeling", "vibe", "mood", "energy"]),
            DiscoveryPriority("Style", "What style or genre are you thinking about?", keywords=["genre", "style", "sound", "rap", "jazz", "rock", "pop", "electronic", "folk", "r&b", "soul"]),
            DiscoveryPriority("Message", "Is there a message or theme you want to express?", keywords=["theme", "message", "meaning", "express", "say"]),
            DiscoveryPriority("Artist Identity", "Is this for yourself, a project, or someone else?", keywords=["project", "alias", "identity", "myself", "band", "group"]),
            DiscoveryPriority("Sound Reference", "Are there any artists or songs that capture the sound you're after?", keywords=["reference", "inspired", "like", "reminds", "influence"]),
            DiscoveryPriority("Audience", "Who do you imagine listening to this?", keywords=["audience", "listener", "fan"]),
        ],
    ),
    CreativeDomain.SOFTWARE: DomainProfile(
        label="Software",
        label_question="What kind of software are you thinking of building?",
        discovery_priorities=[
            DiscoveryPriority("Problem", "What problem are you trying to solve?", keywords=["problem", "solve", "pain", "frustrat", "need"]),
            DiscoveryPriority("User", "Who experiences this problem?", keywords=["user", "customer", "people", "audience", "who"]),
            DiscoveryPriority("Core Function", "What should the software actually do?", keywords=["do", "feature", "function", "capability", "allow"]),
            DiscoveryPriority("Platform", "What platform — mobile, desktop, or web?", keywords=["mobile", "desktop", "web", "platform", "app", "ios", "android", "cross-platform"]),
            DiscoveryPriority("Constraints", "Any constraints — timeline, budget, or tech stack preferences?", keywords=["constraint", "timeline", "budget", "tech", "stack", "framework"]),
            DiscoveryPriority("Success Metric", "How will you know if it's working?", keywords=["success", "metric", "measure", "goal", "kpi"]),
        ],
    ),
    CreativeDomain.FILM: DomainProfile(
        label="Film",
        label_question="What kind of film are you imagining?",
        discovery_priorities=[
            DiscoveryPriority("Emotional Core", "What feeling do you want to stay with your audience?", keywords=["feel", "feeling", "emotion", "hope", "fear", "joy", "wonder"], evaluator=_eval_emotional_core),
            DiscoveryPriority("Theme", "What deeper idea are you exploring?", keywords=["theme", "message", "meaning", "explore", "about"], evaluator=_eval_film_theme),
            DiscoveryPriority("Main Character", "Who's the protagonist?", keywords=["character", "protagonist", "hero", "lead", "named"], evaluator=_eval_film_character),
            DiscoveryPriority("Conflict", "What stands in their way?", keywords=["conflict", "tension", "struggle", "goal", "wants", "against"], evaluator=_eval_film_conflict),
            DiscoveryPriority("Visual World", "What does this world look like?", keywords=["world", "setting", "visual", "look", "aesthetic", "place"], evaluator=_eval_visual_world),
            DiscoveryPriority("Audience", "Who are you making this for?", keywords=["audience", "viewer", "audiences", "for "], evaluator=_eval_audience),
        ],
    ),
    CreativeDomain.GAME: DomainProfile(
        label="Game Design",
        label_question="What kind of game do you have in mind?",
        discovery_priorities=[
            DiscoveryPriority("Core Concept", "What's the core idea or hook?", keywords=["about", "idea", "concept", "hook", "premise"]),
            DiscoveryPriority("Genre", "What genre — RPG, platformer, puzzle, narrative, or something else?", keywords=["genre", "rpg", "platformer", "puzzle", "narrative", "strategy", "simulation"]),
            DiscoveryPriority("Player Experience", "What should the player feel or experience?", keywords=["feel", "experience", "emotion", "atmosphere", "immersion"]),
            DiscoveryPriority("Mechanics", "What are the core mechanics or interactions?", keywords=["mechanic", "gameplay", "interact", "control", "system"]),
            DiscoveryPriority("Scope", "What's the scope — solo project, small team, or large production?", keywords=["scope", "solo", "team", "indie", "small", "large"]),
            DiscoveryPriority("Audience", "Who is this game for?", keywords=["audience", "player", "fan", "community"]),
        ],
    ),
    CreativeDomain.BUSINESS: DomainProfile(
        label="Business / Startup",
        label_question="Tell me about the venture you're building.",
        discovery_priorities=[
            DiscoveryPriority("Problem", "What problem are you solving?", keywords=["problem", "solve", "pain", "frustrat", "gap"]),
            DiscoveryPriority("Customer", "Who is the customer?", keywords=["customer", "client", "user", "buyer", "target market"]),
            DiscoveryPriority("Value Proposition", "What makes your approach different?", keywords=["different", "unique", "value", "proposition", "advantage", "moat"]),
            DiscoveryPriority("Market", "How big is the opportunity?", keywords=["market", "opportunity", "size", "growth", "trend"]),
            DiscoveryPriority("Business Model", "How will it sustain itself?", keywords=["model", "revenue", "pricing", "subscription", "monetize"]),
            DiscoveryPriority("Next Step", "What's the first thing you need to validate?", keywords=["validate", "next", "first", "mvp", "prototype", "test"]),
        ],
    ),
    CreativeDomain.EDUCATION: DomainProfile(
        label="Education",
        label_question="What do you want to teach?",
        discovery_priorities=[
            DiscoveryPriority("Subject", "What subject or skill do you want to teach?", keywords=["subject", "skill", "topic", "teach", "learn"]),
            DiscoveryPriority("Audience", "Who are the learners?", keywords=["learner", "student", "audience", "beginner", "advanced"]),
            DiscoveryPriority("Goal", "What should they walk away knowing or able to do?", keywords=["goal", "outcome", "walk away", "able to", "know"]),
            DiscoveryPriority("Format", "What format — course, workshop, curriculum, or resource?", keywords=["course", "workshop", "curriculum", "resource", "lesson", "module"]),
            DiscoveryPriority("Depth", "What depth — introductory, intermediate, or advanced?", keywords=["introductory", "intermediate", "advanced", "beginner", "level"]),
        ],
    ),
    CreativeDomain.RESEARCH: DomainProfile(
        label="Research",
        label_question="What question are you trying to answer?",
        discovery_priorities=[
            DiscoveryPriority("Question", "What research question are you trying to answer?", keywords=["question", "research", "investigat", "explore"]),
            DiscoveryPriority("Context", "What's already known in this space?", keywords=["known", "literature", "existing", "prior", "background", "context"]),
            DiscoveryPriority("Method", "How will you approach this?", keywords=["method", "approach", "methodology", "experiment", "study"]),
            DiscoveryPriority("Impact", "What would a meaningful result look like?", keywords=["impact", "result", "meaningful", "contribution", "significance"]),
            DiscoveryPriority("Resources", "What resources or access do you need?", keywords=["resource", "access", "data", "equipment", "funding", "collaboration"]),
        ],
    ),
    CreativeDomain.VISUAL_ART: DomainProfile(
        label="Visual Art",
        label_question="What kind of visual work are you creating?",
        discovery_priorities=[
            DiscoveryPriority("Medium", "What medium — painting, digital, sculpture, mixed media?", keywords=["medium", "painting", "digital", "sculpture", "mixed media", "illustration", "photography"]),
            DiscoveryPriority("Subject", "What's the subject or focus?", keywords=["subject", "focus", "about", "depict", "explore"]),
            DiscoveryPriority("Mood", "What mood or atmosphere are you after?", keywords=["mood", "atmosphere", "tone", "feeling", "emotion"]),
            DiscoveryPriority("Style", "Any stylistic inspirations or references?", keywords=["style", "reference", "inspired", "influence", "movement"]),
            DiscoveryPriority("Audience", "Who do you want to see this work?", keywords=["audience", "view", "exhibit", "share", "gallery"]),
        ],
    ),
}


_DOMAIN_RULES: List[tuple[str, CreativeDomain, int]] = [
    # Storytelling
    (r"(?:write|story|novel|fiction|narrative|book|memoir|script|screenplay|plot|character|chapter)", CreativeDomain.STORYTELLING, 10),
    (r"(?:poem|poetry|prose|literary|author|writer)", CreativeDomain.STORYTELLING, 10),
    (r"(?:short story|flash fiction|creative writing)", CreativeDomain.STORYTELLING, 15),
    # Music
    (r"(?:song|album|music|track|\bep\b|record|single|beat|melody|lyric|band|mixtape)", CreativeDomain.MUSIC, 10),
    (r"(?:rap|hip.?hop|jazz|rock|pop|folk|electronic|classical|r&b|soul|demo|produce)", CreativeDomain.MUSIC, 15),
    (r"(?:make (?:a|an|some) (?:song|beat|track|music|album))", CreativeDomain.MUSIC, 20),
    (r"(?:record\s+(?:a|an|some) (?:song|album|ep|track))", CreativeDomain.MUSIC, 20),
    # Software
    (r"(?:app|software|website|platform|tool|api|database|web.?site|mobile|desktop)", CreativeDomain.SOFTWARE, 10),
    (r"(?:feature|user story|sprint|deploy|code|program|developer|sdk)", CreativeDomain.SOFTWARE, 10),
    (r"(?:build\s+(?:a|an) (?:app|software|website|platform|tool|api))", CreativeDomain.SOFTWARE, 20),
    # Film
    (r"(?:film|movie|documentary|short film|video|cinema|director|producer|cinematography)", CreativeDomain.FILM, 10),
    (r"(?:animation|animator|storyboard|pilot episode)", CreativeDomain.FILM, 10),
    (r"(?:ai|artificial intelligence)\s*(?:-?\s*generated|made|created)?\s*(?:film|movie)", CreativeDomain.FILM, 25),
    (r"(?:shoot|make)\s+(?:a\s+)?(?:film|movie|documentary|short)", CreativeDomain.FILM, 20),
    # Game
    (r"(?:game|rpg|platformer|level|player|world|mechanics|narrative design)", CreativeDomain.GAME, 10),
    (r"(?:make|build|design)\s+(?:a\s+)?(?:game|rpg)", CreativeDomain.GAME, 20),
    # Business
    (r"(?:startup|business|company|product|venture|enterprise|entrepreneur)", CreativeDomain.BUSINESS, 10),
    (r"(?:revenue|funding|investor|pitch deck|go.?to.?market)", CreativeDomain.BUSINESS, 10),
    (r"(?:launch\s+(?:a|an) (?:startup|business|company|product|venture))", CreativeDomain.BUSINESS, 20),
    # Education
    (r"(?:course|curriculum|teach|learn|lesson|classroom|student|tutorial|workshop)", CreativeDomain.EDUCATION, 10),
    (r"(?:educator|teacher|training|syllabus|pedagogy)", CreativeDomain.EDUCATION, 10),
    (r"(?:create|make|build)\s+(?:a|an) (?:course|curriculum|lesson|workshop)", CreativeDomain.EDUCATION, 20),
    # Research
    (r"(?:research|paper|study|thesis|dissertation|experiment|hypothesis|journal)", CreativeDomain.RESEARCH, 10),
    (r"(?:literature review|methodology|data|findings|publication)", CreativeDomain.RESEARCH, 10),
    # Visual Art
    (r"(?:paint|draw|illustrate|sculpt|photograph|mixed media)", CreativeDomain.VISUAL_ART, 10),
    (r"(?:create|make)\s+(?:a |an )?(?:painting|illustration|sculpture|piece|art)", CreativeDomain.VISUAL_ART, 15),
]


def detect_domain(message: str, existing_domain: Optional[CreativeDomain] = None) -> CreativeDomain:
    msg_lower = message.lower().strip()
    scores: dict[CreativeDomain, int] = {}

    for pattern, domain, weight in _DOMAIN_RULES:
        if re.search(pattern, msg_lower):
            scores[domain] = scores.get(domain, 0) + weight

    if not scores:
        return existing_domain or CreativeDomain.UNKNOWN

    best = max(scores, key=scores.get)
    best_score = scores[best]

    if existing_domain and existing_domain != CreativeDomain.UNKNOWN:
        existing_score = scores.get(existing_domain, 0)

        # Creative medium domains are sticky.
        # Subject-matter keywords (education, business, research, etc.)
        # should not override an established medium like Storytelling, Music, Film, etc.
        if existing_domain in MEDIUM_DOMAINS:
            # Only switch to another medium if the new signal is materially stronger
            if best in MEDIUM_DOMAINS and best_score > existing_score + 2:
                return best
            # Never downgrade a medium to a subject domain on incidental keywords
            return existing_domain

        # Non-medium domains: keep the higher-scoring or existing domain
        if existing_score >= best_score:
            return existing_domain

    return best


def get_domain_profile(domain: CreativeDomain) -> DomainProfile:
    return DOMAIN_PROFILES.get(domain, DomainProfile(label="Project", label_question="Tell me more about your project.", discovery_priorities=[]))


def get_unaddressed_priorities(
    domain: CreativeDomain,
    beliefs_text: List[str],
    requirement_states: Optional[List] = None,
) -> List[DiscoveryPriority]:
    """Return DiscoveryPriorities that have not yet been satisfied.

    Mission 021A: requirement_states are checked first and are authoritative.
    A CONFIRMED or RESOLVED requirement is architecturally retired —
    it is never returned as unaddressed, regardless of keyword matching.
    Keyword matching on belief text acts as a secondary fallback for
    workspaces that predate requirement_states.
    """
    profile = get_domain_profile(domain)
    unaddressed: List[DiscoveryPriority] = []

    # Build set of areas that are already satisfied via requirement state
    confirmed_areas: set = set()
    if requirement_states:
        try:
            from core.schemas import RequirementStatus
            confirmed_areas = {
                r.area for r in requirement_states
                if r.status in (RequirementStatus.CONFIRMED, RequirementStatus.RESOLVED)
            }
        except ImportError:
            pass

    for priority in profile.discovery_priorities:
        # Requirement state is authoritative — confirmed means done
        if priority.area in confirmed_areas:
            continue

        # Fallback: keyword matching on belief text (legacy + pre-domain workspaces)
        addressed = False
        for text in beliefs_text:
            text_lower = text.lower()
            if priority.keywords:
                if any(kw in text_lower for kw in priority.keywords):
                    addressed = True
                    break
            elif priority.area.lower() in text_lower:
                addressed = True
                break
            for word in priority.area.lower().split():
                if word in text_lower and len(word) > 3:
                    addressed = True
                    break
        if not addressed:
            unaddressed.append(priority)

    return unaddressed


def activity_intro(activity: CreativeActivity, domain: CreativeDomain, beliefs_count: int = 0) -> str:
    domain_profile = get_domain_profile(domain)
    domain_name = domain_profile.label.lower() if domain != CreativeDomain.UNKNOWN else "project"
    activity_greeting = _ACTIVITY_LABELS.get(activity, "")

    if activity == CreativeActivity.BRAINSTORM or activity == CreativeActivity.EXPLORE:
        if domain != CreativeDomain.UNKNOWN:
            return f"{activity_greeting}. What kind of {domain_name} are you imagining?"
        return f"{activity_greeting}. What's on your mind?"
    if activity == CreativeActivity.RESEARCH:
        return f"{activity_greeting}. What question are you trying to answer?"
    if activity == CreativeActivity.PLAN:
        return f"{activity_greeting}. What's the goal you're working toward?"
    if activity == CreativeActivity.GENERATE:
        if beliefs_count > 0:
            return f"I can help bring this to life once I understand it fully."
        return f"{activity_greeting}. Tell me what you have in mind."
    if activity == CreativeActivity.REVIEW:
        return f"{activity_greeting}. What would you like me to look at?"
    if activity == CreativeActivity.CRITIQUE:
        return f"{activity_greeting}. Share what you've got and I'll tell you what I see."
    if activity == CreativeActivity.REFINE:
        return f"{activity_greeting}. What part are you looking to improve?"

    return ""


def normalize_input(message: str) -> str:
    msg = message.strip()
    msg = re.sub(r'\bI will your\b', 'I need your', msg, flags=re.IGNORECASE)
    msg = re.sub(r'\bI will\b', "I'd like", msg, flags=re.IGNORECASE)
    msg = re.sub(r'\byour help\b', 'help', msg, flags=re.IGNORECASE)
    msg = re.sub(r'\bcan I\b', 'I want to', msg, flags=re.IGNORECASE)
    msg = re.sub(r'\bcould you\b', 'please', msg, flags=re.IGNORECASE)
    msg = re.sub(r'\bwanna\b', 'want to', msg, flags=re.IGNORECASE)
    msg = re.sub(r'\bgonna\b', 'going to', msg, flags=re.IGNORECASE)
    return msg
