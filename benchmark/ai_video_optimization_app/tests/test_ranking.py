"""Tests for orchestrator/ranking.py candidate ranking logic."""
from orchestrator.models import Candidate
from orchestrator.ranking import rank_candidates, select_best_candidate


def _make_candidate(
    overall: float, identity: float, motion: float, number: int = 1
) -> Candidate:
    return Candidate(
        candidate_id=f"cand-{number}",
        iteration=1,
        seed=1000 + number,
        workflow="",
        output_video="",
        qa_report={
            "overall_score": overall,
            "identity_score": identity,
            "motion_score": motion,
        },
        optimization_score=overall,
        status="completed",
        is_best_in_iteration=False,
        is_best_in_experiment=False,
    )


class TestRankCandidates:
    def test_ranks_by_overall_score_desc(self):
        candidates = [
            _make_candidate(0.5, 0.6, 0.7, 1),
            _make_candidate(0.9, 0.8, 0.7, 2),
            _make_candidate(0.7, 0.5, 0.6, 3),
        ]
        ranked = rank_candidates(candidates)
        assert [c.candidate_id for c in ranked] == ["cand-2", "cand-3", "cand-1"]

    def test_ties_broken_by_identity_score(self):
        candidates = [
            _make_candidate(0.8, 0.5, 0.7, 1),
            _make_candidate(0.8, 0.9, 0.7, 2),
        ]
        ranked = rank_candidates(candidates)
        assert ranked[0].candidate_id == "cand-2"

    def test_ties_broken_by_motion_score(self):
        candidates = [
            _make_candidate(0.8, 0.7, 0.5, 1),
            _make_candidate(0.8, 0.7, 0.9, 2),
        ]
        ranked = rank_candidates(candidates)
        assert ranked[0].candidate_id == "cand-2"

    def test_single_candidate(self):
        candidates = [_make_candidate(0.5, 0.6, 0.7, 1)]
        ranked = rank_candidates(candidates)
        assert len(ranked) == 1
        assert ranked[0].candidate_id == "cand-1"

    def test_empty_list(self):
        ranked = rank_candidates([])
        assert ranked == []


class TestSelectBestCandidate:
    def test_returns_highest_overall_score(self):
        candidates = [
            _make_candidate(0.5, 0.6, 0.7, 1),
            _make_candidate(0.9, 0.8, 0.7, 2),
        ]
        best = select_best_candidate(candidates)
        assert best.candidate_id == "cand-2"

    def test_returns_none_for_empty_list(self):
        assert select_best_candidate([]) is None

    def test_marks_only_one_best(self):
        candidates = [
            _make_candidate(0.9, 0.8, 0.7, 1),
            _make_candidate(0.9, 0.5, 0.7, 2),
        ]
        best = select_best_candidate(candidates)
        assert best.candidate_id == "cand-1"