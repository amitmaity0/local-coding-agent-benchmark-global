"""Evaluator module for autonomous optimization loop decisions.

Determines whether the optimization loop should continue based on
stopping conditions: target score, max iterations, confidence threshold,
plateau detection, and user cancellation.

This logic is intentionally kept separate from the optimizer so that
the optimizer focuses on producing improvements while the evaluator
decides when to stop.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


class StoppingReason(str, enum.Enum):
    """Reasons the optimization loop stopped."""

    TARGET_SCORE_REACHED = "TARGET_SCORE_REACHED"
    MAX_ITERATIONS_REACHED = "MAX_ITERATIONS_REACHED"
    USER_CANCELLED = "USER_CANCELLED"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    NO_IMPROVEMENT = "NO_IMPROVEMENT"
    STEP_FAILURE = "STEP_FAILURE"


@dataclass
class EvaluationResult:
    """Result of evaluating a completed iteration."""

    should_continue: bool
    stopping_reason: Optional[StoppingReason] = None
    improvement: float = 0.0
    is_new_best: bool = False
    consecutive_no_improvement: int = 0


@dataclass
class EvaluationState:
    """Mutable state tracked across iterations for evaluation decisions."""

    best_score: Optional[float] = None
    best_iteration: int = 0
    consecutive_no_improvement: int = 0
    last_score: Optional[float] = None


def calculate_improvement(
    current_score: float,
    previous_best: Optional[float],
) -> float:
    """Calculate the score improvement relative to the best score so far.

    Args:
        current_score: Score of the current iteration.
        previous_best: Best score from previous iterations.

    Returns:
        Improvement delta (positive means improved).
    """
    if previous_best is None:
        return current_score
    return current_score - previous_best


def evaluate_iteration(
    *,
    iteration: int,
    score: float,
    confidence: float,
    target_score: float,
    max_iterations: int,
    cancelled: bool,
    confidence_threshold: float = 0.1,
    plateau_threshold: int = 3,
    improvement_epsilon: float = 0.001,
    state: Optional[EvaluationState] = None,
) -> EvaluationResult:
    """Evaluate whether to continue after a completed iteration.

    Checks all stopping conditions in priority order:
    1. User cancellation
    2. Target score reached
    3. Maximum iterations reached
    4. Low optimizer confidence
    5. Score plateau (no meaningful improvement for N iterations)

    Args:
        iteration: Current iteration number (1-based).
        score: QA score of the current iteration.
        confidence: Optimizer confidence for this iteration.
        target_score: Target quality score threshold.
        max_iterations: Maximum allowed iterations.
        cancelled: Whether the user requested cancellation.
        confidence_threshold: Minimum confidence to continue.
        plateau_threshold: Consecutive iterations without improvement before stopping.
        improvement_epsilon: Minimum improvement to count as meaningful.
        state: Persistent evaluation state (created automatically if None).

    Returns:
        EvaluationResult with decision and metadata.
    """
    if state is None:
        state = EvaluationState()

    # Initialize best on first iteration
    is_first = state.best_score is None
    if is_first:
        state.best_score = score
        state.best_iteration = iteration
        state.last_score = score
        logger.info(f"Eval iter={iteration}: first iteration, score={score:.3f}")

        # Even on first iteration, check cancellation and low confidence
        if cancelled:
            return EvaluationResult(
                should_continue=False,
                stopping_reason=StoppingReason.USER_CANCELLED,
                improvement=score,
                is_new_best=True,
                consecutive_no_improvement=0,
            )
        if confidence < confidence_threshold:
            return EvaluationResult(
                should_continue=False,
                stopping_reason=StoppingReason.LOW_CONFIDENCE,
                improvement=score,
                is_new_best=True,
                consecutive_no_improvement=0,
            )
        if iteration >= max_iterations:
            return EvaluationResult(
                should_continue=False,
                stopping_reason=StoppingReason.MAX_ITERATIONS_REACHED,
                improvement=score,
                is_new_best=True,
                consecutive_no_improvement=0,
            )
        return EvaluationResult(
            should_continue=True,
            stopping_reason=None,
            improvement=score,
            is_new_best=True,
            consecutive_no_improvement=0,
        )

    improvement = calculate_improvement(score, state.best_score)
    is_new_best = improvement > improvement_epsilon

    # Update best tracking
    if is_new_best:
        state.best_score = score
        state.best_iteration = iteration
        state.consecutive_no_improvement = 0
        logger.info(
            f"Eval iter={iteration}: new best score={score:.3f} "
            f"(prev={state.best_score:.3f})"
        )
    else:
        state.consecutive_no_improvement += 1
        logger.info(
            f"Eval iter={iteration}: score={score:.3f} "
            f"(no improvement, streak={state.consecutive_no_improvement})"
        )

    state.last_score = score

    # Check stopping conditions in priority order
    if cancelled:
        return EvaluationResult(
            should_continue=False,
            stopping_reason=StoppingReason.USER_CANCELLED,
            improvement=improvement,
            is_new_best=is_new_best,
            consecutive_no_improvement=state.consecutive_no_improvement,
        )

    if score >= target_score:
        logger.info(
            f"Eval iter={iteration}: target score {target_score} reached "
            f"with {score:.3f}"
        )
        return EvaluationResult(
            should_continue=False,
            stopping_reason=StoppingReason.TARGET_SCORE_REACHED,
            improvement=improvement,
            is_new_best=is_new_best,
            consecutive_no_improvement=state.consecutive_no_improvement,
        )

    if iteration >= max_iterations:
        logger.info(
            f"Eval iter={iteration}: max iterations {max_iterations} reached"
        )
        return EvaluationResult(
            should_continue=False,
            stopping_reason=StoppingReason.MAX_ITERATIONS_REACHED,
            improvement=improvement,
            is_new_best=is_new_best,
            consecutive_no_improvement=state.consecutive_no_improvement,
        )

    if confidence < confidence_threshold:
        logger.info(
            f"Eval iter={iteration}: confidence {confidence:.2f} below "
            f"threshold {confidence_threshold}"
        )
        return EvaluationResult(
            should_continue=False,
            stopping_reason=StoppingReason.LOW_CONFIDENCE,
            improvement=improvement,
            is_new_best=is_new_best,
            consecutive_no_improvement=state.consecutive_no_improvement,
        )

    if state.consecutive_no_improvement >= plateau_threshold:
        logger.info(
            f"Eval iter={iteration}: plateau detected after "
            f"{state.consecutive_no_improvement} iterations"
        )
        return EvaluationResult(
            should_continue=False,
            stopping_reason=StoppingReason.NO_IMPROVEMENT,
            improvement=improvement,
            is_new_best=is_new_best,
            consecutive_no_improvement=state.consecutive_no_improvement,
        )

    return EvaluationResult(
        should_continue=True,
        stopping_reason=None,
        improvement=improvement,
        is_new_best=is_new_best,
        consecutive_no_improvement=state.consecutive_no_improvement,
    )


def should_continue(
    *,
    iteration: int,
    score: float,
    confidence: float,
    target_score: float,
    max_iterations: int,
    cancelled: bool = False,
    confidence_threshold: float = 0.1,
    plateau_threshold: int = 3,
    improvement_epsilon: float = 0.001,
    state: Optional[EvaluationState] = None,
) -> bool:
    """Convenience wrapper: returns True if the loop should continue.

    Args:
        iteration: Current iteration number.
        score: QA score of the current iteration.
        confidence: Optimizer confidence.
        target_score: Target quality score.
        max_iterations: Maximum allowed iterations.
        cancelled: Whether the user requested cancellation.
        confidence_threshold: Minimum confidence to continue.
        plateau_threshold: Consecutive iterations without improvement.
        improvement_epsilon: Minimum improvement to count.
        state: Persistent evaluation state.

    Returns:
        True if another iteration should run.
    """
    result = evaluate_iteration(
        iteration=iteration,
        score=score,
        confidence=confidence,
        target_score=target_score,
        max_iterations=max_iterations,
        cancelled=cancelled,
        confidence_threshold=confidence_threshold,
        plateau_threshold=plateau_threshold,
        improvement_epsilon=improvement_epsilon,
        state=state,
    )
    return result.should_continue