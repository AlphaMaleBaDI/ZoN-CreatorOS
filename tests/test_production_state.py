import pytest
from core.schemas import ProductionState, StateEvidence, StateAssessment
from core.pie import ProductionIntelligenceEngine


@pytest.fixture
def pie():
    return ProductionIntelligenceEngine()


class TestProductionStateEnum:
    def test_enum_values(self):
        assert ProductionState.IDEATION.value == "ideation"
        assert ProductionState.PLANNING.value == "planning"
        assert ProductionState.PRODUCTION.value == "production"
        assert ProductionState.PUBLISHING.value == "publishing"
        assert ProductionState.RELEASED.value == "released"
        assert ProductionState.ARCHIVED.value == "archived"

    def test_enum_order(self):
        values = [s.value for s in ProductionState]
        assert values == ["ideation", "planning", "production", "publishing", "released", "archived"]


class TestStateEvidence:
    def test_basic_evidence(self):
        e = StateEvidence(artifact_type="launch_plan", exists=True, eval_score=0.8, eval_passed=True)
        assert e.artifact_type == "launch_plan"
        assert e.exists is True
        assert e.eval_score == 0.8
        assert e.eval_passed is True

    def test_missing_artifact(self):
        e = StateEvidence(artifact_type="campaign_plan", exists=False)
        assert e.exists is False
        assert e.eval_score is None
        assert e.eval_passed is None


class TestStateAssessment:
    def test_basic_assessment(self):
        sa = StateAssessment(
            current_state=ProductionState.PLANNING,
            evidence=[StateEvidence(artifact_type="launch_plan", exists=True)],
            requirements=["Create Campaign Plan"],
            next_state=ProductionState.PRODUCTION,
            can_transition=False,
            blockers=["Campaign Plan does not exist"],
        )
        assert sa.current_state == ProductionState.PLANNING
        assert sa.next_state == ProductionState.PRODUCTION
        assert sa.can_transition is False
        assert len(sa.blockers) == 1


class TestDetermineState:
    def test_ideation_no_artifacts(self, pie):
        sa = pie.determine_state(set(), {})
        assert sa.current_state == ProductionState.IDEATION
        assert sa.can_transition is False
        assert len(sa.blockers) > 0

    def test_planning_with_launch_plan(self, pie):
        sa = pie.determine_state({"launch_plan"}, {})
        assert sa.current_state == ProductionState.PLANNING
        assert sa.next_state == ProductionState.PRODUCTION
        assert sa.can_transition is False  # campaign_plan missing

    def test_planning_ready_to_advance(self, pie):
        existing = {"launch_plan", "campaign_plan"}
        scores = {"launch_plan": 0.8, "campaign_plan": 0.7}
        sa = pie.determine_state(existing, scores)
        assert sa.current_state == ProductionState.PLANNING
        assert sa.can_transition is True
        assert sa.next_state == ProductionState.PRODUCTION
        assert len(sa.blockers) == 0

    def test_production_with_content_calendar(self, pie):
        existing = {"launch_plan", "campaign_plan", "content_calendar"}
        scores = {"launch_plan": 0.8, "campaign_plan": 0.7, "content_calendar": 0.9}
        sa = pie.determine_state(existing, scores)
        assert sa.current_state == ProductionState.PRODUCTION
        assert len(sa.evidence) > 0

    def test_eval_below_threshold_blocks_transition(self, pie):
        existing = {"launch_plan", "campaign_plan"}
        scores = {"launch_plan": 0.3, "campaign_plan": 0.7}
        sa = pie.determine_state(existing, scores)
        assert sa.can_transition is False
        blocker_found = any("eval below threshold" in b for b in sa.blockers)
        assert blocker_found

    def test_determinism(self, pie):
        existing = {"launch_plan", "campaign_plan"}
        scores = {"launch_plan": 0.8, "campaign_plan": 0.7}
        r1 = pie.determine_state(existing, scores)
        r2 = pie.determine_state(existing, scores)
        assert r1.current_state == r2.current_state
        assert r1.can_transition == r2.can_transition
        assert r1.blockers == r2.blockers

    def test_state_evidence_includes_all_artifact_types(self, pie):
        existing = {"launch_plan", "campaign_plan"}
        sa = pie.determine_state(existing, {})
        types_found = {e.artifact_type for e in sa.evidence}
        assert "launch_plan" in types_found
        assert "campaign_plan" in types_found
        assert "content_calendar" in types_found
        assert len(sa.evidence) > 3

    def test_requirements_are_actionable(self, pie):
        existing = {"launch_plan"}
        sa = pie.determine_state(existing, {})
        assert len(sa.requirements) > 0
        for req in sa.requirements:
            assert "Planning" in req or "Production" in req or "Publishing" in req or "launch" in req.lower() or "campaign" in req.lower()

    def test_publishing_transition(self, pie):
        existing = {"launch_plan", "campaign_plan", "content_calendar", "publishing_checklist"}
        scores = {"launch_plan": 0.8, "campaign_plan": 0.7, "content_calendar": 0.9}
        sa = pie.determine_state(existing, scores)
        # production is dominant because content_calendar + launch + campaign all score well
        assert sa.current_state in (ProductionState.PRODUCTION, ProductionState.PUBLISHING)


class TestAnalyzeIntegration:
    def test_analyze_includes_state_assessment(self, pie):
        assessment = pie.analyze("launch_plan", {"launch_plan"}, {"launch_plan": 0.8})
        assert assessment.state_assessment is not None
        assert assessment.state_assessment.current_state.value in ("ideation", "planning")

    def test_analyze_state_assessment_is_deterministic(self, pie):
        existing = {"launch_plan", "campaign_plan"}
        scores = {"launch_plan": 0.8, "campaign_plan": 0.7}
        a1 = pie.analyze("launch_plan", existing, scores)
        a2 = pie.analyze("launch_plan", existing, scores)
        assert a1.state_assessment.current_state == a2.state_assessment.current_state

    def test_analyze_backward_compatible(self, pie):
        assessment = pie.analyze("launch_plan", {"launch_plan"}, {"launch_plan": 0.8})
        assert hasattr(assessment, "production_state")
        assert hasattr(assessment, "production_progress")
        assert hasattr(assessment, "completed")
        assert hasattr(assessment, "missing")
        assert hasattr(assessment, "recommended_next")
        assert hasattr(assessment, "narrative")

    def test_without_eval_scores(self, pie):
        assessment = pie.analyze("launch_plan", {"launch_plan"})
        assert assessment.state_assessment is not None
        assert assessment.state_assessment.current_state == ProductionState.PLANNING

    def test_unknown_artifact_type(self, pie):
        assessment = pie.analyze("unknown_type", set())
        assert assessment.state_assessment is not None
        assert assessment.state_assessment.current_state == ProductionState.IDEATION
