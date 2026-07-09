"""
Onboarding Engine — goal-driven conversation.

Not a wizard. A first collaboration.

The engine knows what context it needs.
It doesn't care about the order.
Every message fills some gaps.
When enough is complete, it assembles.
"""

import time
import logging
from uuid import uuid4, UUID
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from core.context_extractor import ContextExtractor, ContextExtraction

logger = logging.getLogger(__name__)


@dataclass
class ContextNeeds:
    """What the system needs to understand before assembling a workspace."""
    creator_name: bool = False
    project: bool = False
    domain: bool = False
    audience: bool = False
    vision: bool = False
    timeline: bool = False
    brand: bool = False

    @property
    def filled(self) -> int:
        return sum(1 for v in [self.creator_name, self.project, self.domain,
                                self.audience, self.vision, self.timeline,
                                self.brand] if v)

    @property
    def total(self) -> int:
        return 7

    @property
    def completion(self) -> float:
        return self.filled / self.total

    @property
    def is_sufficient(self) -> bool:
        """Enough context to assemble a workspace."""
        return self.domain and self.vision and self.creator_name


@dataclass
class ConversationMessage:
    role: str  # "system" or "user"
    text: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    workspace_id: Optional[str] = None
    messages: List[ConversationMessage] = field(default_factory=list)
    extraction: ContextExtraction = field(default_factory=ContextExtraction)
    needs: ContextNeeds = field(default_factory=ContextNeeds)
    phase: str = "active"  # active | assembling | complete
    created_at: float = field(default_factory=time.time)


# In-memory session store
_sessions: Dict[str, ConversationSession] = {}


def get_session(session_id: str) -> Optional[ConversationSession]:
    return _sessions.get(session_id)


def create_session() -> ConversationSession:
    session = ConversationSession()
    _sessions[session.session_id] = session
    return session


def delete_session(session_id: str):
    _sessions.pop(session_id, None)


class OnboardingEngine:
    """Goal-driven conversation engine.

    Tracks what context is needed, asks the most valuable next question,
    and assembles the workspace when sufficient context exists.
    """

    def __init__(self):
        self.extractor = ContextExtractor()

    def start(self, session: ConversationSession) -> str:
        """Generate the opening message."""
        msg = (
            "Before we begin...\n\n"
            "Tell me what you're trying to create."
        )
        session.messages.append(ConversationMessage(role="system", text=msg))
        return msg

    def process_message(self, session: ConversationSession, user_input: str) -> str:
        """Process a user message. Extract context. Decide next action."""
        session.messages.append(ConversationMessage(role="user", text=user_input))

        # Handle confirmation phase
        if session.phase == "confirming":
            return self._handle_confirmation(session, user_input)

        ext = self.extractor.extract(user_input, existing=session.extraction)
        session.extraction = ext

        self._update_needs(session, user_input, ext)

        # Enough to confirm: domain + vision + creator_name
        # Audience is a bonus but not required for confirmation
        has_enough = (
            ext.domain and session.needs.vision and
            session.needs.creator_name
        )
        if has_enough and session.phase == "active":
            session.phase = "confirming"
            return self._confirm_and_assemble(session)

        return self._ask_next_question(session, ext)

        return self._ask_next_question(session, ext)

    def _update_needs(self, session: ConversationSession, text: str, ext: ContextExtraction):
        needs = session.needs
        t = text.lower()

        if not needs.creator_name:
            name_patterns = [
                "i'm", "my name is", "i am", "call me",
                "i go by", "i'm known as",
            ]
            matched = False
            for p in name_patterns:
                if p in t:
                    idx = t.index(p) + len(p)
                    words = text[idx:].split()
                    if words:
                        ext.creator_name = words[0].strip(".,!?;:")
                        needs.creator_name = True
                        matched = True
                    break
            # Short response = likely a name (e.g. user just types "Christopher")
            if not matched and len(text.split()) <= 2 and len(text) < 30:
                ext.creator_name = text.strip(".,!?")
                needs.creator_name = True

        if not needs.domain and ext.domain:
            needs.domain = True

        if not needs.vision:
            if len(text.split()) >= 8:
                needs.vision = True

        if not needs.audience and ext.audience:
            needs.audience = True

        if not needs.timeline and ext.timeline:
            needs.timeline = True

        if not needs.project and ext.project_name:
            needs.project = True
        elif not needs.project and len(text.split()) >= 4 and ext.domain:
            ext.project_name = self._infer_project_name(text, ext.domain)
            if ext.project_name:
                needs.project = True

        if not needs.brand:
            brand_keywords = ["voice", "tone", "style", "aesthetic", "vibe", "energy", "mood"]
            if any(kw in t for kw in brand_keywords):
                needs.brand = True

    def _infer_project_name(self, text: str, domain: str) -> Optional[str]:
        import re
        # Try to extract a meaningful noun phrase
        # "I want to release an afrofuturistic EP about identity" → "Afrofuturistic EP"
        patterns = [
            r'\b(?:a|an|the|my|our|this|that)\s+([\w\s]+?)\s+(?:about|exploring|that|which|for|to)\b',
            r'\b(?:a|an|the|my|our|this|that)\s+([\w\s]+?)$',
            r'\b(\w+\s+(?:EP|LP|Album|Single|Film|Project|Collection|Exhibition))\b',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if 2 < len(name) < 40:
                    return name.title()

        domain_names = {
            "music": "Untitled EP",
            "film": "Untitled Film",
            "visual_art": "Untitled Exhibition",
            "fashion": "Untitled Collection",
            "tech": "Untitled Project",
        }
        return domain_names.get(domain, "Untitled Film")

    def _ask_next_question(self, session: ConversationSession, ext: ContextExtraction) -> str:
        needs = session.needs

        if not needs.creator_name:
            return "Who's creating this?"

        if not needs.domain:
            if ext.project_name:
                return f"Tell me more about {ext.project_name}. What kind of work is it?"
            return "What kind of project is this?"

        if not needs.vision:
            return "What's the story behind it? What are you trying to say?"

        if not needs.audience:
            return "Who is this for? Who do you want to reach?"

        if not needs.timeline:
            return "When do you want to have this ready?"

        if not needs.project:
            return "What would you like to call this project?"

        if not needs.brand:
            return "What's the energy you want this to carry?"

        return "Tell me anything else about your vision."

    def _confirm_and_assemble(self, session: ConversationSession) -> str:
        ext = session.extraction
        parts = ["Here's how I understand your vision.\n"]

        parts.append("---")
        if ext.project_name:
            parts.append(f"\nProject\n  {ext.project_name}")
        if ext.domain:
            parts.append(f"\nDomain\n  {ext.domain.title()}")
        if ext.themes:
            parts.append(f"\nThemes\n  {', '.join(t.replace('_', ' ').title() for t in ext.themes)}")
        if ext.audience:
            parts.append(f"\nAudience\n  {ext.audience.title()}")
        if ext.goals:
            parts.append(f"\nGoals\n  {ext.goals[0].title()}")
        if ext.timeline:
            parts.append(f"\nTimeline\n  {ext.timeline}")
        parts.append("\n---")
        parts.append("\nDid I understand correctly?")
        parts.append("\n\nType 'yes' to begin, or tell me what to adjust.")

        msg = "\n".join(parts)
        session.messages.append(ConversationMessage(role="system", text=msg))
        return msg

    def _handle_confirmation(self, session: ConversationSession, user_input: str) -> str:
        """Handle user response to confirmation."""
        t = user_input.lower().strip()
        affirmatives = ["yes", "yeah", "yep", "correct", "looks good", "perfect", "great", "that's right", "spot on"]
        if any(a in t for a in affirmatives):
            return self._assemble_and_respond(session)
        else:
            # User is refining — extract new context and re-confirm
            ext = self.extractor.extract(user_input, existing=session.extraction)
            session.extraction = ext
            self._update_needs(session, user_input, ext)

            # If they gave us a name, mark it
            if not session.needs.creator_name:
                name_patterns = ["i'm ", "my name is ", "i am ", "call me ", "i go by "]
                for p in name_patterns:
                    if p in t:
                        idx = t.index(p) + len(p)
                        name = user_input[idx:].split()[0:2]
                        ext.creator_name = " ".join(name).strip(".,!?")
                        session.needs.creator_name = True
                        break
                # If no pattern matched but it's a short response, treat as name
                if not session.needs.creator_name and len(user_input.split()) <= 3:
                    ext.creator_name = user_input.strip(".,!?")
                    session.needs.creator_name = True

            session.phase = "confirming"
            return self._confirm_and_assemble(session)

    def _assemble_and_respond(self, session: ConversationSession) -> str:
        session.phase = "assembling"
        ext = session.extraction

        workspace_id = self._assemble_workspace(session)

        msg = self._build_assembly_summary(session, workspace_id)
        session.messages.append(ConversationMessage(role="system", text=msg))
        session.phase = "complete"
        return msg

    def _assemble_workspace(self, session: ConversationSession) -> str:
        """Create workspace, project, and profile from extracted context."""
        from services.workspace_service import WorkspaceService
        from services.profile_service import ProfileService
        from memory.creator_profile import CreatorProfile

        ws_service = WorkspaceService()
        profile_service = ProfileService()

        ext = session.extraction
        project_name = ext.project_name or "Untitled Film"
        creator_name = ext.creator_name or "OdiBa"

        ws = ws_service.create_workspace("CreatorOS")
        session.workspace_id = str(ws.workspace_id)

        ws_service.create_project(ws.workspace_id, project_name)

        profile = CreatorProfile(
            creator_name=creator_name,
            brand_voice=self._infer_brand_voice(ext),
            writing_style="authentic",
            goals=ext.goals or ["complete the project"],
            preferred_platforms=self._infer_platforms(ext),
            personality=self._infer_personality(ext),
            preferred_tools=[],
            working_habits=[],
        )
        profile_service.update_creator_profile(profile)

        self._store_understanding(session, ws.workspace_id)

        logger.info(f"Workspace assembled: {ws.workspace_id} — {project_name}")
        return str(ws.workspace_id)

    def _store_understanding(self, session: ConversationSession, workspace_id):
        """Store Workspace Understanding — the canonical description."""
        import json, os
        ext = session.extraction

        understanding = {
            "project": ext.project_name or "Untitled Project",
            "purpose": f"Explore {', '.join(ext.themes)} through {ext.domain}." if ext.themes else f"Create {ext.domain} work.",
            "audience": ext.audience or "General audience",
            "creator_intent": ext.goals[0] if ext.goals else "Complete the project.",
            "current_goal": "Complete Planning.",
            "domain": ext.domain,
            "themes": ext.themes,
            "timeline": ext.timeline,
        }

        path = os.path.join("workspace_db", str(workspace_id))
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "understanding.json"), "w") as f:
            json.dump(understanding, f, indent=2)

    def _build_assembly_summary(self, session: ConversationSession, workspace_id: str) -> str:
        ext = session.extraction
        creator = ext.creator_name or "Creator"
        project = ext.project_name or "your project"

        parts = [
            f"Workspace assembled.",
            f"\nWelcome back, {creator}.",
            f"\nYour workspace is ready.",
            f"\nProject: {project}",
            f"Domain: {ext.domain.title() if ext.domain else 'Creative'}",
        ]

        if ext.themes:
            parts.append(f"Themes: {', '.join(t.replace('_', ' ').title() for t in ext.themes)}")

        parts.append("\n\nEntering workspace...")
        return "\n".join(parts)

    def _infer_brand_voice(self, ext: ContextExtraction) -> str:
        theme_str = " ".join(ext.themes)
        if "afrofuturism" in theme_str or "technology" in theme_str:
            return "bold visionary"
        if "identity" in theme_str or "spirituality" in theme_str:
            return "introspective storyteller"
        if "social_impact" in theme_str:
            return "passionate advocate"
        if "love" in theme_str:
            return "emotional wordsmith"
        if "urban" in theme_str:
            return "streetwise narrator"
        return "authentic voice"

    def _infer_platforms(self, ext: ContextExtraction) -> List[str]:
        platforms = []
        if ext.domain == "music":
            platforms = ["spotify", "bandcamp", "instagram"]
        elif ext.domain == "film":
            platforms = ["youtube", "vimeo", "film festivals"]
        elif ext.domain == "visual_art":
            platforms = ["instagram", "gallery", "online exhibition"]
        elif ext.domain == "fashion":
            platforms = ["instagram", "shopify", "lookbook"]
        elif ext.domain == "tech":
            platforms = ["product hunt", "twitter", "github"]
        else:
            platforms = ["instagram", "website"]
        return platforms

    def _infer_personality(self, ext: ContextExtraction) -> str:
        themes = set(ext.themes)
        if "afrofuturism" in themes or "technology" in themes:
            return "Creative"
        if "spirituality" in themes or "nature" in themes:
            return "Reflective"
        if "social_impact" in themes or "resilience" in themes:
            return "Energetic"
        if "urban" in themes:
            return "Energetic"
        return "Creative"
