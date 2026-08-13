"""Tests for the state machine."""

from orchestrator.state import ExperimentState, can_transition, transition


def test_valid_transitions() -> None:
    assert can_transition(ExperimentState.NEW, ExperimentState.QUEUED)
    assert can_transition(ExperimentState.QUEUED, ExperimentState.GENERATING)
    assert can_transition(ExperimentState.GENERATING, ExperimentState.ANALYZING)
    assert can_transition(ExperimentState.ANALYZING, ExperimentState.OPTIMIZING)
    assert can_transition(ExperimentState.OPTIMIZING, ExperimentState.GENERATING)
    assert can_transition(ExperimentState.ANALYZING, ExperimentState.COMPLETED)


def test_invalid_transitions() -> None:
    assert not can_transition(ExperimentState.NEW, ExperimentState.COMPLETED)
    assert not can_transition(ExperimentState.COMPLETED, ExperimentState.GENERATING)
    assert not can_transition(ExperimentState.FAILED, ExperimentState.GENERATING)


def test_terminal_states() -> None:
    for terminal in (ExperimentState.COMPLETED, ExperimentState.FAILED, ExperimentState.CANCELLED):
        for state in ExperimentState:
            if state != terminal:
                assert not can_transition(terminal, state)


def test_cancel_from_any_non_terminal() -> None:
    for state in (
        ExperimentState.NEW,
        ExperimentState.QUEUED,
        ExperimentState.GENERATING,
        ExperimentState.ANALYZING,
        ExperimentState.OPTIMIZING,
    ):
        assert can_transition(state, ExperimentState.CANCELLED)


def test_transition_raises_on_invalid() -> None:
    try:
        transition(ExperimentState.NEW, ExperimentState.COMPLETED)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_transition_succeeds_on_valid() -> None:
    result = transition(ExperimentState.NEW, ExperimentState.QUEUED)
    assert result == ExperimentState.QUEUED