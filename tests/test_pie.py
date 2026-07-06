import pytest
from core.pie import ProductionIntelligenceEngine, PRODUCTION_KNOWLEDGE_GRAPH, _reachable_types


class TestProductionKnowledgeGraph:
    def test_reachable_from_launch_plan(self):
        reachable = _reachable_types("launch_plan", PRODUCTION_KNOWLEDGE_GRAPH)
        assert "launch_plan" in reachable
        assert "campaign_plan" in reachable
        assert "content_calendar" in reachable
        assert "press_release" in reachable
        assert "budget_plan" in reachable
        assert "content_script" in reachable
        assert "production_schedule" in reachable
        assert "media_kit" in reachable
        assert "press_distribution" in reachable
        assert "resource_allocation" in reachable

    def test_reachable_from_leaf(self):
        reachable = _reachable_types("content_script", PRODUCTION_KNOWLEDGE_GRAPH)
        assert reachable == {"content_script"}

    def test_unknown_type_includes_root(self):
        reachable = _reachable_types("nonexistent_type", PRODUCTION_KNOWLEDGE_GRAPH)
        assert reachable == {"nonexistent_type"}


class TestProductionIntelligenceEngine:
    def test_first_artifact(self):
        pie = ProductionIntelligenceEngine()
        assessment = pie.analyze("launch_plan", {"launch_plan"})
        assert assessment.completed == ["launch_plan"]
        assert "campaign_plan" in assessment.missing
        assert "content_calendar" in assessment.missing
        assert "press_release" in assessment.missing
        assert assessment.recommended_next[0] in ("campaign_plan", "content_calendar", "press_release")
        assert 0 < assessment.production_progress < 1
        assert assessment.confidence > 0

    def test_half_complete(self):
        pie = ProductionIntelligenceEngine()
        existing = {"launch_plan", "campaign_plan", "content_calendar"}
        assessment = pie.analyze("launch_plan", existing)
        assert "launch_plan" in assessment.completed
        assert "campaign_plan" in assessment.completed
        assert "content_calendar" in assessment.completed
        assert "press_release" in assessment.missing
        assert assessment.production_progress >= 0.3

    def test_fully_complete(self):
        pie = ProductionIntelligenceEngine()
        all_types = set(PRODUCTION_KNOWLEDGE_GRAPH.keys())
        assessment = pie.analyze("launch_plan", all_types)
        assert len(assessment.missing) == 0
        assert assessment.production_progress == 1.0

    def test_unknown_artifact_type(self):
        pie = ProductionIntelligenceEngine()
        assessment = pie.analyze("unknown_type", set())
        assert assessment.production_progress == 1.0
        assert assessment.confidence == 1.0

    def test_deterministic(self):
        pie = ProductionIntelligenceEngine()
        existing = {"launch_plan"}
        r1 = pie.analyze("launch_plan", existing)
        r2 = pie.analyze("launch_plan", existing)
        assert r1.model_dump() == r2.model_dump()

    def test_empty_workspace(self):
        pie = ProductionIntelligenceEngine()
        assessment = pie.analyze("launch_plan", set())
        assert len(assessment.completed) == 0
        assert len(assessment.missing) > 0
        assert assessment.production_progress == 0.0

    def test_recommended_next_is_actionable(self):
        pie = ProductionIntelligenceEngine()
        assessment = pie.analyze("launch_plan", {"launch_plan"})
        for rec in assessment.recommended_next:
            assert rec in PRODUCTION_KNOWLEDGE_GRAPH["launch_plan"]
