"""Web routes for MotionForge.

Defines all HTTP endpoints for the dashboard, experiment creation,
and experiment detail pages.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from loguru import logger

from orchestrator.models import ExperimentCreate
from orchestrator.state import ExperimentState


def _serialize_dt(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO strings for templates."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _to_dict(obj: Any) -> Any:
    """Convert Pydantic model to plain dict with serializable values."""
    if hasattr(obj, "model_dump"):
        data = obj.model_dump(mode="json")
        return data
    return obj

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the main dashboard page.

    Args:
        request: FastAPI request object.

    Returns:
        Rendered HTML dashboard.
    """
    engine = request.app.state.engine
    experiments = engine.list_experiments()

    status_counts = {s.value: 0 for s in ExperimentState}
    for exp in experiments:
        status_counts[exp.status.value] += 1

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "experiments": [exp.model_dump(mode="json") for exp in experiments],
            "total": len(experiments),
            "running": status_counts.get("GENERATING", 0)
            + status_counts.get("ANALYZING", 0)
            + status_counts.get("OPTIMIZING", 0),
            "completed": status_counts.get("COMPLETED", 0),
            "failed": status_counts.get("FAILED", 0),
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_experiment(request: Request) -> HTMLResponse:
    """Render the new experiment form page.

    Args:
        request: FastAPI request object.

    Returns:
        Rendered HTML form.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="new_experiment.html",
        context={},
    )


@router.post("/new", response_class=HTMLResponse)
async def create_experiment(
    request: Request,
    prompt: str = Form(...),
    negative_prompt: str = Form(default=""),
    workflow_template: str = Form(default=""),
    target_score: float = Form(default=0.8),
    max_iterations: int = Form(default=10),
    seed: int = Form(default=None),
    cfg: float = Form(default=7.0),
    noise: float = Form(default=0.1),
) -> RedirectResponse:
    """Handle new experiment form submission.

    Args:
        request: FastAPI request object.
        prompt: Generation prompt.
        negative_prompt: Negative prompt.
        workflow_template: Workflow template name.
        target_score: Target quality score.
        max_iterations: Maximum iterations.
        seed: Random seed.
        cfg: CFG scale.
        noise: Noise level.

    Returns:
        Redirect to the experiment detail page.
    """
    engine = request.app.state.engine
    data = ExperimentCreate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        workflow_template=workflow_template,
        target_score=target_score,
        max_iterations=max_iterations,
        seed=seed if seed else None,
        cfg=cfg,
        noise=noise,
    )
    experiment = engine.create_experiment(data)
    return RedirectResponse(
        url=f"/experiment/{experiment.id}", status_code=303
    )


@router.get("/experiment/{experiment_id}", response_class=HTMLResponse)
async def experiment_detail(
    request: Request, experiment_id: str
) -> HTMLResponse:
    """Render the experiment detail page.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        Rendered HTML detail page.
    """
    engine = request.app.state.engine
    experiment = engine.get_status(experiment_id)
    iterations = engine.get_iterations(experiment_id)

    # Load latest QA report if available
    qa_report = None
    for it in reversed(iterations):
        if it.report_path:
            try:
                import json

                with open(it.report_path) as f:
                    qa_report = json.load(f)
                break
            except (FileNotFoundError, json.JSONDecodeError):
                break

    # Load latest optimization result if available
    optimization = None
    for it in reversed(iterations):
        exp_dir = Path(it.report_path).parent if it.report_path else None
        if not exp_dir:
            continue
        opt_path = exp_dir / "optimization.json"
        if opt_path.exists():
            try:
                with open(opt_path) as f:
                    optimization = json.load(f)
                break
            except (FileNotFoundError, json.JSONDecodeError):
                break

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="experiment_detail.html",
        context={
            "experiment": experiment.model_dump(mode="json"),
            "iterations": [it.model_dump(mode="json") for it in iterations],
            "qa_report": qa_report,
            "optimization": optimization,
        },
    )


@router.get("/api/experiment/{experiment_id}/status")
async def experiment_status_api(request: Request, experiment_id: str) -> dict:
    """API endpoint for HTMX polling of experiment status.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        JSON status object.
    """
    engine = request.app.state.engine
    experiment = engine.get_status(experiment_id)
    return {
        "id": experiment.id,
        "status": experiment.status.value,
        "current_iteration": experiment.current_iteration,
        "score": experiment.score,
        "max_iterations": experiment.max_iterations,
        "best_score": experiment.best_score,
        "best_iteration": experiment.best_iteration,
        "target_score": experiment.target_score,
        "stopping_reason": experiment.stopping_reason,
        "optimizer_confidence": experiment.optimizer_confidence,
    }


@router.post("/experiment/{experiment_id}/cancel")
async def cancel_experiment_api(
    request: Request, experiment_id: str
) -> RedirectResponse:
    """Cancel a running experiment.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment to cancel.

    Returns:
        Redirect back to experiment detail page.
    """
    engine = request.app.state.engine
    engine.cancel_experiment(experiment_id)
    return RedirectResponse(url=f"/experiment/{experiment_id}", status_code=303)


@router.post("/experiment/{experiment_id}/start")
async def start_experiment_loop(
    request: Request, experiment_id: str
) -> RedirectResponse:
    """Start the autonomous optimization loop in a background thread.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment to start.

    Returns:
        Redirect back to experiment detail page.
    """
    import threading

    engine = request.app.state.engine
    engine.start_experiment(experiment_id)

    def _run():
        try:
            engine.run_loop(experiment_id)
        except Exception as exc:
            logger.error(f"Background loop error for {experiment_id}: {exc}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return RedirectResponse(url=f"/experiment/{experiment_id}", status_code=303)


@router.get("/api/experiment/{experiment_id}/progress")
async def experiment_progress_api(
    request: Request, experiment_id: str
) -> dict:
    """API endpoint for detailed progress data.

    Returns score history, best result tracking, and estimated
    remaining iterations for the dashboard chart and progress bar.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        JSON progress object.
    """
    engine = request.app.state.engine
    return engine.get_progress(experiment_id)


@router.get("/api/experiment/{experiment_id}/timeline")
async def experiment_timeline_api(request: Request, experiment_id: str) -> list[dict]:
    """API endpoint for experiment timeline events.

    Returns a list of timeline events (generation, analysis, optimization)
    for each completed iteration, plus the current activity.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        List of timeline event dicts.
    """
    engine = request.app.state.engine
    iterations = engine.get_iterations(experiment_id)
    experiment = engine.get_status(experiment_id)

    timeline: list[dict] = []
    for it in iterations:
        timeline.append(
            {
                "iteration": it.number,
                "events": [],
            }
        )
        timeline[-1]["events"].append(
            {
                "type": "generated",
                "status": "done",
                "time": it.created_at.isoformat() if it.created_at else None,
            }
        )
        if it.report_path:
            timeline[-1]["events"].append(
                {
                    "type": "qa_complete",
                    "status": "done",
                    "score": it.score,
                }
            )
        # Check if optimization file exists
        if it.report_path:
            import json as _json

            from pathlib import Path as _Path

            opt_path = _Path(it.report_path).parent / "optimization.json"
            if opt_path.exists():
                try:
                    with open(opt_path) as f:
                        _json.load(f)
                    timeline[-1]["events"].append(
                        {"type": "optimization_complete", "status": "done"}
                    )
                except (FileNotFoundError, json.JSONDecodeError):
                    pass

    # Add current activity for running experiments
    if experiment.status.value in (
        "GENERATING",
        "ANALYZING",
        "OPTIMIZING",
    ):
        current_iter = experiment.current_iteration
        # Check if we already have an entry for this iteration
        has_current = any(
            t["iteration"] == current_iter for t in timeline
        )
        if not has_current:
            timeline.append(
                {
                    "iteration": current_iter,
                    "events": [],
                }
            )

        activity_map = {
            "GENERATING": "generating",
            "ANALYZING": "analyzing",
            "OPTIMIZING": "optimizing",
        }
        activity = activity_map.get(experiment.status.value, "running")
        timeline[-1]["events"].append(
            {
                "type": activity,
                "status": "in_progress",
            }
        )

    return timeline


# ── Analytics API Endpoints ───────────────────────────────────────


@router.get("/api/experiments/{experiment_id}/analytics")
async def experiment_analytics_api(
    request: Request, experiment_id: str
) -> dict:
    """Get full analytics for an experiment.

    Returns all analytics data including metrics, score progression,
    QA progression, candidate analytics, parameter history, strategy stats,
    best result, and summary.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        Complete analytics response.
    """
    from orchestrator.analytics import get_full_analytics

    return get_full_analytics(experiment_id)


@router.get("/api/experiments/{experiment_id}/metrics")
async def experiment_metrics_api(
    request: Request, experiment_id: str
) -> dict:
    """Get experiment-level metrics.

    Returns aggregated metrics like best score, average score,
    improvement, total iterations, and candidate counts.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        Experiment metrics dict.
    """
    from orchestrator.analytics import (
        calculate_experiment_metrics,
        generate_experiment_summary,
    )

    metrics = calculate_experiment_metrics(experiment_id)
    summary = generate_experiment_summary(experiment_id)

    return {
        "experiment_id": experiment_id,
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
        "summary": summary,
    }


@router.get("/api/experiments/{experiment_id}/score-history")
async def experiment_score_history_api(
    request: Request, experiment_id: str
) -> list[dict]:
    """Get score progression across iterations.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        List of {iteration, score} dicts.
    """
    from orchestrator.analytics import calculate_score_progression

    entries = calculate_score_progression(experiment_id)
    return [
        {"iteration": e.iteration, "score": e.score} for e in entries
    ]


@router.get("/api/experiments/{experiment_id}/qa-history")
async def experiment_qa_history_api(
    request: Request, experiment_id: str
) -> dict:
    """Get QA metric progression across iterations.

    Returns per-dimension progression (identity, motion, camera,
    hands, face, lighting, physics, lip_sync, continuity).

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        Dict mapping metric name to list of {iteration, value} dicts.
    """
    from orchestrator.analytics import calculate_metric_progression

    return calculate_metric_progression(experiment_id)


@router.get("/api/experiments/{experiment_id}/candidates/analytics")
async def candidates_analytics_api(
    request: Request, experiment_id: str
) -> dict:
    """Get per-iteration candidate analytics.

    Returns candidate statistics per iteration including
    best/worst/average scores, score spread, and winning candidate.

    Args:
        request: FastAPI request object.
        experiment_id: ID of the experiment.

    Returns:
        Dict with iteration_metrics, best_result, and strategy_stats.
    """
    from orchestrator.analytics import (
        calculate_iteration_metrics,
        calculate_strategy_stats,
        get_best_results,
    )

    iteration_metrics = calculate_iteration_metrics(experiment_id)
    best = get_best_results(experiment_id)
    strategy_stats = calculate_strategy_stats(experiment_id)

    return {
        "experiment_id": experiment_id,
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
    }


@router.get("/experiments/{experiment_id}/candidates", response_class=HTMLResponse)
async def experiment_candidates(
    request: Request, experiment_id: str
) -> HTMLResponse:
    """Show candidates for all iterations."""
    engine = request.app.state.engine
    templates = request.app.state.templates
    iterations = engine.get_iterations(experiment_id)
    all_candidates = []
    for it in iterations:
        cands = engine.get_candidates(experiment_id, it.iteration)
        all_candidates.extend(cands)

    return templates.TemplateResponse(
        request=request,
        name="experiment_candidates.html",
        context={
            "experiment_id": experiment_id,
            "iterations": [it.model_dump(mode="json") for it in iterations],
            "candidates": [c.model_dump(mode="json") for c in all_candidates],
        },
    )


@router.get("/experiments/{experiment_id}/iteration/{iteration}/candidates", response_class=HTMLResponse)
async def iteration_candidates(
    request: Request, experiment_id: str, iteration: int
) -> HTMLResponse:
    """Show candidates for a specific iteration."""
    engine = request.app.state.engine
    templates = request.app.state.templates
    candidates = engine.get_candidates(experiment_id, iteration)
    return templates.TemplateResponse(
        request=request,
        name="iteration_candidates.html",
        context={
            "experiment_id": experiment_id,
            "iteration": iteration,
            "candidates": [c.model_dump(mode="json") for c in candidates],
        },
    )


@router.get("/api/experiments/{experiment_id}/iteration/{iteration}/candidates")
async def api_iteration_candidates(
    request: Request, experiment_id: str, iteration: int
) -> JSONResponse:
    """API: Get candidates for a specific iteration."""
    engine = request.app.state.engine
    candidates = engine.get_candidates(experiment_id, iteration)
    return JSONResponse(
        [c.model_dump(mode="json") for c in candidates]
    )