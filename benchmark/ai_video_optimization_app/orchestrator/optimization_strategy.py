"""Adaptive optimization strategy for MotionForge.

Determines WHAT to change based on QA results and candidate history
instead of always modifying all parameters.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from loguru import logger


class OptimizationMode(str, Enum):
    """Optimization modes that determine strategy behaviour."""

    TARGETED = "TARGETED"
    """Focus on specific weak metrics identified by QA."""

    REFINE = "REFINE"
    """Score is improving; make smaller, more careful changes."""

    EXPLORE = "EXPLORE"
    """Progress stalled; allow larger changes to escape local optima."""

    RECOVER = "RECOVER"
    """Current iteration regressed significantly; return toward best-known."""


# Mapping from QA dimension scores to the generation parameters
# most likely to influence them.
_DIMENSION_PARAMS: dict[str, list[str]] = {
    "identity": ["prompt", "seed", "cfg"],
    "motion": ["noise", "seed", "steps"],
    "camera": ["prompt", "noise", "seed"],
    "hands": ["prompt", "negative_prompt", "seed"],
    "face": ["prompt", "negative_prompt", "seed"],
    "lighting": ["prompt", "cfg", "noise"],
    "physics": ["noise", "steps", "seed"],
    "lip_sync": ["prompt", "steps", "seed"],
    "continuity": ["noise", "seed", "steps"],
}

# All generation parameters the optimizer may touch.
_ALL_PARAMS = [
    "prompt",
    "negative_prompt",
    "seed",
    "cfg",
    "noise",
    "steps",
]


@dataclass
class OptimizationConfig:
    """Configuration for optimization strategy thresholds.

    Loaded from YAML; never hardcoded.
    """

    # Minimum score improvement to count as meaningful progress.
    improvement_threshold: float = 1.0

    # Number of iterations without meaningful improvement before
    # triggering EXPLORE mode.
    plateau_iterations: int = 2

    # Scores below this threshold are considered "weak" for a given
    # dimension, triggering TARGETED mode.
    targeted_score_threshold: float = 70.0

    # How much worse the current score must be compared to the best
    # to trigger RECOVER mode.
    recovery_regression_threshold: float = 5.0

    # Probability of forcing EXPLORE even when another mode applies.
    exploration_probability: float = 0.25


@dataclass
class CandidateHistory:
    """Summary of candidate/iteration history for strategy decisions."""

    best_score: float
    current_score: float
    previous_score: Optional[float]
    score_history: list[float] = field(default_factory=list)
    iteration_number: int = 0


@dataclass
class OptimizationStrategy:
    """Structured decision describing what the optimizer should focus on."""

    mode: OptimizationMode
    focus_areas: list[str] = field(default_factory=list)
    parameters_modified: list[str] = field(default_factory=list)
    parameters_preserved: list[str] = field(default_factory=list)
    reasoning: str = ""
    expected_improvements: list[str] = field(default_factory=list)
    confidence: float = 0.5
    score_improvement: float = 0.0
    score_regression: float = 0.0


def determine_strategy(
    qa_report: dict,
    candidate_history: Optional[CandidateHistory],
    config: OptimizationConfig = OptimizationConfig(),
) -> OptimizationStrategy:
    """Determine the optimization strategy based on QA results and history.

    Evaluates QA scores against thresholds and candidate history to decide
    which optimization mode to use and which parameters to modify.

    Args:
        qa_report: QA report dict with dimension scores (keys like
            'identity_score', 'motion_score', etc.) and 'overall_score'.
        candidate_history: Historical score data. May be None if no
            history is available.
        config: Strategy configuration thresholds.

    Returns:
        OptimizationStrategy with mode, focus areas, and parameter decisions.

    Note:
        Never raises exceptions that would block the optimization loop.
        Falls back to REFINE on any unexpected input.
    """
    try:
        return _determine_strategy_internal(qa_report, candidate_history, config)
    except Exception as exc:
        logger.warning(
            f"Strategy determination failed ({exc}); falling back to REFINE"
        )
        return _fallback_refine(qa_report)


def _determine_strategy_internal(
    qa_report: dict,
    candidate_history: Optional[CandidateHistory],
    config: OptimizationConfig,
) -> OptimizationStrategy:
    """Internal strategy determination — may raise on bad input."""

    # 1. Check for RECOVER: significant regression from best
    if candidate_history and _is_regression(
        candidate_history, config.recovery_regression_threshold
    ):
        return _build_recover_strategy(qa_report, candidate_history, config)

    # 2. Check for EXPLORE: plateau or random exploration
    if _should_explore(candidate_history, config):
        return _build_explore_strategy(qa_report, config)

    # 3. Check for TARGETED: one or more weak dimensions
    weak_dims = _find_weak_dimensions(qa_report, config.targeted_score_threshold)
    if weak_dims:
        return _build_targeted_strategy(
            qa_report, weak_dims, candidate_history, config
        )

    # 4. Default to REFINE
    return _build_refine_strategy(qa_report, candidate_history, config)


# ── Mode builders ──────────────────────────────────────────────────


def _build_targeted_strategy(
    qa_report: dict,
    weak_dims: list[str],
    history: Optional[CandidateHistory],
    config: OptimizationConfig,
) -> OptimizationStrategy:
    """Build a TARGETED strategy focusing on specific weak dimensions."""
    params_to_modify = select_parameters_to_modify(weak_dims)
    params_preserved = [p for p in _ALL_PARAMS if p not in params_to_modify]

    focus_labels = [d.replace("_score", "").replace("_", " ") for d in weak_dims]
    reasoning = (
        f"Current QA indicates weak {', '.join(focus_labels)}. "
        f"Focusing optimization on parameters that influence these areas."
    )

    improvements = [
        f"Improve {dim.replace('_score', '')} quality" for dim in weak_dims
    ]

    return OptimizationStrategy(
        mode=OptimizationMode.TARGETED,
        focus_areas=focus_labels,
        parameters_modified=params_to_modify,
        parameters_preserved=params_preserved,
        reasoning=reasoning,
        expected_improvements=improvements,
        confidence=0.7,
    )


def _build_refine_strategy(
    qa_report: dict,
    history: Optional[CandidateHistory],
    config: OptimizationConfig,
) -> OptimizationStrategy:
    """Build a REFINE strategy for steady improvement."""
    # In refine mode, only change seed and make small adjustments.
    params_to_modify = ["seed"]
    params_preserved = [p for p in _ALL_PARAMS if p != "seed"]

    reasoning = (
        "Score is improving consistently. Making minimal changes to "
        "preserve what is working while exploring slight variations."
    )

    return OptimizationStrategy(
        mode=OptimizationMode.REFINE,
        focus_areas=[],
        parameters_modified=params_to_modify,
        parameters_preserved=params_preserved,
        reasoning=reasoning,
        expected_improvements=["Continued incremental improvement"],
        confidence=0.6,
    )


def _build_explore_strategy(
    qa_report: dict,
    config: OptimizationConfig,
) -> OptimizationStrategy:
    """Build an EXPLORE strategy to escape local optima."""
    params_to_modify = ["seed", "noise", "cfg", "steps", "prompt"]
    params_preserved = [p for p in _ALL_PARAMS if p not in params_to_modify]

    reasoning = (
        "Progress has stalled. Exploring broader parameter space to "
        "escape local optimum. Allowing larger changes to seed, noise, "
        "CFG, steps, and prompt."
    )

    return OptimizationStrategy(
        mode=OptimizationMode.EXPLORE,
        focus_areas=["exploration"],
        parameters_modified=params_to_modify,
        parameters_preserved=params_preserved,
        reasoning=reasoning,
        expected_improvements=[
            "Break out of local optimum",
            "Discover new high-quality configurations",
        ],
        confidence=0.4,
    )


def _build_recover_strategy(
    qa_report: dict,
    history: CandidateHistory,
    config: OptimizationConfig,
) -> OptimizationStrategy:
    """Build a RECOVER strategy to return toward best-known configuration."""
    # Prefer returning to best-known params; only vary 1-2.
    params_to_modify = ["seed", "noise"]
    params_preserved = [p for p in _ALL_PARAMS if p not in params_to_modify]

    regression = history.best_score - history.current_score
    reasoning = (
        f"Current iteration regressed by {regression:.1f} points from best. "
        f"Returning toward best-known configuration with minor exploration."
    )

    return OptimizationStrategy(
        mode=OptimizationMode.RECOVER,
        focus_areas=["recovery"],
        parameters_modified=params_to_modify,
        parameters_preserved=params_preserved,
        reasoning=reasoning,
        expected_improvements=[
            "Return to quality level of best-known configuration",
        ],
        confidence=0.5,
        score_regression=regression,
    )


def _fallback_refine(qa_report: dict) -> OptimizationStrategy:
    """Safe fallback: REFINE with minimal changes."""
    return OptimizationStrategy(
        mode=OptimizationMode.REFINE,
        focus_areas=[],
        parameters_modified=["seed"],
        parameters_preserved=["prompt", "negative_prompt", "cfg", "noise", "steps"],
        reasoning="Strategy fallback: using REFINE mode with minimal changes.",
        expected_improvements=["Maintain current quality level"],
        confidence=0.5,
    )


# ── Analysis helpers ───────────────────────────────────────────────


def _find_weak_dimensions(
    qa_report: dict, threshold: float
) -> list[str]:
    """Find QA dimensions whose scores fall below the threshold.

    Args:
        qa_report: QA report dict.
        threshold: Score threshold (0-100 scale).

    Returns:
        List of dimension names (e.g. ['motion_score', 'hands_score']).
    """
    dimension_keys = [
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
    weak = []
    for key in dimension_keys:
        val = qa_report.get(key)
        if val is not None:
            # Handle both 0-1 and 0-100 scale scores
            score = val * 100 if val <= 1.0 else val
            if score < threshold:
                weak.append(key)
    return weak


def _is_regression(
    history: CandidateHistory, threshold: float
) -> bool:
    """Check if current score regressed significantly from best."""
    if history.current_score is None or history.best_score is None:
        return False
    return (history.best_score - history.current_score) >= threshold


def _has_plateaued(
    history: Optional[CandidateHistory], config: OptimizationConfig
) -> bool:
    """Check if scores have plateaued for the configured number of iterations."""
    if not history or len(history.score_history) < config.plateau_iterations + 1:
        return False

    recent = history.score_history[-config.plateau_iterations :]
    for i in range(1, len(recent)):
        improvement = recent[i] - recent[i - 1]
        if improvement >= config.improvement_threshold:
            return False
    return True


def should_explore(
    history: Optional[CandidateHistory],
    config: OptimizationConfig = OptimizationConfig(),
) -> bool:
    """Determine whether to trigger exploration mode.

    Exploration is triggered when:
    - Scores have plateaued for the configured number of iterations, OR
    - Random exploration probability fires.

    Args:
        history: Candidate history.
        config: Optimization configuration.

    Returns:
        True if exploration should be triggered.
    """
    if _has_plateaued(history, config):
        return True
    if random.random() < config.exploration_probability:
        return True
    return False


def _should_explore(
    history: Optional[CandidateHistory],
    config: OptimizationConfig,
) -> bool:
    """Internal exploration check (deterministic plateau only, no random).

    The random exploration probability is applied in the public
    `should_explore` function; here we only check plateau.
    """
    return _has_plateaued(history, config)


# ── Parameter selection ────────────────────────────────────────────


def select_parameters_to_modify(
    weak_dimensions: list[str],
) -> list[str]:
    """Select generation parameters to modify based on weak QA dimensions.

    Uses a mapping from QA dimensions to the parameters most likely
    to influence them.

    Args:
        weak_dimensions: List of weak dimension names
            (e.g. ['motion_score', 'hands_score']).

    Returns:
        Deduplicated list of parameter names to modify.
    """
    params: set[str] = set()
    for dim in weak_dimensions:
        clean_dim = dim.replace("_score", "")
        for param in _DIMENSION_PARAMS.get(clean_dim, ["seed"]):
            params.add(param)
    return sorted(params)


# ── Context builder ────────────────────────────────────────────────


def build_optimization_context(
    strategy: OptimizationStrategy,
    qa_report: dict,
    current_candidate: Optional[dict] = None,
    best_candidate: Optional[dict] = None,
    previous_qa_reports: Optional[list[dict]] = None,
    previous_optimization_results: Optional[list[dict]] = None,
    iteration_number: int = 1,
) -> dict:
    """Build the full optimization context for the optimizer service.

    The context includes everything the optimizer needs to make informed
    decisions: strategy, QA data, candidate history, and iteration number.

    Args:
        strategy: The determined optimization strategy.
        qa_report: Current QA report dict.
        current_candidate: Current candidate data (optional).
        best_candidate: Best candidate data (optional).
        previous_qa_reports: List of previous QA reports (optional).
        previous_optimization_results: List of previous optimization
            results (optional).
        iteration_number: Current iteration number.

    Returns:
        Dict containing the full optimization context.
    """
    context: dict = {
        "optimization_mode": strategy.mode.value,
        "focus_areas": strategy.focus_areas,
        "parameters_modified": strategy.parameters_modified,
        "parameters_preserved": strategy.parameters_preserved,
        "strategy_reasoning": strategy.reasoning,
        "iteration_number": iteration_number,
        "qa_report": qa_report,
    }

    if current_candidate:
        context["current_candidate"] = current_candidate
    if best_candidate:
        context["best_candidate"] = best_candidate
    if previous_qa_reports:
        context["previous_qa_reports"] = previous_qa_reports
    if previous_optimization_results:
        context["previous_optimization_results"] = previous_optimization_results

    return context