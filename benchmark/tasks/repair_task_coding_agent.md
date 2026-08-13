Task: Harden and complete the autonomous optimization loop

Repository:
- /workspace/ai_video_optimization_app

Context:
The autonomous generate → analyze → optimize → apply → next iteration loop has now been implemented in orchestrator/engine.py.

Before allowing unattended experiments, perform a focused correctness review and fix the following issues.

IMPORTANT:
Do not redesign the autonomous-loop architecture.
Do not rewrite working components unnecessarily.
Preserve the existing single-cycle behavior.
Preserve the workflow-sidecar architecture.
Do not modify LTX2.3-Basic-API.json.
Do not introduce workflow-specific if/elif logic.
Use the existing OptimizationResult, optimization strategy, persistence, and state models wherever possible.

============================================================
1. Verify/fix OptimizationResult.steps actually reaches ComfyUI
============================================================

This is the highest-priority issue.

The optimizer can return:

    new_steps

and _apply_optimization_result() currently applies it to the ExperimentORM.

However, verify that the generation path actually takes:

    Experiment.steps

and maps it into the selected ComfyUI workflow.

The autonomous loop must behave like:

    Iteration 1:
        steps = 30
          ↓
        generate with 30 steps
          ↓
        QA
          ↓
        optimizer returns new_steps = 45
          ↓
        apply OptimizationResult
          ↓
    Iteration 2:
        steps = 45
          ↓
        ComfyUI MUST actually receive 45

Do not merely store the new value in the database.

Inspect:

- orchestrator/engine.py
- services/workflow.py
- workflow sidecar implementation
- ExperimentORM.steps
- WorkflowLoader.set_steps()
- LTX2.3-Basic-API.yaml

If set_steps() already exists, ensure Engine.generate() calls it.

The sidecar must support the steps mapping required by a workflow.

For LTX2.3, inspect the actual JSON workflow and determine the correct node/input for the step count.

Do NOT guess the node ID.

Do NOT hardcode the LTX node ID into Python.

If the LTX sidecar needs a steps mapping, add it to:

    workflows/LTX2.3-Basic-API.yaml

using the existing sidecar schema.

Add a regression test that proves:

    Experiment.steps = 45

results in the generated workflow containing the correct step value.

Also test:

    OptimizationResult.new_steps = 45

→ _apply_optimization_result()
→ Experiment.steps = 45
→ next generation uses 45.

============================================================
2. Verify all optimized parameters are actually applied to the next workflow
============================================================

For the autonomous loop, verify this complete chain:

    OptimizationResult
        ↓
    _apply_optimization_result()
        ↓
    ExperimentORM
        ↓
    next Engine.generate()
        ↓
    WorkflowLoader
        ↓
    ComfyUI workflow JSON

Verify at minimum:

    new_prompt
    new_negative_prompt
    new_seed
    new_cfg
    new_noise
    new_steps

For parameters marked unsupported by the sidecar:

    DO NOT APPLY

For LTX2.3 specifically:

    prompt           → 121.text
    negative_prompt  → 110.text
    seed             → 114.noise_seed
                       115.noise_seed
    cfg               → 103.cfg
                       129.cfg
    noise             → unsupported / unchanged
    steps             → actual LTX step input

Use the actual workflow JSON to verify the steps mapping.

Add an integration-style test that starts with known experiment values, applies a known OptimizationResult, generates the workflow without contacting ComfyUI, and verifies the resulting workflow inputs.

============================================================
3. Verify candidate semantics
============================================================

Inspect the existing:

    generation.candidates_per_iteration
    generation.parallel_generation

configuration and candidate models.

Current default configuration:

    candidates_per_iteration: 3
    parallel_generation: false

Determine how candidates are intended to work in the existing architecture.

Do NOT invent a new candidate architecture.

Determine whether the intended autonomous semantics are:

Option A:

    Iteration 1
       ├── Candidate 1
       ├── Candidate 2
       └── Candidate 3
              ↓
          evaluate/rank
              ↓
          optimize
              ↓
    Iteration 2

or whether the current implementation intentionally treats each generation as one candidate/iteration.

Use the existing code and documentation to determine the intended behavior.

If candidate generation is already implemented elsewhere, integrate run_loop() with that existing implementation.

If candidates are NOT yet implemented in the single-cycle/autonomous path, do NOT attempt a large candidate-generation redesign in this task.

Instead:

- preserve the current behavior
- explicitly document the current semantics
- add a test ensuring the loop does not accidentally create 3 autonomous iterations merely because candidates_per_iteration=3.

The task must leave the application behavior internally consistent.

============================================================
4. Verify background execution from the Web UI
============================================================

Inspect the route/action that starts an autonomous experiment.

Determine whether:

    run_loop(experiment_id)

is executed in a background task or whether the HTTP request remains blocked for the entire experiment.

The desired behavior is:

    POST /start-loop
          ↓
    start background execution
          ↓
    return HTTP response
          ↓
    UI polls experiment status

The UI must NOT remain blocked waiting for:

    ComfyUI generation
    video download
    Nemotron analysis
    optimizer request
    multiple iterations

If the current route already uses the appropriate FastAPI background mechanism, preserve it.

If not, implement the smallest appropriate change consistent with the existing architecture.

Do not introduce Celery, Redis, a new job queue, or another large infrastructure dependency.

Add a test verifying the start-loop request returns without waiting for the entire loop.

============================================================
5. Improve cancellation semantics
============================================================

The current loop checks cancellation before starting a new iteration.

Preserve that behavior unless the existing architecture supports stronger cancellation.

Document/implement the semantics:

    Cancel requested
       ↓
    current ComfyUI/Nemotron operation finishes
       ↓
    loop sees cancellation
       ↓
    no new iteration starts
       ↓
    experiment becomes CANCELLED

Do not attempt to forcibly terminate an external ComfyUI generation unless the existing ComfyUI service already supports safe cancellation.

The UI should clearly indicate that cancellation stops the next iteration and may not interrupt the current external operation.

Add a test that:

1. starts an iteration
2. marks experiment cancelled
3. completes current operation
4. verifies no next generation is started.

============================================================
6. Clean up stale comments/documentation
============================================================

The current Engine contains a section labelled:

    Autonomous Optimization Loop (not yet implemented)

but run_loop() is now implemented.

Update this to accurately describe the implementation.

Also update any docstrings/comments that still describe the engine as:

    generate → analyze → optimize → stop

if they refer to the autonomous path.

Do not change historical/single-cycle documentation that intentionally describes run_single_iteration().

The distinction should be explicit:

    run_single_iteration()
        Generate → Analyze → Optimize → STOP

    run_loop()
        Generate → Analyze → Optimize → Apply → next iteration

============================================================
7. Improve iteration state consistency
============================================================

Review run_loop() for stale ORM state.

Each iteration should obtain a fresh ExperimentORM snapshot before generating.

The parameters captured for iteration N must be immutable:

    prompt_used
    negative_prompt_used
    seed_used
    cfg_used
    noise_used
    steps_used
    workflow_used
    sampling settings

Then optimization may update the ExperimentORM for iteration N+1.

Never modify the historical values stored for iteration N after optimization.

Verify:

    iteration N
        uses steps=30
        records steps_used=30

    optimizer
        returns new_steps=45

    experiment
        steps becomes 45

    iteration N+1
        uses steps=45
        records steps_used=45

Add regression tests for this exact sequence.

============================================================
8. Verify target-score termination
============================================================

Confirm that:

    QAReport.overall_score

and:

    Experiment.target_score

use the same scale.

Current QAReport uses:

    0.0 - 1.0

and the live experiment produced:

    overall_score = 0.8

The autonomous loop currently checks:

    score >= target_score

Preserve this if the experiment target_score is also 0.0–1.0.

Do NOT mix this with:

    optimization.targeted_score_threshold = 70.0

unless the existing strategy explicitly requires that separate scale.

Add tests:

A. target_score=0.8 and score=0.8
   → stop

B. target_score=0.8 and score=0.81
   → stop

C. target_score=0.8 and score=0.79
   → optimize and continue

D. verify no optimization occurs after target is reached.

============================================================
9. Verify max_iterations termination
============================================================

Confirm:

    max_iterations=3

results in at most:

    iteration 1
    iteration 2
    iteration 3

There must never be iteration 4.

The check must happen before generation.

Add a test verifying generation call count.

============================================================
10. Verify failure handling
============================================================

Preserve the existing failure behavior:

    generation failure
    analysis failure
    optimization failure
    invalid optimization result

must:

- mark experiment FAILED
- persist current iteration
- persist stopping_reason
- not start another iteration
- not silently continue

Do not swallow exceptions.

Add/maintain tests for each major failure point.

============================================================
11. Preserve LTX2.3 sidecar behavior
============================================================

Do not modify the working LTX2.3 prompt/seed/CFG mappings unless required for steps.

The current expected mappings are:

    prompt
        121.text

    negative_prompt
        110.text

    seed
        114.noise_seed
        115.noise_seed

    cfg
        103.cfg
        129.cfg

    noise
        unsupported

Add the correct steps mapping based on the actual workflow JSON.

Do not hardcode these node IDs into Python.

============================================================
12. Sampling configuration
============================================================

Preserve the current experiment-specific sampling hierarchy:

    experiment.sampling_interval
        ↓
    config.video_analysis.sampling_interval

    experiment.max_frames
        ↓
    config.video_analysis.max_frames

    experiment.skip_frame
        ↓
    config.video_analysis.skip_frame

The autonomous loop should persist:

    sampling_interval_used
    max_frames_used
    skip_frame_used

against each iteration.

Do not regress this behavior while fixing the loop.

============================================================
13. Tests
============================================================

Use the actual project virtual environment:

    source .venv/bin/activate

Verify:

    which python
    python --version

Run:

    python -m compileall web orchestrator services

Then:

    pytest

All existing tests must pass.

Add tests covering the fixes above.

At minimum verify:

- steps reaches workflow
- all optimizer parameters reach next iteration
- unsupported noise remains untouched
- iteration snapshots remain immutable
- target-score termination
- max-iteration termination
- failure termination
- cancellation behavior
- candidate semantics
- background loop invocation
- stale documentation fixed

============================================================
14. Application startup
============================================================

Run:

    python -m web.app

Confirm the application starts successfully.

If port 7000 is already occupied by another MotionForge instance, do not kill unrelated processes. Report the condition and verify startup through an appropriate method.

============================================================
15. Final report
============================================================

Report:

1. Files changed
2. Whether steps was previously missing from the ComfyUI generation path
3. Exact LTX2.3 steps mapping discovered from the workflow
4. How OptimizationResult is now propagated to the next iteration
5. Candidate semantics discovered
6. Whether run_loop executes in background from the UI
7. Cancellation behavior
8. Target-score behavior
9. Max-iteration behavior
10. Tests added
11. Full pytest result
12. compileall result
13. startup result
14. Any remaining limitations

Do not claim the autonomous loop is production-ready unless the actual next-generation workflow has been verified to use the optimized values.

Do not modify unrelated UI features or optimization strategy code.
