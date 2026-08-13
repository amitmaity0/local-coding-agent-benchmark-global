"""Tests for WorkflowLoader."""

import json
import tempfile
from pathlib import Path

from orchestrator.exceptions import WorkflowLoadError, WorkflowValidationError
from services.workflow import WorkflowLoader


def _sample_workflow() -> dict:
    """Return a minimal sample ComfyUI workflow."""
    return {
        "1": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "old prompt", "clip": ["2", 0]},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "old negative", "clip": ["3", 0]},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
                "steps": 20,
                "cfg": 7.0,
                "model": ["4", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.safetensors"},
        },
    }


def test_load_workflow_from_disk() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wf = _sample_workflow()
        path = Path(tmp) / "test.json"
        with open(path, "w") as f:
            json.dump(wf, f)

        loader = WorkflowLoader(workflows_dir=tmp)
        loaded = loader.load("test")
        assert loaded == wf


def test_load_workflow_missing() -> None:
    loader = WorkflowLoader(workflows_dir="/tmp/nonexistent_dir_12345")
    try:
        loader.load("missing.json")
        assert False, "Should have raised WorkflowLoadError"
    except WorkflowLoadError:
        pass


def test_load_invalid_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.json"
        path.write_text("not json {{{")

        loader = WorkflowLoader(workflows_dir=tmp)
        try:
            loader.load("bad")
            assert False, "Should have raised WorkflowValidationError"
        except WorkflowValidationError:
            pass


def test_replace_parameters() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    result = loader.replace_parameters(
        wf,
        {"KSampler": {"cfg": 9.0, "steps": 30}},
    )
    assert result["3"]["inputs"]["cfg"] == 9.0
    assert result["3"]["inputs"]["steps"] == 30
    # Original unchanged
    assert wf["3"]["inputs"]["cfg"] == 7.0


def test_replace_by_id() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    result = loader.replace_by_id(wf, "1", {"text": "new text"})
    assert result["1"]["inputs"]["text"] == "new text"
    assert wf["1"]["inputs"]["text"] == "old prompt"


def test_set_prompt() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    result = loader.set_prompt(wf, "positive", "negative")
    assert result["1"]["inputs"]["text"] == "positive"
    assert result["2"]["inputs"]["text"] == "negative"


def test_set_seed() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    result = loader.set_seed(wf, 12345)
    assert result["3"]["inputs"]["seed"] == 12345


def test_set_cfg() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    result = loader.set_cfg(wf, 12.0)
    assert result["3"]["inputs"]["cfg"] == 12.0


def test_set_steps() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    result = loader.set_steps(wf, 50)
    assert result["3"]["inputs"]["steps"] == 50


def test_apply_config() -> None:
    wf = _sample_workflow()
    loader = WorkflowLoader()
    config = {
        "prompt": "a cat",
        "negative_prompt": "blurry",
        "seed": 999,
        "cfg": 8.5,
        "steps": 25,
    }
    result = loader.apply_config(wf, config)
    assert result["1"]["inputs"]["text"] == "a cat"
    assert result["2"]["inputs"]["text"] == "blurry"
    assert result["3"]["inputs"]["seed"] == 999
    assert result["3"]["inputs"]["cfg"] == 8.5
    assert result["3"]["inputs"]["steps"] == 25


def test_original_workflow_unchanged() -> None:
    """Ensure all methods return copies, not mutations."""
    wf = _sample_workflow()
    original = json.dumps(wf, sort_keys=True)
    loader = WorkflowLoader()

    loader.set_prompt(wf, "x")
    loader.set_seed(wf, 1)
    loader.set_cfg(wf, 1.0)
    loader.replace_parameters(wf, {"KSampler": {"steps": 1}})
    loader.replace_by_id(wf, "1", {"text": "z"})

    assert json.dumps(wf, sort_keys=True) == original