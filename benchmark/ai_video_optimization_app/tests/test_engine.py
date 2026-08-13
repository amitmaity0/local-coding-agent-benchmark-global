"""Tests for the orchestration engine."""

import tempfile
from pathlib import Path

from orchestrator.config import AppConfig, DatabaseConfig
from orchestrator.engine import Engine
from orchestrator.models import ExperimentCreate
from orchestrator.state import ExperimentState


def _make_config() -> AppConfig:
    """Create a config with a temp SQLite database."""
    db_path = tempfile.mktemp(suffix=".db")
    return AppConfig(
        database=DatabaseConfig(url=f"sqlite:///{db_path}")
    )


def test_create_experiment() -> None:
    config = _make_config()
    engine = Engine(config)

    data = ExperimentCreate(prompt="A cat walking", max_iterations=5)
    exp = engine.create_experiment(data)

    assert exp.id is not None
    assert exp.prompt == "A cat walking"
    assert exp.status == ExperimentState.NEW
    assert exp.current_iteration == 0


def test_start_experiment() -> None:
    config = _make_config()
    engine = Engine(config)

    data = ExperimentCreate(prompt="Test")
    exp = engine.create_experiment(data)
    started = engine.start_experiment(exp.id)

    assert started.status == ExperimentState.QUEUED


def test_cancel_experiment() -> None:
    config = _make_config()
    engine = Engine(config)

    data = ExperimentCreate(prompt="Test")
    exp = engine.create_experiment(data)
    cancelled = engine.cancel_experiment(exp.id)

    assert cancelled.status == ExperimentState.CANCELLED


def test_get_status() -> None:
    config = _make_config()
    engine = Engine(config)

    data = ExperimentCreate(prompt="Test")
    exp = engine.create_experiment(data)
    status = engine.get_status(exp.id)

    assert status.id == exp.id
    assert status.status == ExperimentState.NEW


def test_list_experiments() -> None:
    config = _make_config()
    engine = Engine(config)

    engine.create_experiment(ExperimentCreate(prompt="A"))
    engine.create_experiment(ExperimentCreate(prompt="B"))

    experiments = engine.list_experiments()
    assert len(experiments) == 2


def test_get_status_not_found() -> None:
    config = _make_config()
    engine = Engine(config)

    try:
        engine.get_status("nonexistent-id")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass