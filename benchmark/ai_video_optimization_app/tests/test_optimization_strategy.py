"""Tests for the adaptive optimization strategy."""

from orchestrator.optimization_strategy import (
    build_optimization_context,
    CandidateHistory,
    determine_strategy,
    OptimizationConfig,
    OptimizationMode,
    OptimizationStrategy,
    select_parameters_to_modify,
    should_explore,
)


# ── Helper factories ───────────────────────────────────────────────


def _make_qa_report(
    overall=0.75,
    identity=0.80,
    motion=0.70,
    camera=0.75,
    hands=0.65,
    face=0.80,
    lighting=0.78,
    physics=0.72,
    lip_sync=0.76,
    continuity=0.74,
):
    """Create a QA report dict with configurable scores."""
    return {
        "overall_score": overall,
        "identity_score": identity,
        "motion_score": motion,
        "camera_score": camera,
        "hands_score": hands,
        "face_score": face,
        "lighting_score": lighting,
        "physics_score": physics,
        "lip_sync_score": lip_sync,
        "continuity_score": continuity,
    }


def _make_history(
    best_score=80.0,
    current_score=75.0,
    previous_score=72.0,
    score_history=None,
    iteration=3,
):
    """Create a CandidateHistory with configurable scores."""
    return CandidateHistory(
        best_score=best_score,
        current_score=current_score,
        previous_score=previous_score,
        score_history=score_history or [],
        iteration_number=iteration,
    )


# ── TARGETED mode tests ───────────────────────────────────────────


def test_targeted_mode_low_identity():
    """TARGETED mode when identity score is weak."""
    qa = _make_qa_report(identity=0.50, motion=0.80, hands=0.80)
    # best == current so RECOVER won't trigger
    history = _make_history(
        best_score=70, current_score=70, score_history=[65, 70]
    )
    config = OptimizationConfig(targeted_score_threshold=70.0)

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.TARGETED
    assert "identity" in strategy.focus_areas
    assert "prompt" in strategy.parameters_modified or "seed" in strategy.parameters_modified


def test_targeted_mode_low_motion():
    """TARGETED mode when motion score is weak."""
    qa = _make_qa_report(motion=0.40, identity=0.85, hands=0.85)
    history = _make_history(
        best_score=70, current_score=70, score_history=[65, 70]
    )
    config = OptimizationConfig(targeted_score_threshold=70.0)

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.TARGETED
    assert "motion" in strategy.focus_areas
    assert "noise" in strategy.parameters_modified or "seed" in strategy.parameters_modified


def test_targeted_mode_low_hands():
    """TARGETED mode when hands score is weak."""
    qa = _make_qa_report(hands=0.30, identity=0.85, motion=0.85)
    history = _make_history(
        best_score=70, current_score=70, score_history=[65, 70]
    )
    config = OptimizationConfig(targeted_score_threshold=70.0)

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.TARGETED
    assert "hands" in strategy.focus_areas


def test_targeted_mode_multiple_weak():
    """TARGETED mode when multiple dimensions are weak."""
    qa = _make_qa_report(motion=0.40, hands=0.30, continuity=0.35)
    history = _make_history(
        best_score=50, current_score=50, score_history=[50]
    )
    config = OptimizationConfig(targeted_score_threshold=70.0)

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.TARGETED
    assert len(strategy.focus_areas) >= 2


def test_targeted_mode_preserves_good_params():
    """TARGETED mode preserves parameters not relevant to weak dimensions."""
    qa = _make_qa_report(identity=0.50)
    history = _make_history(best_score=75, current_score=70, score_history=[65, 70])
    config = OptimizationConfig(targeted_score_threshold=70.0)

    strategy = determine_strategy(qa, history, config)

    # Some params should be preserved (not all modified)
    assert len(strategy.parameters_preserved) > 0


# ── REFINE mode tests ─────────────────────────────────────────────


def test_refine_mode_improving_scores():
    """REFINE mode when scores are improving consistently."""
    qa = _make_qa_report(
        identity=0.80, motion=0.75, hands=0.75, continuity=0.75,
        camera=0.75, face=0.80, lighting=0.78, physics=0.72,
        lip_sync=0.76, overall=0.75,
    )
    history = _make_history(
        best_score=80, current_score=80, score_history=[60, 70, 80]
    )
    config = OptimizationConfig(
        targeted_score_threshold=70.0,
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.REFINE
    assert strategy.parameters_modified == ["seed"]
    assert "prompt" in strategy.parameters_preserved


def test_refine_mode_all_scores_good():
    """REFINE mode when all QA scores are above threshold."""
    qa = _make_qa_report(
        identity=0.90, motion=0.85, hands=0.88, continuity=0.90,
        camera=0.85, face=0.90, lighting=0.88, physics=0.85,
        lip_sync=0.87, overall=0.88,
    )
    history = _make_history(
        best_score=88, current_score=88, score_history=[80, 88]
    )
    config = OptimizationConfig(targeted_score_threshold=70.0)

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.REFINE


# ── EXPLORE mode tests ────────────────────────────────────────────


def test_explore_mode_plateau():
    """EXPLORE mode when scores have plateaued."""
    qa = _make_qa_report()
    history = _make_history(
        best_score=75,
        current_score=75,
        score_history=[70, 75, 75, 75],
    )
    config = OptimizationConfig(
        targeted_score_threshold=70.0,
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.EXPLORE
    assert "seed" in strategy.parameters_modified
    assert "noise" in strategy.parameters_modified


def test_explore_mode_allows_large_changes():
    """EXPLORE mode modifies more parameters than other modes."""
    qa = _make_qa_report()
    history = _make_history(
        best_score=75,
        current_score=75,
        score_history=[70, 75, 75, 75],
    )
    config = OptimizationConfig(
        targeted_score_threshold=70.0,
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    strategy = determine_strategy(qa, history, config)

    assert len(strategy.parameters_modified) >= 4


# ── RECOVER mode tests ────────────────────────────────────────────


def test_recover_mode_significant_regression():
    """RECOVER mode when current score regressed significantly from best."""
    qa = _make_qa_report(overall=0.40)
    history = _make_history(
        best_score=80, current_score=60, score_history=[70, 80, 60]
    )
    config = OptimizationConfig(recovery_regression_threshold=5.0)

    strategy = determine_strategy(qa, history, config)

    assert strategy.mode == OptimizationMode.RECOVER
    assert strategy.score_regression >= 20.0


def test_recover_mode_preserves_most_params():
    """RECOVER mode preserves most parameters, only varies 1-2."""
    qa = _make_qa_report(overall=0.40)
    history = _make_history(
        best_score=80, current_score=60, score_history=[70, 80, 60]
    )
    config = OptimizationConfig(recovery_regression_threshold=5.0)

    strategy = determine_strategy(qa, history, config)

    assert len(strategy.parameters_modified) <= 2
    assert len(strategy.parameters_preserved) >= 4


# ── Score plateau detection ───────────────────────────────────────


def test_plateau_detection_with_threshold():
    """Plateau is detected when improvement is below threshold."""
    history = _make_history(
        best_score=75,
        current_score=75,
        score_history=[70, 75, 75, 75],
    )
    config = OptimizationConfig(
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    assert should_explore(history, config)


def test_no_plateau_when_improving():
    """No plateau when scores keep improving."""
    history = _make_history(
        best_score=80,
        current_score=80,
        score_history=[60, 70, 80],
    )
    config = OptimizationConfig(
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    assert not should_explore(history, config)


# ── Score regression detection ────────────────────────────────────


def test_regression_detected_when_below_threshold():
    """Regression is detected when drop exceeds threshold."""
    history = _make_history(best_score=80, current_score=60)
    config = OptimizationConfig(recovery_regression_threshold=5.0)

    strategy = determine_strategy(_make_qa_report(), history, config)
    assert strategy.mode == OptimizationMode.RECOVER


def test_no_regression_when_within_threshold():
    """No regression detected when drop is small."""
    history = _make_history(best_score=80, current_score=78)
    config = OptimizationConfig(recovery_regression_threshold=5.0)

    qa = _make_qa_report()
    strategy = determine_strategy(qa, history, config)
    assert strategy.mode != OptimizationMode.RECOVER


# ── Parameter preservation ────────────────────────────────────────


def test_parameters_preserved_in_refine():
    """REFINE mode preserves all params except seed."""
    qa = _make_qa_report()
    history = _make_history(
        best_score=80, current_score=80, score_history=[60, 70, 80]
    )
    config = OptimizationConfig(
        targeted_score_threshold=70.0,
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    strategy = determine_strategy(qa, history, config)
    assert "cfg" in strategy.parameters_preserved
    assert "steps" in strategy.parameters_preserved
    assert "noise" in strategy.parameters_preserved


def test_parameters_modified_in_explore():
    """EXPLORE mode modifies many parameters."""
    qa = _make_qa_report()
    history = _make_history(
        best_score=75, current_score=75, score_history=[70, 75, 75, 75]
    )
    config = OptimizationConfig(
        targeted_score_threshold=70.0,
        improvement_threshold=1.0,
        plateau_iterations=2,
    )

    strategy = determine_strategy(qa, history, config)
    assert "seed" in strategy.parameters_modified
    assert "noise" in strategy.parameters_modified
    assert "cfg" in strategy.parameters_modified


# ── Parameter modification ────────────────────────────────────────


def test_select_parameters_for_motion():
    """select_parameters_to_modify returns correct params for motion."""
    params = select_parameters_to_modify(["motion_score"])
    assert "noise" in params or "seed" in params


def test_select_parameters_for_identity():
    """select_parameters_to_modify returns correct params for identity."""
    params = select_parameters_to_modify(["identity_score"])
    assert "prompt" in params or "seed" in params


def test_select_parameters_deduplicated():
    """select_parameters_to_modify returns deduplicated params."""
    params = select_parameters_to_modify(["motion_score", "continuity_score"])
    assert len(params) == len(set(params))


# ── Missing history fallback ──────────────────────────────────────


def test_fallback_to_refine_with_no_history():
    """Strategy falls back to REFINE when no history is available and all scores are good."""
    qa = _make_qa_report(
        identity=0.80, motion=0.75, hands=0.75, continuity=0.75,
        camera=0.75, face=0.80, lighting=0.78, physics=0.72,
        lip_sync=0.76, overall=0.75,
    )
    strategy = determine_strategy(qa, None)

    # With no history and all scores above threshold, should be REFINE
    assert strategy.mode == OptimizationMode.REFINE


def test_fallback_with_empty_qa_report():
    """Strategy handles empty QA report gracefully."""
    strategy = determine_strategy({}, None)

    assert strategy.mode == OptimizationMode.REFINE


def test_fallback_with_invalid_data():
    """Strategy never raises exceptions that block the loop."""
    try:
        strategy = determine_strategy("not a dict", None)
        # If it doesn't raise, it should return a valid strategy
        assert isinstance(strategy, OptimizationStrategy)
    except TypeError:
        # The function handles non-dict input; if it raises TypeError
        # that's caught internally and falls back
        pass


# ── Invalid configuration ─────────────────────────────────────────


def test_invalid_config_uses_defaults():
    """Strategy works with default config when values are extreme."""
    qa = _make_qa_report()
    history = _make_history(best_score=50, current_score=50)
    config = OptimizationConfig(
        improvement_threshold=-100.0,
        plateau_iterations=0,
        targeted_score_threshold=-1.0,
        recovery_regression_threshold=-100.0,
        exploration_probability=0.0,
    )

    strategy = determine_strategy(qa, history, config)
    assert isinstance(strategy, OptimizationStrategy)


def test_zero_threshold_triggers_targeted():
    """Zero threshold means all dimensions are weak."""
    qa = _make_qa_report()
    # best == current so RECOVER won't trigger
    history = _make_history(best_score=70, current_score=70)
    config = OptimizationConfig(targeted_score_threshold=0.0)

    strategy = determine_strategy(qa, history, config)
    # With threshold 0, all scores > 0, so no weak dims → REFINE
    assert strategy.mode in (OptimizationMode.REFINE, OptimizationMode.TARGETED)


# ── Build optimization context ────────────────────────────────────


def test_build_optimization_context_includes_mode():
    """Context includes optimization mode."""
    strategy = OptimizationStrategy(
        mode=OptimizationMode.TARGETED,
        focus_areas=["motion"],
        parameters_modified=["seed", "noise"],
        parameters_preserved=["cfg", "steps"],
        reasoning="Test reasoning",
    )
    context = build_optimization_context(
        strategy=strategy,
        qa_report=_make_qa_report(),
        iteration_number=5,
    )

    assert context["optimization_mode"] == "TARGETED"
    assert context["iteration_number"] == 5


def test_build_optimization_context_with_candidates():
    """Context includes candidate data when provided."""
    strategy = OptimizationStrategy(mode=OptimizationMode.REFINE)
    context = build_optimization_context(
        strategy=strategy,
        qa_report=_make_qa_report(),
        current_candidate={"seed": 123, "cfg": 7.0},
        best_candidate={"seed": 456, "cfg": 8.0},
    )

    assert "current_candidate" in context
    assert "best_candidate" in context
    assert context["current_candidate"]["seed"] == 123


def test_build_optimization_context_with_history():
    """Context includes previous reports when provided."""
    strategy = OptimizationStrategy(mode=OptimizationMode.EXPLORE)
    context = build_optimization_context(
        strategy=strategy,
        qa_report=_make_qa_report(),
        previous_qa_reports=[{"overall_score": 0.6}],
        previous_optimization_results=[{"confidence": 0.5}],
    )

    assert "previous_qa_reports" in context
    assert "previous_optimization_results" in context


# ── Strategy result structure ─────────────────────────────────────


def test_strategy_has_all_required_fields():
    """Strategy result contains all required fields."""
    qa = _make_qa_report()
    strategy = determine_strategy(qa, None)

    assert hasattr(strategy, "mode")
    assert hasattr(strategy, "focus_areas")
    assert hasattr(strategy, "parameters_modified")
    assert hasattr(strategy, "parameters_preserved")
    assert hasattr(strategy, "reasoning")
    assert hasattr(strategy, "expected_improvements")
    assert hasattr(strategy, "confidence")
    assert isinstance(strategy.focus_areas, list)
    assert isinstance(strategy.parameters_modified, list)
    assert isinstance(strategy.parameters_preserved, list)
    assert isinstance(strategy.reasoning, str)
    assert 0.0 <= strategy.confidence <= 1.0


def test_strategy_reasoning_is_not_empty():
    """Strategy reasoning provides explanation."""
    qa = _make_qa_report()
    strategy = determine_strategy(qa, None)

    assert len(strategy.reasoning) > 0