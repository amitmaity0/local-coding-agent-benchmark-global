# 🏃 Benchmark Run Procedure

> **Standard operating procedure for executing, capturing, validating,
> and preserving every Local Coding Agent Benchmark run**

This document defines the repeatable procedure for a single benchmark
execution.

The goal is to make every run:

-   🔁 repeatable
-   📜 auditable
-   🧪 independently verifiable
-   📊 comparable across machines
-   🤖 usable by both Pi and future OpenHands experiments

The procedure is designed around the current repository structure:

``` text
local-coding-agent-benchmark/
│
├── benchmark/
│   ├── ai_video_optimization_app/
│   └── scripts/
│
├── tasks/
├── hardware/
└── results/
    ├── charts/
    ├── processed/
    └── raw/
        └── <RUN_ID>/
```

------------------------------------------------------------------------

# 🧭 Golden Rule

> ## One benchmark run = one immutable evidence package

Everything required to understand what happened during a run should be
preserved under one directory:

``` text
results/raw/<RUN_ID>/
```

A run should never depend on information that exists only in the
terminal scrollback.

------------------------------------------------------------------------

# 🔬 Complete Run Lifecycle

``` text
┌──────────────────────┐
│ 1. Define Run ID     │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 2. Prepare Machine   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. Prepare Repository│
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. Capture Baseline  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 5. Start Timer        │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 6. Start Coding Agent│
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 7. Preserve Session  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 8. Validate Repair   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 9. Capture Final Git │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 10. Freeze Evidence  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 11. Process Results  │
└──────────────────────┘
```

------------------------------------------------------------------------

# 1. 🆔 Create a Unique Run ID

Use:

``` text
YYYYMMDD-HHMMSS-<task>-<platform>-<runtime>
```

Examples:

``` text
20260813-064832-task01-mac-m4-omlx
20260813-122237-task01-windows-rtx5060-llama
```

The Run ID must be unique.

Use the same Run ID everywhere:

``` text
RUN_ID
  │
  ├── results/raw/<RUN_ID>/
  ├── Pi session name
  ├── metadata
  ├── logs
  └── published result references
```

------------------------------------------------------------------------

# 2. 💻 Prepare the Machine

Before beginning a benchmark, record the machine configuration.

At minimum:

  Category           Capture
  ------------------ --------------------------
  💻 Platform        Windows / macOS / Linux
  🧠 CPU             Exact CPU / SoC
  🎮 GPU             Exact GPU
  💾 GPU memory      VRAM or unified memory
  🧮 System memory   RAM
  🖥️ OS              OS + version
  ⚙️ Runtime         llama.cpp / oMLX / other
  🤖 Agent           Pi / OpenHands
  🧠 Model           Exact model
  📦 Quantization    Exact format
  📐 Context         Context window
  🚀 MTP             Enabled / disabled

Also record versions of important runtime components.

Example:

``` bash
uname -a
```

For macOS:

``` bash
sw_vers
system_profiler SPHardwareDataType
```

For Windows:

``` powershell
Get-ComputerInfo
nvidia-smi
```

For NVIDIA systems:

``` bash
nvidia-smi
```

The exact commands may differ by operating system.

> ⚠️ Do not change machine configuration after the run begins unless the
> experiment explicitly tests that change.

------------------------------------------------------------------------

# 3. 📁 Prepare the Benchmark Repository

The coding-agent benchmark repository and the software-under-test
repository should be treated as separate concerns.

Conceptually:

``` text
local-coding-agent-benchmark/
        │
        │ records experiment
        ▼
motionforge/
        │
        │ agent modifies
        ▼
software repair
```

Before each run:

``` bash
cd <software-repository>
```

Verify the repository:

``` bash
git status
git rev-parse HEAD
git branch --show-current
```

The working tree should be clean:

``` text
nothing to commit, working tree clean
```

If it is not clean, stop and resolve the state before benchmarking.

------------------------------------------------------------------------

# 4. 🎯 Checkout the Exact Baseline

The compared systems must begin from the same revision.

For the current Task 01 experiment, the primary baseline is:

``` text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

Recommended sequence:

``` bash
git fetch --all --prune
git checkout <benchmark-base>
git reset --hard <baseline-commit>
git clean -fd
```

Then verify:

``` bash
git rev-parse HEAD
git status --short
```

Expected:

``` text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

and no uncommitted changes.

------------------------------------------------------------------------

# 5. 🧪 Verify the Baseline

Before allowing the coding agent to modify the repository, verify that
the baseline itself is usable.

Run the task's baseline validation.

For example:

``` bash
pytest
```

or the project's documented test command.

Capture the result.

The important distinction is:

``` text
Baseline failure
      ≠
Agent-induced failure
```

If the baseline already fails, document exactly which tests fail before
the agent starts.

Do not silently fix baseline failures.

------------------------------------------------------------------------

# 6. 📸 Initialize the Evidence Directory

Create:

``` bash
mkdir -p results/raw/${RUN_ID}/pi-session
```

The resulting directory should eventually contain evidence such as:

``` text
results/raw/<RUN_ID>/
├── metadata.txt
├── git-before.txt
├── diff-before.patch
├── pi-version.txt
├── timing.txt
├── pi-session/
├── pi-session.jsonl
├── pi-session.html
├── git-after.txt
├── diff.patch
├── tests.txt
└── screenshots.md
```

Not every file is mandatory for every agent, but the principle is:

> **Preserve raw evidence before processing it.**

------------------------------------------------------------------------

# 7. 📝 Capture the Initial Git State

Record:

``` bash
git rev-parse HEAD
git status --short
git diff --stat
git diff
```

Recommended files:

``` text
git-before.txt
diff-before.patch
```

Example:

``` bash
git rev-parse HEAD | tee results/raw/${RUN_ID}/git-before.txt
git status --short | tee -a results/raw/${RUN_ID}/git-before.txt
git diff --stat | tee -a results/raw/${RUN_ID}/git-before.txt
git diff > results/raw/${RUN_ID}/diff-before.patch
```

The benchmark should always preserve the exact starting revision.

------------------------------------------------------------------------

# 8. 🤖 Record the Coding-Agent Version

For Pi:

``` bash
pi --version
```

Save it:

``` bash
pi --version > results/raw/${RUN_ID}/pi-version.txt
```

For future agents, record the equivalent version or Git revision.

------------------------------------------------------------------------

# 9. ⚙️ Capture the Full Configuration

Create:

``` text
metadata.txt
```

A recommended format:

``` text
Run ID:
Task ID:
Date:
Hostname:
OS:
Working Directory:

CPU:
GPU:
GPU VRAM:
System Memory:

Inference Runtime:
Runtime Version:
Agent:
Agent Version:
Model:
Model Revision:
Quantization:

Context Window:
Max Output Tokens:
MTP:
Temperature:
Top P:
Top K:

Baseline Commit:
Benchmark Branch:
```

Do not leave important fields undocumented when they materially affect
the experiment.

------------------------------------------------------------------------

# 10. ⏱️ Start Timing

The benchmark's primary timing measurement is **agent execution
wall-clock time**.

The conceptual boundary is:

``` text
START
  │
  ├── Agent receives task
  │
  ├── Agent investigates
  ├── Agent edits
  ├── Agent executes tools
  ├── Agent tests
  ├── Agent recovers
  └── Agent reaches final state
  │
END
```

Do not include, unless explicitly part of the experiment:

-   machine boot
-   model download
-   dependency installation
-   repository cloning
-   manual setup

Record both:

``` text
START_ISO
END_ISO
```

and:

``` text
WALL_TIME_SECONDS
WALL_TIME_MINUTES
```

------------------------------------------------------------------------

# 11. ⚠️ Timing Implementation Requirement

The current repository contains separate:

``` text
initialize.sh
run_benchmark.sh
stop_benchmark.sh
```

scripts.

The current `run_benchmark.sh` records the start timestamp, while
`stop_benchmark.sh` calculates duration from `START_TIME`.

Because shell variables normally do not persist automatically between
separately launched shell processes, **the benchmark procedure should
not rely on an in-memory `START_TIME` surviving from one script
invocation to another**.

The safer implementation is:

``` text
initialize
   │
   └── write START_TIME to timing.txt
                         │
                         ▼
                    run agent
                         │
                         ▼
                    stop script
                         │
                         └── read START_TIME
                             from timing.txt
```

This is important because the current raw timing files contain a
collection problem in which the wall-time fields are not reliable
elapsed-duration values.

### Recommended rule

> **Always preserve the raw start/end timestamps. Calculate elapsed
> duration during result processing from those timestamps if
> necessary.**

Do not overwrite the raw evidence.

------------------------------------------------------------------------

# 12. 🚀 Start the Coding Agent

For the current Pi benchmark, the agent should be launched with the
exact configuration being evaluated.

The current RTX benchmark script uses:

``` bash
pi \
  --session-dir "${RUN_DIR}/pi-session" \
  --name "${RUN_ID}" \
  --model llamacpp/Qwen3.6-27B-MTP-4.5bpw-pure.gguf
```

The corresponding Mac configuration uses the oMLX Qwen3.6-27B MTP
configuration.

The exact model/runtime invocation must be recorded in the run metadata.

------------------------------------------------------------------------

# 13. 📝 Provide the Task

Give the coding agent the benchmark task according to the task
definition.

For Task 01:

``` text
tasks/task01.md
```

should define the engineering problem and success criteria.

The agent should receive the same substantive task for every compared
configuration.

Do not manually guide one agent toward:

-   a specific file
-   a specific function
-   a specific implementation
-   a specific patch
-   a specific workaround

unless that information is intentionally part of the benchmark.

------------------------------------------------------------------------

# 14. 🚫 Do Not Interfere During the Run

Once the benchmark begins:

``` text
Agent
  │
  ├── inspect
  ├── reason
  ├── edit
  ├── test
  ├── diagnose
  └── iterate
```

The operator should not:

-   fix code manually
-   tell the agent where the bug is
-   run hidden repair commands
-   modify the repository
-   selectively change configuration
-   restart the agent merely because progress is slow

If operator intervention becomes necessary, record it as a benchmark
anomaly.

------------------------------------------------------------------------

# 15. 📜 Preserve the Agent Session

For Pi, preserve the complete session where possible.

Recommended:

``` text
pi-session/
pi-session.jsonl
pi-session.html
```

The JSONL session is the machine-readable source.

The HTML export is a convenient human-readable representation.

The session can reveal:

``` text
Prompt
   ↓
Reasoning / responses
   ↓
Tool calls
   ↓
File changes
   ↓
Test execution
   ↓
Failures
   ↓
Recovery
   ↓
Final response
```

This is extremely valuable for later analysis.

------------------------------------------------------------------------

# 16. 🧪 Capture Test Results

After the agent declares completion, run the benchmark's validation
procedure.

Capture:

``` text
tests.txt
```

Example:

``` bash
pytest 2>&1 | tee results/raw/${RUN_ID}/tests.txt
```

Use the project's actual validation command if it differs.

Record:

-   command
-   exit code
-   tests collected
-   tests passed
-   tests failed
-   skipped tests
-   errors
-   warnings relevant to interpretation

------------------------------------------------------------------------

# 17. ⚠️ Distinguish Environment Errors from Repair Failures

A benchmark validation command can fail because the environment is
broken.

For example:

``` text
pytest: command not found
```

is not equivalent to:

``` text
pytest
FAILED test_x
```

The first indicates a test-environment problem.

The second indicates a software/test failure.

Always classify the result:

  Result                        Classification
  ----------------------------- ------------------------
  All required tests pass       ✅ Validation success
  Tests fail due to code        ❌ Repair failure
  Test command unavailable      ⚠️ Environment failure
  Baseline already failed       ⚠️ Baseline anomaly
  Test infrastructure crashes   ⚠️ Validation anomaly

Do not convert an environment failure into a software failure without
evidence.

------------------------------------------------------------------------

# 18. 🧾 Capture the Final Git State

After validation:

``` bash
git status --short
git rev-parse HEAD
git diff --stat
git diff
```

Save:

``` text
git-after.txt
diff.patch
```

Recommended:

``` bash
git status --short > results/raw/${RUN_ID}/git-after.txt
git rev-parse HEAD >> results/raw/${RUN_ID}/git-after.txt
git diff --stat >> results/raw/${RUN_ID}/git-after.txt
git diff > results/raw/${RUN_ID}/diff.patch
```

The final patch is one of the most important benchmark artifacts.

------------------------------------------------------------------------

# 19. 🔍 Check for Unexpected Changes

Before declaring the run complete, inspect:

``` bash
git status
git diff --stat
```

Ask:

``` text
Did the agent modify only expected repository files?
```

Look for:

-   generated binaries
-   model files
-   temporary files
-   caches
-   environment files
-   unrelated changes
-   accidental deletions

If unexpected changes exist, preserve them and document the anomaly.

Do not silently delete them before freezing the evidence.

------------------------------------------------------------------------

# 20. ⏹️ Stop Timing and Freeze the Run

Capture:

``` text
END_ISO
END_TIME
```

Then calculate:

``` text
duration = END_TIME - START_TIME
```

Prefer reconstructing elapsed time from the timestamps if the raw
duration field is suspect.

The evidence directory should now be considered frozen.

``` text
results/raw/<RUN_ID>/
       │
       ├── configuration
       ├── baseline
       ├── session
       ├── timing
       ├── tests
       └── final patch
```

------------------------------------------------------------------------

# 21. 🧊 Evidence Freeze Checklist

Before processing results, verify:

``` text
☐ Unique RUN_ID
☐ Task ID recorded
☐ Hardware recorded
☐ OS recorded
☐ Runtime recorded
☐ Runtime version recorded
☐ Agent recorded
☐ Agent version recorded
☐ Model recorded
☐ Quantization recorded
☐ Context recorded
☐ MTP recorded
☐ Baseline commit recorded
☐ Working tree state recorded
☐ Pre-run diff captured
☐ Agent session preserved
☐ Start timestamp preserved
☐ End timestamp preserved
☐ Test output preserved
☐ Final git state preserved
☐ Final patch preserved
☐ Anomalies documented
```

Only after this checklist is complete should the run be considered an
**evidence-complete benchmark run**.

------------------------------------------------------------------------

# 22. 📊 Process the Raw Results

Raw results should not be edited.

Instead:

``` text
results/raw/
      │
      ▼
processing
      │
      ▼
results/processed/
      │
      ▼
charts / comparison
```

For example:

``` text
results/raw/
    20260813-064832-task01-mac-m4/

results/processed/
    task01-mac-m4.json
```

The processed file should reference the original Run ID.

------------------------------------------------------------------------

# 23. 🧮 Normalize Measurements

Convert raw measurements into a consistent schema.

Recommended fields:

``` text
run_id
task_id
platform
hardware
runtime
runtime_version
agent
agent_version
model
model_revision
quantization
context_window
mtp
start_time
end_time
wall_time_seconds
input_tokens
output_tokens
total_tokens
prompt_tokens_per_second
generation_tokens_per_second
model_calls
tool_calls
test_attempts
tests_passed
tests_failed
repair_success
files_changed
lines_added
lines_deleted
```

This allows future experiments to be compared without manually
rebuilding tables.

------------------------------------------------------------------------

# 24. 🔬 Classify the Run

Every run should receive one primary outcome:

``` text
SUCCESS
FAILURE
TIMEOUT
ENVIRONMENT_FAILURE
BASELINE_FAILURE
INCOMPLETE
```

Example:

``` text
repair_success: true
validation_status: success
```

or:

``` text
repair_success: unknown
validation_status: environment_failure
```

Do not force ambiguous runs into `SUCCESS` or `FAILURE`.

------------------------------------------------------------------------

# 25. 📈 Generate Comparison Results

Only compare runs after confirming that their experimental variables are
appropriate.

For the current primary comparison:

``` text
                    Same baseline
                         │
                         ▼
                  Same Task 01
                         │
                         ▼
                 Same Pi agent
                         │
                         ▼
                  Qwen3.6-27B
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       RTX / llama.cpp          M4 / oMLX
            55K                    55K
              │                     │
              └──────────┬──────────┘
                         ▼
                     Compare
```

The comparison should report both:

### Outcome

``` text
Repair success
Tests
Wall-clock time
```

and:

### Explanation

``` text
Token usage
Model calls
Tool calls
Trajectory
Resource usage
```

------------------------------------------------------------------------

# 26. 📋 Recommended Result Table

Every benchmark comparison should eventually produce a table similar to:

  Metric                     RTX 5060 Ti         M4 Pro
  ------------------ ------------------- --------------
  Hardware             RTX 5060 Ti 16 GB   M4 Pro 64 GB
  Runtime                      llama.cpp           oMLX
  Agent                        Pi 0.84.1      Pi 0.84.1
  Model                      Qwen3.6-27B    Qwen3.6-27B
  Context                            55K            55K
  MTP                            Enabled        Enabled
  Wall time                      Derived        Derived
  Input tokens                       TBD            TBD
  Output tokens                      TBD            TBD
  Generation tok/s                   TBD            TBD
  Model calls                        TBD            TBD
  Tool calls                         TBD            TBD
  Tests                              TBD            TBD
  Repair outcome                     TBD            TBD

`TBD` values must remain TBD until supported by raw evidence.

------------------------------------------------------------------------

# 27. 🧠 Analyze the Agent Trajectory

The final patch alone is not enough.

Review the session for:

``` text
1. Initial understanding
2. Repository exploration
3. Hypothesis formation
4. First implementation
5. Test execution
6. Failure diagnosis
7. Recovery
8. Additional edits
9. Final validation
```

A useful trajectory diagram is:

``` text
        🔎 Explore
            │
            ▼
        🧠 Hypothesis
            │
            ▼
        ✏️ Implement
            │
            ▼
        🧪 Test
            │
       ┌────┴────┐
       │         │
      Pass     Fail
       │         │
       ▼         ▼
    Validate   Diagnose
                 │
                 ▼
               Repair
                 │
                 └──────► 🧪 Test
```

This can reveal why two configurations with similar token throughput
have different software-engineering outcomes.

------------------------------------------------------------------------

# 28. 🧪 Benchmark Quality Review

Before publishing a comparison, perform a second-pass audit.

Ask:

### Baseline

-   Did both systems start from the same revision?
-   Was the working tree clean?

### Configuration

-   Was the model identical?
-   Was quantization documented?
-   Was context identical?
-   Was MTP identical?
-   Were relevant agent settings identical?

### Timing

-   Are start/end timestamps valid?
-   Is elapsed time derived correctly?

### Validation

-   Did the test environment work?
-   Were baseline failures distinguished from agent failures?

### Patch

-   Is the final patch preserved?
-   Are unrelated changes documented?

### Agent trajectory

-   Is the session available?
-   Are tool calls inspectable?

### Interpretation

-   Are conclusions limited to what the experiment supports?

------------------------------------------------------------------------

# 29. 🚨 When to Reject a Run

Do not discard a failed run merely because it is inconvenient.

However, mark it as invalid for a specific comparison when a fundamental
benchmark condition was violated.

Examples:

``` text
❌ Wrong repository revision
❌ Wrong model
❌ Wrong task
❌ Manual code intervention
❌ Missing session when session is a required metric
❌ Hardware changed during run
❌ Benchmark configuration accidentally changed
```

The original evidence should still be retained.

Use:

``` text
status: INVALID_FOR_COMPARISON
reason: ...
```

rather than deleting the run.

------------------------------------------------------------------------

# 30. 🔁 Re-running a Benchmark

If a run must be repeated:

> **Never overwrite the previous Run ID.**

Create a new one:

``` text
20260813-180000-task01-mac-m4-omlx-rerun
```

or simply use a new timestamp.

Keep both runs.

This preserves the experimental history.

------------------------------------------------------------------------

# 31. 🧪 Repeated Runs for Nondeterministic Agents

For serious comparisons, use:

``` text
Task 01
├── Run 1
├── Run 2
└── Run 3
```

Then aggregate:

``` text
Median repair time
Success rate
Token distribution
Tool-call distribution
```

Do not report only the fastest run.

------------------------------------------------------------------------

# 32. 🤖 Future OpenHands Compatibility

This procedure is deliberately agent-independent.

For Pi:

``` text
Task
 ↓
Pi
 ↓
Local runtime
 ↓
Repository
 ↓
Validation
```

For OpenHands:

``` text
Task
 ↓
OpenHands
 ↓
Local runtime
 ↓
Repository
 ↓
Validation
```

The evidence schema should remain as similar as possible:

``` text
             Same Task
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
      Pi               OpenHands
       │                   │
       ▼                   ▼
   Run Record          Run Record
       │                   │
       └─────────┬─────────┘
                 ▼
             Comparison
```

Only agent-specific evidence should differ.

------------------------------------------------------------------------

# 33. 📦 Final Run Package

A healthy Pi run should look approximately like:

``` text
results/raw/<RUN_ID>/
│
├── metadata.txt
├── pi-version.txt
│
├── git-before.txt
├── diff-before.patch
│
├── timing.txt
│
├── pi-session/
├── pi-session.jsonl
├── pi-session.html
│
├── tests.txt
│
├── git-after.txt
├── diff.patch
│
└── screenshots.md
```

Additional artifacts are welcome when they help explain the run.

------------------------------------------------------------------------

# 34. 🏷️ Run Status

Use a small controlled vocabulary:

  -----------------------------------------------------------------------
  Status                              Meaning
  ----------------------------------- -----------------------------------
  🟢 `SUCCESS`                        Repair completed and validation
                                      passed

  🔴 `FAILURE`                        Agent completed/terminated but
                                      repair failed

  🟠 `TIMEOUT`                        Maximum runtime reached

  🟡 `ENVIRONMENT_FAILURE`            Benchmark environment prevented
                                      valid validation

  🟡 `BASELINE_FAILURE`               Baseline was already failing

  ⚪ `INCOMPLETE`                     Evidence package is incomplete

  ⚫ `INVALID_FOR_COMPARISON`         Experimental protocol was violated
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 35. 🧠 Evidence Hierarchy

When two sources disagree, use this priority:

``` text
1. Raw repository state
       ↓
2. Raw agent session
       ↓
3. Raw command output
       ↓
4. Machine-readable run metadata
       ↓
5. Processed metrics
       ↓
6. Human interpretation
```

Never let a derived spreadsheet overwrite the underlying raw evidence.

------------------------------------------------------------------------

# 36. 📜 Publication Rule

Before a benchmark number appears in:

-   README
-   GitHub issue
-   Hugging Face
-   Reddit
-   Hacker News
-   X
-   LinkedIn
-   research notes

it should be traceable to:

``` text
Published number
      │
      ▼
Processed result
      │
      ▼
Run ID
      │
      ▼
Raw evidence
      │
      ├── session
      ├── timing
      ├── tests
      └── patch
```

This creates a defensible chain of evidence.

------------------------------------------------------------------------

# 37. 🧭 Current Task 01 Procedure

For the current benchmark series, the recommended sequence is:

``` text
1. Select Task 01
        ↓
2. Checkout baseline
   9ab2b50bc2ce...
        ↓
3. Verify clean working tree
        ↓
4. Verify baseline tests/environment
        ↓
5. Create unique Run ID
        ↓
6. Capture hardware/runtime metadata
        ↓
7. Capture git-before
        ↓
8. Start reliable timestamp recording
        ↓
9. Start Pi with exact model/runtime config
        ↓
10. Give Task 01 to Pi
        ↓
11. Do not intervene
        ↓
12. Preserve Pi session
        ↓
13. Run validation
        ↓
14. Capture git-after
        ↓
15. Capture final patch
        ↓
16. Capture end timestamp
        ↓
17. Freeze raw evidence
        ↓
18. Process metrics
        ↓
19. Review anomalies
        ↓
20. Add to comparison
```

------------------------------------------------------------------------

# 38. ✅ Final Operator Checklist

Before starting:

``` text
☐ Correct machine
☐ Correct runtime
☐ Correct model
☐ Correct context
☐ Correct MTP configuration
☐ Correct task
☐ Correct baseline commit
☐ Clean repository
☐ Baseline validation checked
☐ Run ID created
```

During run:

``` text
☐ Timer started
☐ Agent started with recorded configuration
☐ No manual intervention
☐ Session preserved
```

After run:

``` text
☐ Tests captured
☐ End timestamp captured
☐ git-after captured
☐ diff.patch captured
☐ Session exported
☐ Anomalies recorded
☐ Raw directory frozen
```

Before publication:

``` text
☐ Timing verified
☐ Test result classified
☐ Baseline anomalies separated
☐ Processed metrics trace to raw evidence
☐ Comparison variables verified
☐ Claims limited to measured evidence
```

------------------------------------------------------------------------

# 🎯 Final Principle

The benchmark should make it possible to answer three questions for
**every single published result**:

### 1. What exactly was tested?

``` text
Hardware
+
Runtime
+
Model
+
Agent
+
Task
```

### 2. What exactly happened?

``` text
Session
+
Tool trajectory
+
Timing
+
Tests
+
Final patch
```

### 3. Can somebody audit the claim?

``` text
Published Result
       ↓
Run ID
       ↓
Raw Evidence
       ↓
Original Repository State
```

> ## 🔬 If the result cannot be traced back to the raw run, it is not yet a benchmark result.

This procedure is intended to remain stable as LCAB expands from **Pi +
Qwen3.6-27B** to additional runtimes, hardware, models, and eventually
**OpenHands**.
