# 🔧 Task 01 --- Autonomous Video Optimization Repair

> **Real software-repair workload used to evaluate local coding agents**

**Task ID:** `task01`\
**Benchmark category:** Real software repair\
**Application:** MotionForge / AI video optimization workflow\
**Primary capability:** Autonomous optimization-loop implementation and
workflow-parameter propagation\
**Primary agent:** Pi\
**Model:** Qwen3.6-27B

------------------------------------------------------------------------

## 🎯 Task Overview

This workload asks a coding agent to work inside an existing software
repository and implement/fix the autonomous optimization flow so that
experiment parameters are correctly propagated through generation,
analysis, optimization, persistence, and subsequent iterations.

The task is intentionally more representative of real software
engineering than a standalone code-generation prompt: the agent must
understand an existing codebase, modify multiple components, preserve
behavior, add regression tests, and validate the result.

------------------------------------------------------------------------

## 🔄 Intended Optimization Flow

``` text
              ┌───────────────────────────────┐
              │       Experiment State        │
              │ prompt / seed / cfg / steps  │
              └───────────────┬───────────────┘
                              │
                              ▼
                       🎬 Generate
                              │
                              ▼
                     🔍 Analyze / QA
                              │
                              ▼
                       📊 Score result
                              │
                 ┌────────────┴────────────┐
                 │                         │
           Target reached?             Continue
                 │                         │
              YES│                         ▼
                 ▼                    🤖 Optimize
             🏁 Stop                      │
                                          ▼
                                💾 Persist optimized
                                   parameters
                                          │
                                          ▼
                                🔄 Next iteration
```

The implementation must preserve enough state for an optimization result
from one iteration to become the input configuration for the next
iteration.

------------------------------------------------------------------------

# 🧩 Core Engineering Requirements

## 1. 🔄 Autonomous optimization loop

The engine should support repeated:

``` text
Generate
   ↓
Analyze
   ↓
Optimize
   ↓
Apply optimization result
   ↓
Persist iteration
   ↓
Generate again
```

The implementation supports stopping for:

-   🎯 target score reached
-   🔢 maximum iterations reached
-   🛑 user cancellation
-   ❌ unrecoverable failure

The benchmark branch checks cancellation before starting another
iteration and checks the iteration limit before generation.

------------------------------------------------------------------------

## 2. 📸 Sampling configuration

The loop uses experiment-specific sampling configuration when present,
otherwise application defaults.

  -----------------------------------------------------------------------
  Parameter                           Purpose
  ----------------------------------- -----------------------------------
  `sampling_interval`                 Controls temporal sampling during
                                      video analysis

  `max_frames`                        Limits the number of analyzed
                                      frames

  `skip_frame`                        Controls frame skipping during
                                      analysis
  -----------------------------------------------------------------------

``` text
Experiment configuration
        │
        ├── sampling_interval
        ├── max_frames
        └── skip_frame
        │
        ▼
Video analysis / QA
        │
        ▼
Optimization score
```

------------------------------------------------------------------------

## 3. ⚙️ Inference-step propagation

The workload verifies that the experiment's `steps` parameter reaches
the actual generation workflow.

``` text
ExperimentORM.steps
        │
        ▼
Engine.generate()
        │
        ▼
WorkflowLoader.set_steps()
        │
        ▼
Workflow sidecar mapping
        │
        ▼
ComfyUI workflow JSON
        │
        ▼
Scheduler / sampler node
```

For the LTX2.3 workflow used by this benchmark:

  Parameter      Node Input
  ----------- ------- ---------
  `steps`       `206` `steps`

The workflow sidecar declares `steps` as a required parameter targeting
node `206`.

------------------------------------------------------------------------

## 4. 🧠 Iteration history

Each optimization iteration should preserve the parameters used to
produce that iteration:

``` text
Prompt
Negative prompt
Seed
CFG
Noise
Steps
Workflow
Sampling interval
Maximum frames
Skip frame
QA score
```

The intended trajectory is:

``` text
Iteration 1
    │
    ├── parameters
    ├── generated output
    ├── QA score
    └── optimization result
              │
              ▼
Iteration 2
    │
    ├── updated parameters
    ├── generated output
    ├── QA score
    └── optimization result
              │
              ▼
             ...
```

The purpose is to make the optimization trajectory auditable, not merely
to obtain a final score.

------------------------------------------------------------------------

# 🧪 Regression-Test Coverage

A major part of this workload is extending automated tests around the
new behavior.

The M4 Pro 55K benchmark branch changes six files:

  --------------------------------------------------------------------------------------
  File                                                   Additions Purpose
  ----------------------------------- ---------------------------- ---------------------
  `orchestrator/engine.py`                                       4 Loop/generation
                                                                   integration

  `services/workflow.py`                                        20 Sidecar-aware `steps`
                                                                   mapping

  `tests/test_autonomous_loop.py`                              463 Loop and
                                                                   parameter-flow
                                                                   coverage

  `tests/test_sidecar.py`                                       10 Sidecar behavior

  `tests/test_workflow.py`                                      49 Workflow mapping

  `workflows/LTX2.3-Basic-API.yaml`                              6 `steps` declaration
  --------------------------------------------------------------------------------------

The corresponding RTX benchmark branch changes the same six files and
adds 525 lines to `tests/test_autonomous_loop.py`.

This makes Task 01 a coordinated multi-file software-engineering problem
rather than a trivial isolated edit.

------------------------------------------------------------------------

# 🏗️ Expected Architecture

``` text
┌──────────────────────────────────────────────────────┐
│                    Experiment                         │
│ prompt • seed • cfg • noise • steps • iteration     │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                     Engine                           │
│                                                      │
│ run_loop()                                           │
│   │                                                  │
│   ├── generate()                                     │
│   ├── analyze_with_sampling()                       │
│   ├── persist iteration                              │
│   ├── evaluate target                                │
│   ├── optimize()                                     │
│   └── apply optimization result                      │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                Workflow Loader                       │
│                                                      │
│ sidecar-aware parameter mapping                      │
│ prompt / seed / cfg / steps / ...                    │
└─────────────────────────┬────────────────────────────┘
                          │
                          ▼
                    🎬 ComfyUI
                          │
                          ▼
                    Generated video
                          │
                          ▼
                      🔍 QA
```

------------------------------------------------------------------------

# 📋 Acceptance Criteria

## Functional

-   [ ] Autonomous optimization loop executes multiple iterations.
-   [ ] Generation occurs for each iteration.
-   [ ] Video analysis occurs after generation.
-   [ ] Optimization occurs when the target is not reached.
-   [ ] Optimization results are applied to experiment state.
-   [ ] Updated parameters reach the next iteration.
-   [ ] Target-score termination works.
-   [ ] Maximum-iteration termination works.
-   [ ] User cancellation is handled.
-   [ ] Generation/analysis failures are surfaced.

## Parameter propagation

-   [ ] `sampling_interval` reaches video analysis.
-   [ ] `max_frames` reaches video analysis.
-   [ ] `skip_frame` reaches video analysis.
-   [ ] `steps` reaches generation.
-   [ ] Workflow sidecar mappings are honored.
-   [ ] Generic workflow fallback remains available where appropriate.

## Persistence

-   [ ] Iteration parameters are recorded.
-   [ ] Iteration score is recorded.
-   [ ] Best score is tracked.
-   [ ] Best iteration is tracked.
-   [ ] Best parameters are retained.
-   [ ] Optimization metadata is persisted.

## Testing

-   [ ] Regression tests cover loop behavior.
-   [ ] Workflow parameter mapping is tested.
-   [ ] Sidecar parameter mapping is tested.
-   [ ] Multi-iteration propagation is tested.
-   [ ] Existing tests remain compatible.

------------------------------------------------------------------------

# 🔎 Why This Is a Useful Coding-Agent Benchmark

  -----------------------------------------------------------------------
  Property                            Why it matters
  ----------------------------------- -----------------------------------
  🧩 Multi-file                       Requires repository-wide reasoning

  🔄 Stateful                         Changes must survive across
                                      iterations

  🧠 Behavioral                       Agent must understand execution
                                      flow

  🧪 Test-heavy                       Requires regression-test
                                      development

  ⚙️ Configuration-driven             Parameters cross subsystem
                                      boundaries

  🔗 Integration-oriented             Engine, workflow, persistence and
                                      tests interact

  🐛 Failure-sensitive                Small propagation errors can break
                                      the flow

  📈 Iterative                        Mirrors real debugging and
                                      implementation
  -----------------------------------------------------------------------

The workload therefore measures **software-engineering behavior**, not
just code-generation ability.

------------------------------------------------------------------------

# 📐 Benchmark Boundary

The agent starts from a known repository state and is expected to
discover implementation details independently.

The benchmark should not manually provide:

-   exact files to modify
-   exact functions to edit
-   exact node mappings
-   the final implementation
-   a patch to apply

The intended evaluation is:

``` text
Same task
   +
Same repository state
   +
Same validation
   ↓
Different local AI configuration
   ↓
Compare agent trajectory and outcome
```

------------------------------------------------------------------------

# 🗃️ Baseline and Provenance

The primary benchmark runs started from:

``` text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

The provenance is:

``` text
                         Baseline
                     9ab2b50bc2ce...
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
             Mac / oMLX          RTX / llama.cpp
                55K                  55K
```

The corresponding MotionForge benchmark branches are:

``` text
benchmark/task9-m4pro-omlx-mtp-55k
benchmark/task9-rtx5060ti-mtp
benchmark/task9-m4pro-omlx-mtp-unlimited
```

> ℹ️ **Naming note:** the benchmark repository records this workload as
> `task01`, while the corresponding MotionForge benchmark branches use
> `task9` in their branch names and commit messages. Both identifiers
> are preserved here for traceability.

------------------------------------------------------------------------

# 🧪 Validation Strategy

The benchmark does not judge an agent by diff size.

``` text
                 Code changes
                      │
                      ▼
                Automated tests
                      │
                      ▼
               Functional behavior
                      │
                      ▼
                Final repository
```

A large patch is not inherently better.

Likewise:

``` text
More tokens     ❌
More tool calls ❌
More files      ❌
More iterations ❌
```

do not automatically mean better performance.

The desired outcome is:

``` text
Correct implementation
        +
Regression protection
        +
Successful validation
        +
Reasonable execution trajectory
```

------------------------------------------------------------------------

# 📊 Benchmark Measurements

Each run should capture the agent trajectory as well as the final patch.

  Metric                Purpose
  --------------------- -------------------------
  ⏱️ Wall-clock time    End-to-end productivity
  🧠 Input tokens       Context/inference cost
  ✍️ Output tokens      Generation cost
  🚀 Generation tok/s   Runtime performance
  📥 Prompt tok/s       Context processing
  🤖 Model calls        Agent trajectory
  🔧 Tool calls         Repository interaction
  🔄 Iterations         Convergence behavior
  🧪 Test attempts      Debugging effort
  ✅ Tests passed       Functional outcome
  ❌ Tests failed       Failure behavior
  📁 Files modified     Patch scope
  📝 Diff size          Implementation scope
  🏆 Final outcome      Repair success

The raw benchmark repository preserves original run artifacts so
processed results can be regenerated without losing provenance.

------------------------------------------------------------------------

# ⚠️ Known Data Limitations

### Timing collection

The current raw `timing.txt` files preserve start/end timestamps but
contain incorrectly formatted elapsed-time fields.

Therefore:

> **Elapsed time should be reconstructed from the preserved timestamps
> rather than trusting the existing `WALL_TIME_*` fields.**

### Mac test-output collection

The current Mac `tests.txt` contains:

``` text
pytest: command not found
```

This is an environment/collection issue and should not automatically be
interpreted as a software-repair failure.

The final benchmark analysis should distinguish raw collection problems
from validated software outcomes.

------------------------------------------------------------------------

# 🧠 Why Task 01 Matters

This workload represents the kind of problem a coding agent encounters
in real development:

``` text
Existing system
      │
      ▼
New requirement / defect
      │
      ▼
Understand architecture
      │
      ▼
Find affected components
      │
      ▼
Implement coordinated changes
      │
      ▼
Write regression tests
      │
      ▼
Run tests
      │
      ▼
Debug failures
      │
      ▼
Validate final behavior
```

It exposes the interaction between:

``` text
🧠 Model
   +
🤖 Agent architecture
   +
🔧 Tool execution
   +
📚 Context management
   +
⚙️ Inference runtime
   +
💻 Hardware
```

That interaction is the central research interest of LCAB.

------------------------------------------------------------------------

# 🔗 Related Benchmark Configurations

  --------------------------------------------------------------------------------------
  Experiment    Hardware      Runtime                 Context Purpose
  ------------- ------------- ------------- ----------------- --------------------------
  🟢 RTX        RTX 5060 Ti   llama.cpp                   55K Hardware/runtime
  primary       16 GB                                         comparison

  🔵 Mac        M4 Pro 64 GB  oMLX                        55K Hardware/runtime
  primary                                                     comparison

  🟣 Mac        M4 Pro 64 GB  oMLX                  Unlimited Context/agent-trajectory
  exploratory                                                 study
  --------------------------------------------------------------------------------------

The **RTX vs Mac 55K pair** is the primary comparison.

The unlimited-context run is retained as a separate exploratory study
because its implementation trajectory differs more substantially from
the two 55K benchmark branches.

------------------------------------------------------------------------

# ✅ Definition of Success

For LCAB, Task 01 is successful when the coding agent:

> **Independently investigates the repository, implements the required
> autonomous optimization behavior and parameter propagation, preserves
> regression coverage, and leaves the repository in a validated working
> state.**

The benchmark then measures **how efficiently and reliably** the agent
reaches that state.

------------------------------------------------------------------------

## 🧪 Task 01 in One Diagram

``` text
                    TASK 01
                       │
                       ▼
              🔧 Real software repair
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   🔄 Loop         ⚙️ Parameters    🧪 Tests
        │              │              │
        │        ┌─────┴─────┐        │
        │        │           │        │
        │      steps      sampling    │
        │        │       configuration│
        │        └─────┬─────┘        │
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 🤖 Coding Agent
                       │
                       ▼
                 💻 Repository
                       │
                       ▼
                 🧪 Validation
                       │
                       ▼
                 ✅ Working repair
```

> **Benchmark objective:** measure the path from a real engineering
> problem to a validated software repair---not merely the amount of code
> or tokens produced.
