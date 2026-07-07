import pytest
from core.eval import EvaluationEngine, EVAL_RULES
from core.schemas import EvalAssessment


class TestEvaluationChecks:

    def test_all_checks_defined_for_launch_plan(self):
        assert "launch_plan" in EVAL_RULES
        assert len(EVAL_RULES["launch_plan"]) == 7

    def test_check_has_strategy_pass(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"release_strategy": "A" * 100}, "launch_plan")
        strategy_check = next(c for c in result.checks if c.name == "Has Strategy")
        assert strategy_check.passed is True

    def test_check_has_strategy_fail(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"release_strategy": ""}, "launch_plan")
        strategy_check = next(c for c in result.checks if c.name == "Has Strategy")
        assert strategy_check.passed is False

    def test_check_has_next_actions_pass(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"next_actions": [{"action": "a", "why": "b"}]}, "launch_plan")
        check = next(c for c in result.checks if c.name == "Has Next Actions")
        assert check.passed is True

    def test_check_has_next_actions_empty(self):
        engine = EvaluationEngine()
        result = engine.evaluate({}, "launch_plan")
        check = next(c for c in result.checks if c.name == "Has Next Actions")
        assert check.passed is False

    def test_action_details_missing_fields(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"next_actions": [{}]}, "launch_plan")
        check = next(c for c in result.checks if c.name == "Action Details")
        assert check.passed is False

    def test_action_details_all_have_fields(self):
        engine = EvaluationEngine()
        result = engine.evaluate(
            {"next_actions": [{"action": "Do X", "why": "Because Y"}, {"action": "Do Z", "why": "Because W"}]},
            "launch_plan",
        )
        check = next(c for c in result.checks if c.name == "Action Details")
        assert check.passed is True


class TestEvaluationEngine:

    def test_perfect_artifact(self):
        engine = EvaluationEngine()
        artifact = {
            "release_strategy": "Plan to launch the EP across multiple phases with full marketing support",
            "audience_profile": "Tech-savvy Afrofuturist enthusiasts aged 18-35",
            "next_actions": [{"action": "Lock date", "why": "Need certainty"}],
            "marketing_angles": ["Angle one with enough length to pass the threshold"],
            "confidence_score": 0.85,
        }
        result = engine.evaluate(artifact, "launch_plan")
        assert result.score > 0.8
        assert result.status == "ready"

    def test_empty_artifact(self):
        engine = EvaluationEngine()
        result = engine.evaluate({}, "launch_plan")
        assert result.score == 0.0
        assert result.status == "incomplete"
        assert len(result.recommendations) > 0

    def test_unknown_artifact_type(self):
        engine = EvaluationEngine()
        result = engine.evaluate({}, "unknown_type")
        assert result.score == 1.0
        assert result.status == "ready"
        assert result.checks == []

    def test_deterministic(self):
        engine = EvaluationEngine()
        artifact = {"release_strategy": "A" * 100, "audience_profile": "Test"}
        r1 = engine.evaluate(artifact, "launch_plan")
        r2 = engine.evaluate(artifact, "launch_plan")
        assert r1.score == r2.score
        assert r1.checks == r2.checks

    def test_status_thresholds(self):
        engine = EvaluationEngine()
        assert engine._derive_status(0.9) == "ready"
        assert engine._derive_status(0.8) == "ready"
        assert engine._derive_status(0.65) == "needs_revision"
        assert engine._derive_status(0.5) == "needs_revision"
        assert engine._derive_status(0.3) == "incomplete"
        assert engine._derive_status(0.0) == "incomplete"

    def test_recommendations_for_failing_checks(self):
        engine = EvaluationEngine()
        result = engine.evaluate({}, "launch_plan")
        for rec in result.recommendations:
            assert isinstance(rec, str) and len(rec) > 0

    def test_confidence_based_on_check_coverage(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"release_strategy": "A" * 100}, "launch_plan")
        assert result.confidence == 1.0  # 7 checks >= 6 target

    def test_passes_unknown_fields_gracefully(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"unexpected_field": "value"}, "launch_plan")
        assert isinstance(result, EvalAssessment)
        assert result.score == 0.0

    def test_eval_time_is_positive(self):
        engine = EvaluationEngine()
        result = engine.evaluate({"release_strategy": "A" * 100}, "launch_plan")
        assert result.eval_time_ms > 0

    def test_no_mutation_of_artifact(self):
        engine = EvaluationEngine()
        original = {"release_strategy": "A" * 100}
        before = dict(original)
        engine.evaluate(original, "launch_plan")
        assert original == before


class TestCampaignEval:

    def test_campaign_checks_registered(self):
        assert "campaign_plan" in EVAL_RULES
        assert len(EVAL_RULES["campaign_plan"]) == 8

    def test_perfect_campaign(self):
        engine = EvaluationEngine()
        artifact = {
            "campaign_name": "Digital Diaspora Launch",
            "campaign_objectives": ["Build awareness", "Drive streams"],
            "target_segments": ["Core fans", "New listeners"],
            "channel_strategy": ["Social media", "Email"],
            "content_themes": ["Behind the scenes", "Visualizers"],
            "kpis": ["10k streams first week"],
            "timeline_weeks": 12,
            "next_actions": [{"action": "Finalize budget", "why": "Need cost clarity"}],
        }
        result = engine.evaluate(artifact, "campaign_plan")
        assert result.score >= 0.8
        assert result.status == "ready"

    def test_empty_campaign(self):
        engine = EvaluationEngine()
        result = engine.evaluate({}, "campaign_plan")
        assert result.score == 0.0
        assert result.status == "incomplete"

    def test_missing_kpis_is_detected(self):
        engine = EvaluationEngine()
        artifact = {"campaign_name": "Test", "campaign_objectives": ["Obj1"]}
        result = engine.evaluate(artifact, "campaign_plan")
        kpi_check = next(c for c in result.checks if c.name == "Has KPIs")
        assert kpi_check.passed is False

    def test_campaign_deterministic(self):
        engine = EvaluationEngine()
        artifact = {"campaign_name": "Test", "campaign_objectives": ["Obj1"], "kpis": ["KPI1"]}
        r1 = engine.evaluate(artifact, "campaign_plan")
        r2 = engine.evaluate(artifact, "campaign_plan")
        assert r1.score == r2.score
        assert r1.checks == r2.checks
