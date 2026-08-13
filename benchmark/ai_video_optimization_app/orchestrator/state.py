"""State machine for experiment lifecycle management.

Defines valid states and transitions for experiments.
"""

from __future__ import annotations

import enum
from typing import Final

from loguru import logger


class ExperimentState(str, enum.Enum):
    """Valid states for an experiment."""

    NEW = "NEW"
    QUEUED = "QUEUED"
    GENERATING = "GENERATING"
    ANALYZING = "ANALYZING"
    OPTIMIZING = "OPTIMIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# Valid transitions: current_state -> set of allowed next states
_VALID_TRANSITIONS: Final = {
    ExperimentState.NEW: {ExperimentState.QUEUED, ExperimentState.CANCELLED},
    ExperimentState.QUEUED: {ExperimentState.GENERATING, ExperimentState.CANCELLED},
    ExperimentState.GENERATING: {
        ExperimentState.ANALYZING,
        ExperimentState.FAILED,
        ExperimentState.CANCELLED,
    },
    ExperimentState.ANALYZING: {
        ExperimentState.OPTIMIZING,
        ExperimentState.COMPLETED,
        ExperimentState.FAILED,
        ExperimentState.CANCELLED,
    },
    ExperimentState.OPTIMIZING: {
        ExperimentState.GENERATING,
        ExperimentState.COMPLETED,
        ExperimentState.FAILED,
        ExperimentState.CANCELLED,
    },
    ExperimentState.COMPLETED: set(),
    ExperimentState.FAILED: set(),
    ExperimentState.CANCELLED: set(),
}


def can_transition(from_state: ExperimentState, to_state: ExperimentState) -> bool:
    """Check if a state transition is valid.

    Args:
        from_state: Current state.
        to_state: Desired next state.

    Returns:
        True if the transition is allowed.
    """
    return to_state in _VALID_TRANSITIONS.get(from_state, set())


def transition(current: ExperimentState, next_state: ExperimentState) -> ExperimentState:
    """Perform a state transition, validating it first.

    Args:
        current: Current state.
        next_state: Desired next state.

    Returns:
        The new state.

    Raises:
        ValueError: If the transition is not allowed.
    """
    if not can_transition(current, next_state):
        raise ValueError(
            f"Invalid transition: {current.value} -> {next_state.value}"
        )
    logger.debug(f"State transition: {current.value} -> {next_state.value}")
    return next_state