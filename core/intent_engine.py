"""
Creator Intent Engine — production-command detector.

Returns an IntentDecision only when the message contains an explicit production command.
Returns None when the message is creative conversation, exploratory input, or has no matched production intent.

The creative partner path (Observer + ShadowReasoning) owns all conversational actions.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from core.orchestration import ARTIFACT_METADATA, INTENT_KEYWORDS

logger = logging.getLogger(__name__)


@dataclass
class IntentDecision:
    action: str  # "generate" | "summarize" | "clarify" | "confirm"
    artifact_type: str = ""
    narrative: str = ""
    requires_confirmation: bool = False


@dataclass
class WorkspaceContext:
    current_state: str = "ideation"
    next_state: Optional[str] = None
    transition_artifact: Optional[str] = None
    existing_artifact_types: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    recommended_next: List[str] = field(default_factory=list)
    completed_count: int = 0
    creator_name: str = "Creator"
    project_name: str = ""


ADVANCEMENT_KEYWORDS = [
    "next", "proceed", "continue", "ready", "advance",
    "yes", "yeah", "yep", "ok", "okay", "sure", "let's", "lets",
    "go", "do it", "start", "begin", "move forward",
]

STATUS_KEYWORDS = [
    "how are we", "how are you", "status", "where are we",
    "summary", "progress", "how's it going", "what's up",
]

BLOCKER_KEYWORDS = [
    "blocker", "stuck", "wrong", "problem", "what's wrong",
    "issue", "holding", "waiting", "what's blocking",
]

RECOMMEND_KEYWORDS = [
    "what should", "help", "suggest", "recommend", "what do i",
    "advice", "what's next", "next step", "what now",
]

PROJECT_KEYWORDS = [
    "about my project", "tell me about", "what am i",
    "what's my project", "remind me", "what are we",
]

DIAGNOSTICS_KEYWORDS = [
    "diagnostics", "debug", "inspect", "what's happening",
    "what is the state",
]

FINISH_KEYWORDS = [
    "finish", "complete", "done", "wrap up", "finalize",
    "release", "ship", "launch it",
]


class IntentEngine:

    def resolve(self, text: str, context: WorkspaceContext) -> Optional[IntentDecision]:
        t = text.lower().strip()

        if not t:
            return None

        # Greeting — treat as conversational, not production
        if t in ("hi", "hello", "hey", "yo", "sup"):
            return None

        # Help
        if t in ("help", "?"):
            return self._help_decision(context)

        # Finish / release intent — explicit production command
        if any(kw in t for kw in FINISH_KEYWORDS):
            return self._resolve_finish(context)

        # Explicit artifact generation intents — scoring-based keyword matching
        best_type = None
        best_score = 0
        for artifact_type, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in t)
            if score > best_score:
                if ARTIFACT_METADATA.get(artifact_type):
                    best_score = score
                    best_type = artifact_type
        if best_type:
            return self._resolve_explicit_intent(best_type, ARTIFACT_METADATA[best_type], context)

        # "Plan" keyword — explicit production command
        if "plan" in t:
            return self._resolve_plan_intent(context)

        # Advancement intents — explicit production commands
        if any(kw in t for kw in ADVANCEMENT_KEYWORDS):
            return self._resolve_advancement(context)

        # Discovery intents — explicit production commands
        if any(kw in t for kw in STATUS_KEYWORDS):
            return self._build_status_response(context)

        if any(kw in t for kw in BLOCKER_KEYWORDS):
            return self._build_blockers_response(context)

        if any(kw in t for kw in RECOMMEND_KEYWORDS):
            return self._build_recommendation_response(context)

        if any(kw in t for kw in PROJECT_KEYWORDS):
            return self._build_project_summary(context)

        if any(kw in t for kw in DIAGNOSTICS_KEYWORDS):
            return IntentDecision(
                "summarize",
                narrative="Pipeline diagnostics available at /workspaces/{id}/diagnostics. "
                          "Check the workspace state, existing artifact types, and transition status.",
            )

        return None

    def _resolve_explicit_intent(self, artifact_type: str, metadata: dict, ctx: WorkspaceContext) -> IntentDecision:
        label = metadata["label"]

        if artifact_type in ctx.existing_artifact_types:
            return IntentDecision(
                "summarize", artifact_type=artifact_type,
                narrative=f"{label} is already complete. "
                          f"Current state: {ctx.current_state.title()}.",
            )

        if ctx.blockers:
            next_artifact = self._find_next_recommended(ctx)
            if next_artifact:
                next_meta = ARTIFACT_METADATA.get(next_artifact, {})
                next_label = next_meta.get("label", next_artifact)
                return IntentDecision(
                    "summarize", artifact_type=artifact_type,
                    narrative=f"Before I can generate {label}, you need: "
                              f"{ctx.blockers[0]}\n\n"
                              f"Try generating {next_label} first.",
                )
            return IntentDecision(
                "summarize", artifact_type=artifact_type,
                narrative=f"Currently blocked: {ctx.blockers[0]}",
            )

        return IntentDecision(
            "generate", artifact_type=artifact_type,
            narrative=f"Generating {label}...",
        )

    def _resolve_advancement(self, ctx: WorkspaceContext) -> IntentDecision:
        next_artifact = self._find_next_recommended(ctx)
        if not next_artifact:
            return IntentDecision(
                "summarize",
                narrative="All production milestones are complete. Ready for release.",
            )

        metadata = ARTIFACT_METADATA.get(next_artifact)
        if not metadata:
            return IntentDecision(
                "summarize",
                narrative=f"All available milestones complete. "
                          f"Current state: {ctx.current_state.title()}.",
            )

        label = metadata["label"]
        return IntentDecision(
            "generate", artifact_type=next_artifact,
            narrative=f"Next milestone: {label}.\n"
                      f"Generating {label} now...",
        )

    def _resolve_finish(self, ctx: WorkspaceContext) -> IntentDecision:
        pipeline_artifacts = ["publishing_checklist", "release_complete"]
        missing = [t for t in pipeline_artifacts
                   if t not in ctx.existing_artifact_types]
        if not missing:
            return IntentDecision(
                "summarize",
                narrative="Everything is complete. The project is ready for release.",
            )
        next_artifact = self._find_next_recommended(ctx)
        if next_artifact:
            metadata = ARTIFACT_METADATA.get(next_artifact, {})
            label = metadata.get("label", next_artifact)
            return IntentDecision(
                "generate", artifact_type=next_artifact,
                narrative=f"Let's wrap this up. Next: {label}.\nGenerating now...",
            )
        return IntentDecision(
            "summarize",
            narrative=f"We're in {ctx.current_state.title()}. "
                      f"{ctx.requirements[0] if ctx.requirements else 'Continue when ready.'}",
        )

    def _resolve_plan_intent(self, ctx: WorkspaceContext) -> IntentDecision:
        return self._resolve_advancement(ctx)

    def _build_status_response(self, ctx: WorkspaceContext) -> IntentDecision:
        parts = [f"You're in **{ctx.current_state.title()}**."]
        if ctx.completed_count > 0:
            parts.append(f"{ctx.completed_count} milestone(s) completed.")

        if ctx.blockers:
            parts.append(f"Blocked: {ctx.blockers[0]}")
        elif ctx.requirements:
            parts.append(f"Next: {ctx.requirements[0]}")
        else:
            parts.append("No blockers. Production is flowing.")

        next_artifact = self._find_next_recommended(ctx)
        if next_artifact:
            metadata = ARTIFACT_METADATA.get(next_artifact, {})
            label = metadata.get("label", next_artifact)
            parts.append(f"Recommended next: {label}")

        return IntentDecision("summarize", narrative="\n".join(parts))

    def _build_blockers_response(self, ctx: WorkspaceContext) -> IntentDecision:
        if not ctx.blockers:
            return IntentDecision(
                "summarize",
                narrative="No blockers found. Everything is on track.",
            )
        if ctx.requirements:
            return IntentDecision(
                "summarize",
                narrative=f"Blocked: {ctx.blockers[0]}\n"
                          f"Next action: {ctx.requirements[0]}",
            )
        return IntentDecision(
            "summarize",
            narrative=f"Blocked: {ctx.blockers[0]}",
        )

    def _build_recommendation_response(self, ctx: WorkspaceContext) -> IntentDecision:
        next_artifact = self._find_next_recommended(ctx)
        if not next_artifact:
            return IntentDecision(
                "summarize",
                narrative="All milestones complete.",
            )
        metadata = ARTIFACT_METADATA.get(next_artifact, {})
        label = metadata.get("label", next_artifact)
        return IntentDecision(
            "confirm", artifact_type=next_artifact,
            narrative=f"Highest-impact next step: **{label}**.\n\nSay 'yes' to generate.",
        )

    def _build_project_summary(self, ctx: WorkspaceContext) -> IntentDecision:
        parts = [f"Project: {ctx.project_name or 'Untitled'}"]
        parts.append(f"State: {ctx.current_state.title()}")
        if ctx.existing_artifact_types:
            parts.append("Completed: " + ", ".join(
                ARTIFACT_METADATA.get(a, {}).get("label", a.replace("_", " ").title())
                for a in ctx.existing_artifact_types
            ))
        return IntentDecision("summarize", narrative="\n".join(parts))

    def _help_decision(self, ctx: WorkspaceContext) -> IntentDecision:
        return IntentDecision(
            "summarize",
            narrative="You can tell me what you want to do in your own words.\n\n"
                      'Try:\n'
                      '  "Next"\n'
                      '  "How are we doing?"\n'
                      '  "What\'s blocking us?"\n'
                      '  "Generate content calendar"\n'
                      '  "I\'m ready to finish"',
        )

    def _find_next_recommended(self, ctx: WorkspaceContext) -> Optional[str]:
        # Priority 1: artifact required to advance to the next production state
        if ctx.transition_artifact and ctx.transition_artifact not in ctx.existing_artifact_types:
            if ctx.transition_artifact in ARTIFACT_METADATA:
                return ctx.transition_artifact
        # Priority 2: filter PIE recommendations against what we can generate
        if ctx.recommended_next:
            for atype in ctx.recommended_next:
                if atype in ARTIFACT_METADATA and atype not in ctx.existing_artifact_types:
                    return atype
        # Priority 3: parse requirements text for known artifact type names
        if ctx.requirements:
            for req in ctx.requirements:
                req_lower = req.lower()
                for atype in ARTIFACT_METADATA:
                    if atype.replace("_", " ") in req_lower and atype not in ctx.existing_artifact_types:
                        return atype
        return None
