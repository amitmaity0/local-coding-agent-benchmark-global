"""Candidate ranking module.

Ranks candidates within an iteration by their QA scores and selects
the best candidate for optimization.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from orchestrator.models import Candidate


def rank_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Rank candidates by overall_score, then identity_score, then motion_score.

    Candidates without an optimization_score (failed analysis) are ranked last.

    Args:
        candidates: List of Candidate objects to rank.

    Returns:
        Sorted list of candidates (highest-ranked first).
    """
    def sort_key(c: Candidate) -> tuple[float, float, float]:
        score = c.optimization_score or 0.0
        identity = 0.0
        motion = 0.0
        if c.qa_report:
            identity = float(c.qa_report.get("identity_score", 0.0))
            motion = float(c.qa_report.get("motion_score", 0.0))
        return (score, identity, motion)

    ranked = sorted(candidates, key=sort_key, reverse=True)
    logger.info(
        f"Ranked {len(ranked)} candidates: "
        + ", ".join(
            f"c{c.candidate_id[:8]}(score={c.optimization_score or 0.0:.3f})"
            for c in ranked
        )
    )
    return ranked


def select_best_candidate(
    candidates: list[Candidate],
) -> Optional[Candidate]:
    """Select the highest-ranked candidate.

    Args:
        candidates: List of Candidate objects.

    Returns:
        The best candidate, or None if the list is empty.
    """
    if not candidates:
        return None

    ranked = rank_candidates(candidates)
    best = ranked[0]
    logger.info(
        f"Selected best candidate: {best.candidate_id[:8]} "
        f"score={best.optimization_score or 0.0:.3f}"
    )
    return best