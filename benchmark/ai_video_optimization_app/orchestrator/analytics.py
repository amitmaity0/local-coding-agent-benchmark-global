"""Analytics service for experiment evaluation and progress tracking.

Provides read-only analytics over persisted experiment data.
Does not modify experiment state or alter the optimization loop.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from orchestrator.database import get_session
from orchestrator.models import CandidateORM, ExperimentORM, IterationORM


# ── Data Classes ──────────────────────────────────────────────────


@dataclass
class ExperimentMetrics:
    """Aggregated metrics for an entire experiment."""

    best_overall_score: Optional[float] = None
    initial_score: Optional[float] = None
    score_improvement: float = 0.0
    average_score: Optional[float] = None
    median_score: Optional[float] = None
    score_improvement_per_iteration: float = 0.0
    best_iteration: int = 0
    total_iterations: int = 0
    total_candidates: int = 0
    successful_candidates: int = 0
    failed_candidates: int = 0
    total_generation_time: float = 0.0
    total_analysis_time: float = 0.0
    total_optimization_time: float = 0.0


@dataclass
class IterationMetrics:
    """Metrics for a single iteration."""

    iteration: int = 0
    score: Optional[float] = None
    num_candidates: int = 0
    best_candidate_score: Optional[float] = None
    worst_candidate_score: Optional[float] = None
    average_candidate_score: Optional[float] = None
    score_spread: float = 0.0
    winning_candidate: Optional[int] = None
    winning_seed: Optional[int] = None
    status: str = ""


@dataclass
class ScoreEntry:
    """A single entry in the score progression."""

    iteration: int = 0
    score: Optional[float] = None


@dataclass
class MetricProgression:
    """Progression of a single QA metric across iterations."""

    metric_name: str = ""
    values: list[dict] = field(default_factory=list)


@dataclass
class ParameterChange:
    """Record of a parameter change between iterations."""

    parameter: str = ""
    old_value: Any = None
    new_value: Any = None
    score_before: Optional[float] = None
    score_after: Optional[float] = None


@dataclass
class StrategyStats:
    """Statistics for an optimization strategy."""

    strategy: str = ""
    iterations: int = 0
    average_improvement: float = 0.0
    best_improvement: float = 0.0
    success_rate: float = 0.0


@dataclass
class BestResult:
    """The best result across all candidates in an experiment."""

    iteration: int = 0
    candidate_number: int = 0
    candidate_id: str = ""
    score: Optional[float] = None
    seed: Optional[int] = None
    output_video: Optional[str] = None
    prompt: str = ""
    negative_prompt: str = ""
    cfg: float = 0.0
    noise: float = 0.0
    qa_report: Optional[dict] = None


# ── Core Analytics Functions ──────────────────────────────────────


def calculate_experiment_metrics(experiment_id: str) -> ExperimentMetrics:
    """Calculate aggregated metrics for an experiment.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        ExperimentMetrics with all aggregated values.
    """
    metrics = ExperimentMetrics()

    with get_session() as session:
        exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
        if not exp:
            return metrics

        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        # Gather all candidates across all iterations
        all_candidates: list[CandidateORM] = []
        for it in iterations:
            cands = (
                session.query(CandidateORM)
                .filter_by(iteration_id=it.id)
                .all()
            )
            all_candidates.extend(cands)

        # Score history from iterations
        scores = [it.score for it in iterations if it.score is not None]
        metrics.total_iterations = len(iterations)
        metrics.total_candidates = len(all_candidates)

        if scores:
            metrics.initial_score = scores[0]
            metrics.best_overall_score = max(scores)
            metrics.average_score = statistics.mean(scores)
            metrics.median_score = statistics.median(scores)
            metrics.score_improvement = scores[-1] - scores[0]

            # Find best iteration
            best_it = max(iterations, key=lambda i: i.score or 0.0)
            metrics.best_iteration = best_it.number

            if len(scores) > 1:
                metrics.score_improvement_per_iteration = (
                    (scores[-1] - scores[0]) / (len(scores) - 1)
                )
        elif exp.best_score is not None:
            metrics.best_overall_score = exp.best_score
            metrics.best_iteration = exp.best_iteration

        # Count successful vs failed candidates
        for c in all_candidates:
            if c.status == "completed":
                metrics.successful_candidates += 1
            elif c.status in ("failed", "error"):
                metrics.failed_candidates += 1
            else:
                # Candidates with a score are considered successful
                if c.optimization_score is not None:
                    metrics.successful_candidates += 1

        # Sum generation times
        for c in all_candidates:
            if c.generation_time is not None:
                metrics.total_generation_time += c.generation_time

    return metrics


def calculate_iteration_metrics(
    experiment_id: str,
) -> list[IterationMetrics]:
    """Calculate per-iteration metrics including candidate statistics.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        List of IterationMetrics, one per iteration.
    """
    results: list[IterationMetrics] = []

    with get_session() as session:
        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        for it in iterations:
            im = IterationMetrics(
                iteration=it.number,
                score=it.score,
                status=it.status,
            )

            cands = (
                session.query(CandidateORM)
                .filter_by(iteration_id=it.id)
                .order_by(CandidateORM.number.asc())
                .all()
            )

            im.num_candidates = len(cands)
            cand_scores = [
                c.optimization_score for c in cands
                if c.optimization_score is not None
            ]

            if cand_scores:
                im.best_candidate_score = max(cand_scores)
                im.worst_candidate_score = min(cand_scores)
                im.average_candidate_score = statistics.mean(cand_scores)
                im.score_spread = max(cand_scores) - min(cand_scores)

            # Find winning candidate (is_best_in_iteration flag)
            for c in cands:
                if c.is_best_in_iteration:
                    im.winning_candidate = c.number
                    im.winning_seed = c.seed
                    break

            results.append(im)

    return results


def calculate_score_progression(experiment_id: str) -> list[ScoreEntry]:
    """Calculate the score progression across iterations.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        List of ScoreEntry objects ordered by iteration number.
    """
    entries: list[ScoreEntry] = []

    with get_session() as session:
        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        for it in iterations:
            entries.append(
                ScoreEntry(iteration=it.number, score=it.score)
            )

    return entries


def calculate_metric_progression(
    experiment_id: str,
) -> dict[str, list[dict]]:
    """Calculate the progression of individual QA metrics across iterations.

    Tracks identity, motion, camera, hands, face, lighting,
    physics, lip_sync, and continuity scores per iteration.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        Dict mapping metric name to list of {iteration, value} dicts.
    """
    qa_dimensions = [
        "identity_score",
        "motion_score",
        "camera_score",
        "hands_score",
        "face_score",
        "lighting_score",
        "physics_score",
        "lip_sync_score",
        "continuity_score",
    ]

    # Initialize empty progressions
    progressions: dict[str, list[dict]] = {
        dim: [] for dim in qa_dimensions
    }

    with get_session() as session:
        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        for it in iterations:
            # Try to get QA report from the best candidate in this iteration
            best_cand = (
                session.query(CandidateORM)
                .filter_by(iteration_id=it.id, is_best_in_iteration=1)
                .first()
            )

            if not best_cand:
                # Fall back to first candidate with QA data
                best_cand = (
                    session.query(CandidateORM)
                    .filter_by(iteration_id=it.id)
                    .filter(CandidateORM.qa_report.isnot(None))
                    .first()
                )

            if not best_cand or not best_cand.qa_report:
                continue

            try:
                qa = json.loads(best_cand.qa_report)
            except (json.JSONDecodeError, TypeError):
                continue

            for dim in qa_dimensions:
                value = qa.get(dim)
                if value is not None:
                    progressions[dim].append(
                        {"iteration": it.number, "value": value}
                    )

    return progressions


def calculate_parameter_impact(
    experiment_id: str,
) -> dict[str, list[ParameterChange]]:
    """Track parameter changes across iterations.

    Records old value, new value, score before and after for each
    parameter change. Does not infer causality.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        Dict mapping parameter name to list of ParameterChange objects.
    """
    tracked_params = ["seed", "cfg", "noise", "steps", "prompt", "negative_prompt"]
    changes: dict[str, list[ParameterChange]] = {
        p: [] for p in tracked_params
    }

    with get_session() as session:
        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        # Collect parameters from each iteration's best candidate
        prev_params: dict[str, Any] = {}
        prev_score: Optional[float] = None

        for it in iterations:
            best_cand = (
                session.query(CandidateORM)
                .filter_by(iteration_id=it.id, is_best_in_iteration=1)
                .first()
            )

            if not best_cand:
                best_cand = (
                    session.query(CandidateORM)
                    .filter_by(iteration_id=it.id)
                    .first()
                )

            if not best_cand:
                continue

            # Extract parameters from candidate
            curr_params: dict[str, Any] = {
                "seed": best_cand.seed,
            }

            # Try to get workflow params
            if best_cand.workflow:
                try:
                    wf = json.loads(best_cand.workflow)
                    curr_params["cfg"] = wf.get("cfg", wf.get("cfg_scale"))
                    curr_params["noise"] = wf.get("noise")
                    curr_params["steps"] = wf.get("steps")
                except (json.JSONDecodeError, TypeError):
                    pass

            curr_score = it.score

            # Compare with previous iteration
            for param in tracked_params:
                old_val = prev_params.get(param)
                new_val = curr_params.get(param)
                if old_val is not None and new_val is not None and old_val != new_val:
                    changes[param].append(
                        ParameterChange(
                            parameter=param,
                            old_value=old_val,
                            new_value=new_val,
                            score_before=prev_score,
                            score_after=curr_score,
                        )
                    )

            prev_params = curr_params
            prev_score = curr_score

    return changes


def get_best_results(experiment_id: str) -> BestResult:
    """Find the best result across all candidates in an experiment.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        BestResult with the highest-scoring candidate data.
    """
    result = BestResult()

    with get_session() as session:
        exp = session.query(ExperimentORM).filter_by(id=experiment_id).first()
        if not exp:
            return result

        # Get all candidates with scores
        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        best_score: Optional[float] = None
        best_candidate: Optional[CandidateORM] = None
        best_iteration: Optional[IterationORM] = None

        for it in iterations:
            cands = (
                session.query(CandidateORM)
                .filter_by(iteration_id=it.id)
                .all()
            )
            for c in cands:
                if c.optimization_score is not None:
                    if best_score is None or c.optimization_score > best_score:
                        best_score = c.optimization_score
                        best_candidate = c
                        best_iteration = it

        if best_candidate and best_iteration:
            result.iteration = best_iteration.number
            result.candidate_number = best_candidate.number
            result.candidate_id = best_candidate.id
            result.score = best_candidate.optimization_score
            result.seed = best_candidate.seed
            result.output_video = best_candidate.output_video
            result.prompt = exp.prompt
            result.negative_prompt = exp.negative_prompt
            result.cfg = exp.cfg
            result.noise = exp.noise

            if best_candidate.qa_report:
                try:
                    result.qa_report = json.loads(best_candidate.qa_report)
                except (json.JSONDecodeError, TypeError):
                    pass

    return result


# ── Strategy Analytics ────────────────────────────────────────────


def calculate_strategy_stats(
    experiment_id: str,
) -> list[StrategyStats]:
    """Calculate statistics per optimization strategy.

    Reports observed correlations only; does not claim causation.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        List of StrategyStats, one per strategy used.
    """
    strategies: dict[str, StrategyStats] = {}

    with get_session() as session:
        iterations = (
            session.query(IterationORM)
            .filter_by(experiment_id=experiment_id)
            .order_by(IterationORM.number.asc())
            .all()
        )

        prev_score: Optional[float] = None

        for it in iterations:
            # Read optimization.json from iteration directory
            if it.report_path:
                import pathlib

                opt_path = pathlib.Path(it.report_path).parent / "optimization.json"
                if opt_path.exists():
                    try:
                        with open(opt_path) as f:
                            opt_data = json.load(f)
                        strategy = opt_data.get(
                            "optimization_mode", "REFINE"
                        )

                        if strategy not in strategies:
                            strategies[strategy] = StrategyStats(
                                strategy=strategy
                            )

                        stats = strategies[strategy]
                        stats.iterations += 1

                        curr_score = it.score
                        if prev_score is not None and curr_score is not None:
                            improvement = curr_score - prev_score
                            improvements = getattr(
                                stats, "_improvements", []
                            )
                            improvements.append(improvement)
                            stats._improvements = improvements

                            if improvement > 0:
                                successes = getattr(stats, "_successes", 0)
                                stats._successes = successes + 1

                            best_imp = getattr(stats, "best_improvement", 0.0)
                            if improvement > best_imp:
                                stats.best_improvement = improvement

                    except (FileNotFoundError, json.JSONDecodeError):
                        pass

            prev_score = it.score

    # Finalize computed fields
    result: list[StrategyStats] = []
    for stats in strategies.values():
        improvements = getattr(stats, "_improvements", [])
        if improvements:
            stats.average_improvement = statistics.mean(improvements)
        successes = getattr(stats, "_successes", 0)
        if improvements:
            stats.success_rate = successes / len(improvements)
        # Remove internal tracking attrs
        if hasattr(stats, "_improvements"):
            delattr(stats, "_improvements")
        if hasattr(stats, "_successes"):
            delattr(stats, "_successes")
        result.append(stats)

    return result


# ── Experiment Summary ────────────────────────────────────────────


def generate_experiment_summary(experiment_id: str) -> dict:
    """Generate a human-readable summary of the experiment.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        Dict with summary fields for display.
    """
    metrics = calculate_experiment_metrics(experiment_id)
    score_prog = calculate_score_progression(experiment_id)
    qa_prog = calculate_metric_progression(experiment_id)
    best = get_best_results(experiment_id)

    # Find primary improvements (QA dimensions that improved the most)
    primary_improvements: list[dict] = []
    for dim, values in qa_prog.items():
        if len(values) >= 2:
            first = values[0]["value"]
            last = values[-1]["value"]
            delta = last - first
            if delta > 0:
                # Convert dimension name to display name
                display = dim.replace("_score", "").replace("_", " ").title()
                primary_improvements.append(
                    {
                        "dimension": display,
                        "improvement": round(delta, 2),
                    }
                )
    primary_improvements.sort(key=lambda x: x["improvement"], reverse=True)

    # Build score range string
    score_range = "-"
    if metrics.initial_score is not None and metrics.best_overall_score is not None:
        initial_display = round(metrics.initial_score * 100)
        best_display = round(metrics.best_overall_score * 100)
        improvement_display = best_display - initial_display
        sign = "+" if improvement_display >= 0 else ""
        score_range = f"{initial_display} → {best_display} ({sign}{improvement_display})"

    return {
        "total_iterations": metrics.total_iterations,
        "total_candidates": metrics.total_candidates,
        "score_range": score_range,
        "best_iteration": metrics.best_iteration,
        "best_candidate_iteration": best.iteration,
        "best_candidate_number": best.candidate_number,
        "best_score": (
            round(best.score * 100) if best.score is not None else None
        ),
        "primary_improvements": primary_improvements[:5],
        "successful_candidates": metrics.successful_candidates,
        "failed_candidates": metrics.failed_candidates,
    }


# ── Full Analytics Response ───────────────────────────────────────


def get_full_analytics(experiment_id: str) -> dict:
    """Get a complete analytics response for an experiment.

    Combines all analytics into a single response suitable for
    the dashboard API.

    Args:
        experiment_id: ID of the experiment.

    Returns:
        Dict with all analytics data.
    """
    metrics = calculate_experiment_metrics(experiment_id)
    iteration_metrics = calculate_iteration_metrics(experiment_id)
    score_prog = calculate_score_progression(experiment_id)
    qa_prog = calculate_metric_progression(experiment_id)
    param_impact = calculate_parameter_impact(experiment_id)
    best = get_best_results(experiment_id)
    strategy_stats = calculate_strategy_stats(experiment_id)
    summary = generate_experiment_summary(experiment_id)

    return {
        "experiment_id": experiment_id,
        "metrics": {
            "best_overall_score": metrics.best_overall_score,
            "initial_score": metrics.initial_score,
            "score_improvement": round(metrics.score_improvement, 6),
            "average_score": (
                round(metrics.average_score, 6)
                if metrics.average_score is not None
                else None
            ),
            "median_score": (
                round(metrics.median_score, 6)
                if metrics.median_score is not None
                else None
            ),
            "score_improvement_per_iteration": round(
                metrics.score_improvement_per_iteration, 6
            ),
            "best_iteration": metrics.best_iteration,
            "total_iterations": metrics.total_iterations,
            "total_candidates": metrics.total_candidates,
            "successful_candidates": metrics.successful_candidates,
            "failed_candidates": metrics.failed_candidates,
            "total_generation_time": round(metrics.total_generation_time, 2),
        },
        "score_progression": [
            {"iteration": e.iteration, "score": e.score} for e in score_prog
        ],
        "qa_progression": qa_prog,
        "iteration_metrics": [
            {
                "iteration": im.iteration,
                "score": im.score,
                "num_candidates": im.num_candidates,
                "best_candidate_score": im.best_candidate_score,
                "worst_candidate_score": im.worst_candidate_score,
                "average_candidate_score": im.average_candidate_score,
                "score_spread": round(im.score_spread, 6),
                "winning_candidate": im.winning_candidate,
                "winning_seed": im.winning_seed,
                "status": im.status,
            }
            for im in iteration_metrics
        ],
        "parameter_history": {
            param: [
                {
                    "parameter": pc.parameter,
                    "old_value": pc.old_value,
                    "new_value": pc.new_value,
                    "score_before": pc.score_before,
                    "score_after": pc.score_after,
                }
                for pc in changes
            ]
            for param, changes in param_impact.items()
        },
        "best_result": {
            "iteration": best.iteration,
            "candidate_number": best.candidate_number,
            "candidate_id": best.candidate_id,
            "score": best.score,
            "seed": best.seed,
            "output_video": best.output_video,
            "prompt": best.prompt,
            "negative_prompt": best.negative_prompt,
            "cfg": best.cfg,
            "noise": best.noise,
            "qa_report": best.qa_report,
        },
        "strategy_stats": [
            {
                "strategy": s.strategy,
                "iterations": s.iterations,
                "average_improvement": round(s.average_improvement, 6),
                "best_improvement": round(s.best_improvement, 6),
                "success_rate": round(s.success_rate, 4),
            }
            for s in strategy_stats
        ],
        "summary": summary,
    }