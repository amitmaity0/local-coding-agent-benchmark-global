"""Tests for the analytics service (Task 8).

Covers score progression, QA metric progression, candidate statistics,
best candidate selection, parameter history, strategy statistics, and
edge cases (incomplete iterations, failed candidates, missing data).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator.analytics import (
    calculate_experiment_metrics,
    calculate_iteration_metrics,
    calculate_metric_progression,
    calculate_parameter_impact,
    calculate_score_progression,
    calculate_strategy_stats,
    generate_experiment_summary,
    get_best_results,
    get_full_analytics,
)
from orchestrator.config import AppConfig, DatabaseConfig
from orchestrator.database import Base, init_db
from orchestrator.models import CandidateORM, ExperimentORM, IterationORM


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture()
def db_config():
    """Create a config with an in-memory SQLite database."""
    return DatabaseConfig(url="sqlite:///:memory:")


@pytest.fixture()
def session(db_config):
    """Initialize DB and yield a session."""
    init_db(db_config)
    from orchestrator.database import _engine

    session = _engine._session_factory()
    Base.metadata.create_all(bind=_engine.engine)
    yield session
    session.rollback()
    session.close()


def _create_experiment(session, **kwargs):
    """Helper: create an experiment and return its ORM object."""
    defaults = {
        "prompt": "A cat walking",
        "negative_prompt": "",
        "target_score": 0.8,
        "max_iterations": 10,
        "cfg": 7.0,
        "noise": 0.1,
    }
    defaults.update(kwargs)
    exp = ExperimentORM(**defaults)
    session.add(exp)
    session.flush()
    return exp


def _create_iteration(session, experiment_id, number, **kwargs):
    """Helper: create an iteration and return its ORM object."""
    defaults = {
        "experiment_id": experiment_id,
        "number": number,
        "score": None,
        "status": "completed",
    }
    defaults.update(kwargs)
    it = IterationORM(**defaults)
    session.add(it)
    session.flush()
    return it


def _create_candidate(session, iteration_id, number, **kwargs):
    """Helper: create a candidate and return its ORM object."""
    defaults = {
        "iteration_id": iteration_id,
        "number": number,
        "seed": 42 + number,
        "optimization_score": None,
        "status": "completed",
        "is_best_in_iteration": 0,
        "qa_report": None,
    }
    defaults.update(kwargs)
    cand = CandidateORM(**defaults)
    session.add(cand)
    session.flush()
    return cand


def _build_experiment_with_iterations(
    session, num_iterations=3, candidates_per_iter=2, scores=None
):
    """Build a complete experiment with iterations and scored candidates.

    Args:
        session: DB session.
        num_iterations: Number of iterations to create.
        candidates_per_iter: Candidates per iteration.
        scores: Optional list of lists of candidate scores.
            If None, auto-generates increasing scores.

    Returns:
        The ExperimentORM object.
    """
    exp = _create_experiment(session)

    if scores is None:
        scores = []
        base = 0.5
        for i in range(num_iterations):
            iter_scores = [base + i * 0.1 + j * 0.02 for j in range(candidates_per_iter)]
            scores.append(iter_scores)

    for i in range(num_iterations):
        it_score = max(scores[i]) if scores[i] else None
        it = _create_iteration(session, exp.id, i + 1, score=it_score)

        for j in range(candidates_per_iter):
            is_best = 1 if j == candidates_per_iter - 1 else 0
            cand_score = scores[i][j] if j < len(scores[i]) else None
            qa = {
                "overall_score": cand_score or 0.5,
                "identity_score": 0.7 + i * 0.05,
                "motion_score": 0.6 + i * 0.08,
                "camera_score": 0.65 + i * 0.03,
                "hands_score": 0.5 + i * 0.1,
                "face_score": 0.75 + i * 0.02,
                "lighting_score": 0.8 - i * 0.01,
                "physics_score": 0.7 + i * 0.04,
                "lip_sync_score": 0.6 + i * 0.05,
                "continuity_score": 0.55 + i * 0.07,
            }
            _create_candidate(
                session, it.id, j + 1,
                optimization_score=cand_score,
                is_best_in_iteration=is_best,
                qa_report=json.dumps(qa),
            )

    session.commit()
    return exp


# ── Score Progression Tests ────────────────────────────────────────


class TestScoreProgression:
    def test_empty_experiment(self, session):
        exp = _create_experiment(session)
        session.commit()
        result = calculate_score_progression(exp.id)
        assert result == []

    def test_single_iteration(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.72)
        session.commit()
        result = calculate_score_progression(exp.id)
        assert len(result) == 1
        assert result[0].iteration == 1
        assert result[0].score == 0.72

    def test_multiple_iterations_ordered(self, session):
        exp = _create_experiment(session)
        _create_iteration(session, exp.id, 3, score=0.85)
        _create_iteration(session, exp.id, 1, score=0.60)
        _create_iteration(session, exp.id, 2, score=0.72)
        session.commit()
        result = calculate_score_progression(exp.id)
        assert len(result) == 3
        assert [e.iteration for e in result] == [1, 2, 3]
        assert [e.score for e in result] == [0.60, 0.72, 0.85]

    def test_iterations_with_none_scores(self, session):
        exp = _create_experiment(session)
        _create_iteration(session, exp.id, 1, score=0.70)
        _create_iteration(session, exp.id, 2, score=None)
        _create_iteration(session, exp.id, 3, score=0.80)
        session.commit()
        result = calculate_score_progression(exp.id)
        assert len(result) == 3
        assert result[1].score is None


# ── Experiment Metrics Tests ───────────────────────────────────────


class TestExperimentMetrics:
    def test_empty_experiment(self, session):
        exp = _create_experiment(session)
        session.commit()
        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.total_iterations == 0
        assert metrics.total_candidates == 0
        assert metrics.best_overall_score is None

    def test_basic_metrics(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=3, candidates_per_iter=2
        )
        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.total_iterations == 3
        assert metrics.total_candidates == 6
        assert metrics.best_overall_score is not None
        assert metrics.initial_score is not None

    def test_successful_and_failed_candidates(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.75)
        _create_candidate(session, it.id, 1, optimization_score=0.75, status="completed")
        _create_candidate(session, it.id, 2, optimization_score=None, status="failed")
        session.commit()

        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.successful_candidates == 1
        assert metrics.failed_candidates == 1

    def test_nonexistent_experiment(self, session):
        metrics = calculate_experiment_metrics("nonexistent-id")
        assert metrics.total_iterations == 0


# ── QA Metric Progression Tests ────────────────────────────────────


class TestQAMetricProgression:
    def test_empty_experiment(self, session):
        exp = _create_experiment(session)
        session.commit()
        result = calculate_metric_progression(exp.id)
        assert all(len(v) == 0 for v in result.values())

    def test_all_dimensions_tracked(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=2, candidates_per_iter=1
        )
        result = calculate_metric_progression(exp.id)
        expected_dims = [
            "identity_score", "motion_score", "camera_score",
            "hands_score", "face_score", "lighting_score",
            "physics_score", "lip_sync_score", "continuity_score",
        ]
        for dim in expected_dims:
            assert dim in result

    def test_progression_values_increase(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=3, candidates_per_iter=1
        )
        result = calculate_metric_progression(exp.id)
        # Motion should increase across iterations (0.6, 0.68, 0.76)
        motion_vals = [v["value"] for v in result["motion_score"]]
        assert len(motion_vals) == 3
        assert motion_vals[1] > motion_vals[0]

    def test_missing_qa_metrics_handled_safely(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.70)
        # Candidate with no QA report
        _create_candidate(
            session, it.id, 1, optimization_score=0.70,
            is_best_in_iteration=1, qa_report=None,
        )
        session.commit()
        result = calculate_metric_progression(exp.id)
        assert all(len(v) == 0 for v in result.values())

    def test_invalid_json_qa_report(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.70)
        _create_candidate(
            session, it.id, 1, optimization_score=0.70,
            is_best_in_iteration=1, qa_report="not valid json",
        )
        session.commit()
        result = calculate_metric_progression(exp.id)
        assert all(len(v) == 0 for v in result.values())


# ── Candidate Analytics Tests ──────────────────────────────────────


class TestCandidateAnalytics:
    def test_iteration_metrics_basic(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=2, candidates_per_iter=3
        )
        result = calculate_iteration_metrics(exp.id)
        assert len(result) == 2

        # First iteration should have 3 candidates
        im0 = result[0]
        assert im0.num_candidates == 3
        assert im0.best_candidate_score is not None
        assert im0.worst_candidate_score is not None
        assert im0.average_candidate_score is not None
        assert im0.score_spread >= 0

    def test_winning_candidate(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.80)
        _create_candidate(
            session, it.id, 1, optimization_score=0.75, seed=100,
            is_best_in_iteration=0,
        )
        _create_candidate(
            session, it.id, 2, optimization_score=0.80, seed=200,
            is_best_in_iteration=1,
        )
        session.commit()

        result = calculate_iteration_metrics(exp.id)
        assert len(result) == 1
        assert result[0].winning_candidate == 2
        assert result[0].winning_seed == 200

    def test_score_spread(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.90)
        _create_candidate(session, it.id, 1, optimization_score=0.60)
        _create_candidate(session, it.id, 2, optimization_score=0.90, is_best_in_iteration=1)
        session.commit()

        result = calculate_iteration_metrics(exp.id)
        assert result[0].score_spread == pytest.approx(0.30)


# ── Best Result Tests ──────────────────────────────────────────────


class TestBestResult:
    def test_empty_experiment(self, session):
        exp = _create_experiment(session)
        session.commit()
        result = get_best_results(exp.id)
        assert result.score is None

    def test_selects_highest_scored_candidate(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=3, candidates_per_iter=2
        )
        result = get_best_results(exp.id)
        # Best should be from iteration 3 (highest scores)
        assert result.score is not None
        assert result.iteration == 3

    def test_returns_candidate_details(self, session):
        exp = _create_experiment(session, prompt="A dog running", cfg=8.0)
        it = _create_iteration(session, exp.id, 1, score=0.85)
        _create_candidate(
            session, it.id, 1, optimization_score=0.85, seed=42,
            output_video="/path/to/video.mp4", is_best_in_iteration=1,
        )
        session.commit()

        result = get_best_results(exp.id)
        assert result.score == 0.85
        assert result.seed == 42
        assert result.output_video == "/path/to/video.mp4"
        assert result.prompt == "A dog running"
        assert result.cfg == 8.0


# ── Parameter History Tests ────────────────────────────────────────


class TestParameterHistory:
    def test_empty_experiment(self, session):
        exp = _create_experiment(session)
        session.commit()
        result = calculate_parameter_impact(exp.id)
        assert all(len(v) == 0 for v in result.values())

    def test_tracks_seed_changes(self, session):
        exp = _create_experiment(session)
        it1 = _create_iteration(session, exp.id, 1, score=0.60)
        _create_candidate(
            session, it1.id, 1, optimization_score=0.60, seed=100,
            is_best_in_iteration=1, workflow=json.dumps({"cfg": 7.0}),
        )
        it2 = _create_iteration(session, exp.id, 2, score=0.75)
        _create_candidate(
            session, it2.id, 1, optimization_score=0.75, seed=200,
            is_best_in_iteration=1, workflow=json.dumps({"cfg": 7.0}),
        )
        session.commit()

        result = calculate_parameter_impact(exp.id)
        # Seed changed from 100 to 200
        assert len(result["seed"]) == 1
        assert result["seed"][0].old_value == 100
        assert result["seed"][0].new_value == 200

    def test_tracks_cfg_changes(self, session):
        exp = _create_experiment(session)
        it1 = _create_iteration(session, exp.id, 1, score=0.60)
        _create_candidate(
            session, it1.id, 1, optimization_score=0.60, seed=100,
            is_best_in_iteration=1, workflow=json.dumps({"cfg": 7.0}),
        )
        it2 = _create_iteration(session, exp.id, 2, score=0.75)
        _create_candidate(
            session, it2.id, 1, optimization_score=0.75, seed=200,
            is_best_in_iteration=1, workflow=json.dumps({"cfg": 8.5}),
        )
        session.commit()

        result = calculate_parameter_impact(exp.id)
        assert len(result["cfg"]) == 1
        assert result["cfg"][0].old_value == 7.0
        assert result["cfg"][0].new_value == 8.5


# ── Strategy Statistics Tests ──────────────────────────────────────


class TestStrategyStatistics:
    def test_empty_experiment(self, session):
        exp = _create_experiment(session)
        session.commit()
        result = calculate_strategy_stats(exp.id)
        assert result == []

    def test_reads_strategy_from_optimization_json(self, session, tmp_path):
        exp = _create_experiment(session)

        # Create optimization.json files for two iterations
        dir1 = tmp_path / "iter1"
        dir1.mkdir()
        opt_file1 = dir1 / "optimization.json"
        opt_file1.write_text(json.dumps({"optimization_mode": "TARGETED"}))

        dir2 = tmp_path / "iter2"
        dir2.mkdir()
        opt_file2 = dir2 / "optimization.json"
        opt_file2.write_text(json.dumps({"optimization_mode": "EXPLORE"}))

        it1 = _create_iteration(
            session, exp.id, 1, score=0.70, report_path=str(dir1 / "report.json")
        )
        it2 = _create_iteration(
            session, exp.id, 2, score=0.85, report_path=str(dir2 / "report.json")
        )
        session.commit()

        result = calculate_strategy_stats(exp.id)
        strategies = {s.strategy: s for s in result}
        assert "TARGETED" in strategies
        assert "EXPLORE" in strategies
        assert strategies["TARGETED"].iterations == 1
        assert strategies["EXPLORE"].iterations == 1

    def test_calculates_improvement(self, session, tmp_path):
        exp = _create_experiment(session)

        dir1 = tmp_path / "iter1"
        dir1.mkdir()
        (dir1 / "optimization.json").write_text(
            json.dumps({"optimization_mode": "REFINE"})
        )

        it1 = _create_iteration(
            session, exp.id, 1, score=0.60, report_path=str(dir1 / "report.json")
        )
        it2 = _create_iteration(session, exp.id, 2, score=0.80)
        session.commit()

        result = calculate_strategy_stats(exp.id)
        # Only iteration 1 has a strategy file; the improvement from 0.60 to 0.80
        # is attributed to REFINE (the strategy used in iter 1).
        refine = next((s for s in result if s.strategy == "REFINE"), None)
        assert refine is not None


# ── Experiment Summary Tests ───────────────────────────────────────


class TestExperimentSummary:
    def test_summary_with_data(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=5, candidates_per_iter=3
        )
        summary = generate_experiment_summary(exp.id)
        assert summary["total_iterations"] == 5
        assert summary["total_candidates"] == 15
        assert summary["best_iteration"] > 0

    def test_summary_with_no_data(self, session):
        exp = _create_experiment(session)
        session.commit()
        summary = generate_experiment_summary(exp.id)
        assert summary["total_iterations"] == 0
        assert summary["score_range"] == "-"


# ── Full Analytics Integration Tests ───────────────────────────────


class TestFullAnalytics:
    def test_returns_all_sections(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=3, candidates_per_iter=2
        )
        result = get_full_analytics(exp.id)

        assert "experiment_id" in result
        assert "metrics" in result
        assert "score_progression" in result
        assert "qa_progression" in result
        assert "iteration_metrics" in result
        assert "parameter_history" in result
        assert "best_result" in result
        assert "strategy_stats" in result
        assert "summary" in result

    def test_empty_experiment_returns_valid_structure(self, session):
        exp = _create_experiment(session)
        session.commit()
        result = get_full_analytics(exp.id)
        assert result["metrics"]["total_iterations"] == 0
        assert result["score_progression"] == []


# ── Edge Case Tests ────────────────────────────────────────────────


class TestEdgeCases:
    def test_incomplete_iteration(self, session):
        exp = _create_experiment(session)
        it1 = _create_iteration(session, exp.id, 1, score=0.70, status="completed")
        _create_candidate(
            session, it1.id, 1, optimization_score=0.70, is_best_in_iteration=1,
        )
        # Iteration 2 has no candidates (incomplete)
        it2 = _create_iteration(session, exp.id, 2, score=None, status="generating")
        session.commit()

        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.total_iterations == 2
        assert metrics.total_candidates == 1

    def test_all_failed_candidates(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=None)
        _create_candidate(session, it.id, 1, status="failed")
        _create_candidate(session, it.id, 2, status="error")
        session.commit()

        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.failed_candidates == 2
        assert metrics.successful_candidates == 0

    def test_mixed_completed_and_failed(self, session):
        exp = _create_experiment(session)
        it = _create_iteration(session, exp.id, 1, score=0.75)
        _create_candidate(
            session, it.id, 1, optimization_score=0.75, status="completed",
            is_best_in_iteration=1,
        )
        _create_candidate(session, it.id, 2, status="failed")
        session.commit()

        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.successful_candidates == 1
        assert metrics.failed_candidates == 1

    def test_running_experiment(self, session):
        exp = _create_experiment(session, status="GENERATING")
        it = _create_iteration(session, exp.id, 1, score=0.65)
        _create_candidate(
            session, it.id, 1, optimization_score=0.65, is_best_in_iteration=1,
        )
        session.commit()

        # Analytics should work on running experiments too
        metrics = calculate_experiment_metrics(exp.id)
        assert metrics.total_iterations == 1
        assert metrics.best_overall_score == 0.65

    def test_completed_experiment(self, session):
        exp = _build_experiment_with_iterations(
            session, num_iterations=7, candidates_per_iter=3
        )
        # Mark experiment as completed
        from orchestrator.database import get_session
        with get_session() as s:
            e = s.query(ExperimentORM).filter_by(id=exp.id).first()
            e.status = "COMPLETED"

        summary = generate_experiment_summary(exp.id)
        assert summary["total_iterations"] == 7
        assert summary["total_candidates"] == 21

    def test_nonexistent_experiment(self, session):
        result = get_full_analytics("does-not-exist")
        assert result["metrics"]["total_iterations"] == 0