# 🔬 Benchmark Methodology

> **How the Local Coding Agent Benchmark measures real-world local AI software-repair performance**

The Local Coding Agent Benchmark (LCAB) is designed to measure **end-to-end effectiveness and performance of local AI coding agents on real software-repair workloads**.

The benchmark intentionally focuses on software-engineering outcomes rather than isolated model inference metrics.

---

# 🎯 1. Research Objective

The primary research question is:

> **How quickly and reliably can a local coding-agent system solve a real software-repair task?**

LCAB treats a coding-agent system as the complete execution stack:

```text
┌──────────────────────┐
│ 💻 Hardware          │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🪟 Operating System  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ ⚡ Inference Runtime │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🧠 Model             │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🤖 Coding Agent      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🔧 Tool Execution    │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 📁 Repository        │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🐛 Software Repair   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 🧪 Validation / Tests│
└──────────────────────┘
```

Therefore, benchmark results describe a **specific tested configuration**, rather than making universal claims about one hardware component.

For example:

```text
🟢 RTX 5060 Ti
    +
🪟 Windows
    +
⚡ llama.cpp
    +
🧠 Qwen3.6-27B
    +
🤖 Pi
```

is compared with:

```text
🔵 M4 Pro
    +
🍎 macOS
    +
⚡ oMLX / MLX
    +
🧠 Qwen3.6-27B
    +
🤖 Pi
```

The methodology is intentionally reusable when the coding agent changes from Pi to OpenHands.

---

# 🤖 2. Coding Agent

## Current Agent

The current LCAB benchmark uses:

> **Pi**

Pi is the primary coding agent for the initial benchmark series.

Each run records:

- Pi version / commit
- model configuration
- inference endpoint/runtime
- context configuration
- sampling configuration
- tool configuration
- timeout/retry settings
- permission configuration
- working-directory configuration

The objective is to make the agent configuration reproducible rather than treating the agent as a black box.

---

## 🔮 Future Agent

The methodology is agent-independent.

Future experiments are intended to include:

> **OpenHands**

The same workloads should be reused whenever technically possible.

```text
                 🔧 Same Workload
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
           🤖 Pi             🤖 OpenHands
             │                   │
             ▼                   ▼
        Qwen3.6-27B         Qwen3.6-27B
             │                   │
             ▼                   ▼
       Local Runtime        Local Runtime
             │                   │
             ▼                   ▼
          Hardware            Hardware
```

The objective is not to declare one agent universally superior.

Instead, LCAB investigates how agent architecture affects:

- repair success
- repair time
- token consumption
- tool usage
- failure recovery
- resource consumption
- trajectory/convergence behavior

---

# 🧩 3. Benchmark Unit

The fundamental unit of measurement is a:

> **Software Repair Task**

A task consists of a repository at a known revision plus a clearly defined software problem.

```text
┌─────────────────────────────┐
│ 📁 Repository               │
├─────────────────────────────┤
│ 🔖 Known starting revision  │
├─────────────────────────────┤
│ 🐛 Problem description      │
├─────────────────────────────┤
│ 🎯 Expected behavior        │
├─────────────────────────────┤
│ 🧪 Test suite               │
├─────────────────────────────┤
│ ✅ Validation criteria      │
└─────────────────────────────┘
```

Every compared system starts from the same repository state.

---

# 🔧 4. Task Selection

LCAB prioritizes realistic engineering problems over artificial prompts.

Preferred workloads include:

- 🐛 bugs
- ❌ incorrect behavior
- ➕ missing functionality
- 🔗 broken integrations
- 🔄 regression fixes
- 🔌 API compatibility problems
- ⚙️ configuration problems
- 🧪 test failures
- 🧩 implementation defects
- 📁 multi-file repairs

A good task requires genuine investigation and modification.

It should not be reducible to:

```text
Prompt
  ↓
Generate isolated function
  ↓
Done
```

Instead:

```text
Problem
   ↓
Repository investigation
   ↓
Architecture understanding
   ↓
Implementation
   ↓
Testing
   ↓
Debugging
   ↓
Validated repair
```

---

# 📈 5. Task Difficulty

LCAB should eventually cover multiple difficulty levels.

| Level | Typical characteristics |
|---|---|
| 🟢 Simple | Single-file defect, straightforward logic error |
| 🟡 Moderate | Multi-file modification, API investigation, test-driven debugging |
| 🔴 Complex | Repository-wide investigation, ambiguous failures, multiple iterations, recovery |

Conclusions should not be based exclusively on one difficulty level.

The current Task 01 workload is intentionally representative of a **multi-file, stateful software-engineering problem**.

---

# 📁 6. Repository Preparation

Every run must have a deterministic starting state.

Before execution:

```text
Restore repository
      ↓
Checkout exact revision
      ↓
Reset working tree
      ↓
Verify dependencies
      ↓
Run baseline validation
      ↓
Record environment
      ↓
Freeze starting state
```

Required baseline information:

- repository
- branch/ref
- exact commit SHA
- working-tree state
- baseline test result
- runtime environment
- hardware configuration

The initial repository state must be identical for compared systems.

---

# 🎯 7. Agent Instructions

The agent receives the same substantive task description across compared configurations.

The benchmark should provide information that a normal developer would reasonably receive.

Avoid giving one system additional implementation hints.

The agent should be free to:

- inspect files
- search the repository
- read documentation
- execute tests
- execute shell commands
- modify files
- inspect failures
- iterate
- validate its repair

The operator should not manually guide the agent toward the solution.

```text
Same repository
      +
Same task
      +
Same validation
      ↓
Different local AI configuration
      ↓
Compare outcome + trajectory
```

---

# 🧠 8. Model Configuration

The initial benchmark uses:

> **Qwen3.6-27B**

Record the exact:

- model identifier
- model revision
- quantization
- model format
- context length
- sampling parameters
- temperature
- top-p
- top-k, where applicable
- repetition settings, where applicable
- MTP configuration

The model should remain constant when the experimental question is hardware/runtime comparison.

---

# ⚡ 9. Inference Runtime

The inference runtime is part of the experimental configuration.

Current primary configurations:

| Platform | Runtime |
|---|---|
| 🟢 Windows + RTX 5060 Ti | llama.cpp |
| 🔵 Mac + M4 Pro | oMLX / MLX |

Record:

- runtime name
- version/commit
- build configuration
- acceleration backend
- quantization
- context configuration
- batching configuration
- cache configuration
- Flash Attention configuration
- MTP configuration
- other performance-relevant options

> **A benchmark result is not a hardware-only result when the inference runtime differs.**

---

# 💻 10. Hardware Configuration

Each benchmark machine must be documented.

At minimum:

- CPU
- GPU/SoC
- GPU VRAM or unified memory
- system RAM
- operating system
- OS version
- driver/runtime versions
- storage
- relevant power/thermal configuration

Current systems:

### 🟢 RTX

```text
NVIDIA RTX 5060 Ti
16 GB VRAM
Windows 11 Pro
Intel i5-8600
50 GB system RAM
llama.cpp
```

### 🔵 M4 Pro

```text
Apple M4 Pro
64 GB unified memory
macOS
oMLX / MLX
```

The exact configuration must be captured again at each benchmark run.

---

# 🧪 11. Benchmark Execution

The standard execution lifecycle is:

```text
       🧹 Prepare Environment
                │
                ▼
       🔖 Checkout Revision
                │
                ▼
       🧪 Verify Baseline
                │
                ▼
         ⏱️ Start Timer
                │
                ▼
          🤖 Start Agent
                │
                ▼
          📋 Provide Task
                │
                ▼
        🔎 Agent Investigates
                │
                ▼
          ✏️ Agent Edits
                │
                ▼
        🔧 Agent Uses Tools
                │
                ▼
          🧪 Agent Tests
                │
          ┌─────┴─────┐
          ▼           ▼
        Pass        Fail
          │           │
          │       🔍 Diagnose
          │           │
          │       🔄 Recover
          │           │
          └─────┬─────┘
                ▼
          ✅ Final Validation
                │
                ▼
          📦 Freeze Evidence
```

The full execution trajectory should be captured whenever technically possible.

---

# ⏱️ 12. Timing Methodology

## Start boundary

The benchmark timer begins when the coding agent receives the benchmark task and begins execution.

The measured interval is:

```text
START
 │
 ├── agent reasoning
 ├── repository exploration
 ├── tool calls
 ├── code changes
 ├── test execution
 ├── debugging
 └── recovery
 │
END
```

Normally excluded:

- model download
- initial dependency installation
- repository cloning
- machine boot
- manual environment preparation

These are infrastructure preparation costs unless a particular experiment explicitly includes them.

---

## End boundary

A successful run ends when:

1. the agent has completed the repair;
2. required validation succeeds;
3. the final repository state is captured.

A failed run ends when:

- the agent cannot complete the repair;
- the execution limit is reached;
- the agent becomes unrecoverable;
- required validation continues to fail;
- or the benchmark is otherwise terminated according to the predefined protocol.

---

# ⚠️ 13. Timing Data Integrity

LCAB preserves both:

```text
START_TIMESTAMP
END_TIMESTAMP
```

and derived:

```text
WALL_TIME_SECONDS
```

The timestamps are authoritative raw evidence.

If a derived wall-time field is malformed or suspect, reconstruct elapsed time from the preserved start/end timestamps during processing.

Do not overwrite the raw timing artifact.

This is particularly important for the initial benchmark because the current raw timing collection contains incorrectly formatted elapsed-time fields.

---

# 🧪 14. Baseline Validation

Baseline validation is essential.

```text
Baseline failure
      ≠
Agent-induced failure
```

Before the agent starts:

1. run the relevant test command;
2. record the command;
3. record the exit code;
4. record failing tests;
5. preserve the output.

A baseline failure must be reported as a benchmark anomaly rather than silently attributed to the agent.

---

# 🚨 15. Environment Failure vs Repair Failure

Validation failures must be classified.

| Result | Classification |
|---|---|
| Required tests pass | 🟢 Validation success |
| Tests fail because of repair | 🔴 Repair failure |
| Test executable unavailable | 🟡 Environment failure |
| Baseline already fails | 🟡 Baseline failure |
| Test infrastructure crashes | 🟡 Validation anomaly |
| Evidence incomplete | ⚪ Incomplete |

For example:

```text
pytest: command not found
```

is not equivalent to:

```text
pytest
FAILED test_autonomous_loop.py
```

The initial Mac benchmark contains the former type of collection issue, so it must not automatically be presented as a software-repair failure.

---

# 📊 16. Primary Metrics

## 16.1 🏆 Repair Success Rate

```text
Repair Success Rate =
Successful Repairs / Total Valid Runs × 100
```

This is a primary quality metric.

---

## 16.2 ⏱️ Time to Successful Repair

Wall-clock time from agent start until successful validation.

For multiple runs, report:

- median
- mean
- minimum
- maximum
- percentiles when sample size supports them

Median should receive particular attention because a small number of very long runs can distort the mean.

---

## 16.3 🚀 Successful Repairs per Hour

A practical productivity metric:

```text
Successful Repairs / Hour
```

This should always be presented alongside success rate and repair time.

---

# 🧮 17. Secondary Metrics

## Token consumption

Record:

- input tokens
- output tokens
- total tokens
- tokens per model call
- tokens per successful repair

Token consumption helps explain the computational cost of a repair.

---

## Inference throughput

Record where available:

- prompt-processing tokens/sec
- generation tokens/sec

These are **model/runtime metrics**, not the primary software-engineering outcome.

LCAB explicitly distinguishes:

```text
⚡ Model throughput
```

from:

```text
🔧 End-to-end coding-agent performance
```

---

## Model calls

Record:

- total model calls
- successful calls
- failed calls
- retries
- calls before first useful tool action
- calls before successful repair

---

## Tool calls

Record:

- total tool calls
- shell commands
- file reads
- searches
- test executions
- file modifications
- other available tool operations

Tool-call counts can explain differences between systems using the same model.

---

# 🤖 18. Agent-Trajectory Metrics

The agent session is part of the benchmark evidence.

Useful trajectory measurements include:

### 🔎 Time to first useful action

How long the agent spends before performing a meaningful repository action.

### 🔄 Iteration count

Number of meaningful repair iterations.

### 🧪 Test attempts

Number of test executions.

### 🛠️ Recovery events

Failures followed by successful diagnosis/recovery.

### 🔁 Failed trajectories

Repeated ineffective actions, loops, or failure to converge.

### 📚 Context behavior

Context growth, compaction, reset, or other context-management events where available.

This layer becomes especially important when comparing Pi with future OpenHands runs.

---

# 🧪 19. Software-Repair Quality

Passing the immediate test suite is necessary but should not automatically be treated as proof of perfect patch quality.

Where appropriate, inspect:

- required tests
- regression tests
- unintended behavior changes
- unrelated modifications
- modification scope
- code quality
- maintainability
- test coverage

Distinguish:

```text
Functional Success
```

from:

```text
Patch Quality
```

A patch that passes the target test while introducing unrelated regressions should not receive the same qualitative interpretation as a clean repair.

---

# 💾 20. Resource Measurements

Where practical, capture:

- peak GPU VRAM
- peak system RAM
- GPU utilization
- CPU utilization
- memory pressure
- power consumption
- energy consumed

Report resources separately from repair quality.

```text
System A
  ├── Faster repair
  └── Higher memory use

System B
  ├── Slower repair
  └── Lower memory use
```

Both observations are useful; neither should be hidden inside an unexplained composite score.

---

# 🎛️ 21. Controlling Variables

For a controlled comparison, keep constant whenever possible:

- repository
- repository revision
- task description
- model
- model revision
- quantization
- agent instructions
- validation procedure
- maximum runtime
- relevant sampling settings

Change only the variable being studied.

For the primary hardware/runtime comparison:

```text
                Controlled
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
       Task       Model        Agent
        │           │           │
        └───────────┼───────────┘
                    │
                    ▼
              Experimental
                 variables
                    │
              ┌─────┴─────┐
              ▼           ▼
           Hardware     Runtime
```

---

# 🧪 22. Experimental Dimensions

LCAB should explicitly declare the variable under investigation.

## Hardware experiment

```text
Variable:
Hardware

Prefer constant:
Model
Agent
Workload
Context
Runtime, where technically possible
```

## Runtime experiment

```text
Variable:
Inference runtime

Prefer constant:
Hardware
Model
Agent
Workload
```

## Agent experiment

```text
Variable:
Coding agent

Prefer constant:
Hardware
Model
Runtime
Workload
```

## Model experiment

```text
Variable:
Model

Prefer constant:
Hardware
Runtime
Agent
Workload
```

This prevents accidental conclusions caused by changing multiple factors simultaneously.

---

# 🔁 23. Repeated Runs

LLM-based coding agents are nondeterministic.

Therefore:

> **One successful or unsuccessful run should not normally be treated as definitive evidence.**

For important comparisons, execute each task multiple times when practical.

Example:

```text
Task 01
 ├── Run 1
 ├── Run 2
 └── Run 3

Task 02
 ├── Run 1
 ├── Run 2
 └── Run 3
```

Report:

- per-run results
- aggregate results
- variance where appropriate

As the benchmark grows, confidence intervals or other uncertainty estimates can be added.

---

# 🎲 24. Determinism

Distinguish between deterministic and nondeterministic components.

### More deterministic

- repository revision
- task
- test suite
- validation procedure
- hardware
- runtime configuration

### Potentially nondeterministic

- model generation
- agent decisions
- tool ordering
- recovery behavior

Fix random seeds where supported.

If a component cannot be made deterministic, document that limitation rather than claiming exact reproducibility.

---

# 📦 25. Run Evidence Package

Every run should produce an immutable raw evidence package.

Recommended structure:

```text
results/raw/<RUN_ID>/
│
├── metadata.txt
├── git-before.txt
├── diff-before.patch
│
├── pi-version.txt
├── timing.txt
│
├── pi-session/
├── pi-session.jsonl
├── pi-session.html
│
├── tests.txt
├── git-after.txt
├── diff.patch
│
└── anomalies.md
```

Not every artifact is mandatory for every future agent, but the principle is:

> **Preserve raw evidence before processing it.**

---

# 🧾 26. Machine-Readable Run Record

A processed run should have a stable schema.

Conceptually:

```json
{
  "run_id": "20260813-064832-task01-mac-m4-omlx",
  "task_id": "task01",
  "agent": "pi",
  "agent_version": "0.84.1",
  "model": "Qwen3.6-27B",
  "runtime": "oMLX/MLX",
  "hardware": "Apple M4 Pro 64GB",
  "context_window": 55000,
  "mtp": true,
  "success": true,
  "wall_clock_seconds": 0,
  "input_tokens": 0,
  "output_tokens": 0,
  "tool_calls": 0,
  "model_calls": 0,
  "tests_passed": 0,
  "tests_failed": 0
}
```

The actual values must come from raw evidence.

Do not invent missing metrics.

---

# 🏷️ 27. Run Status

Use a controlled vocabulary:

| Status | Meaning |
|---|---|
| 🟢 `SUCCESS` | Repair completed and validation passed |
| 🔴 `FAILURE` | Repair failed |
| 🟠 `TIMEOUT` | Maximum execution time reached |
| 🟡 `ENVIRONMENT_FAILURE` | Environment prevented valid validation |
| 🟡 `BASELINE_FAILURE` | Baseline was already failing |
| ⚪ `INCOMPLETE` | Evidence package incomplete |
| ⚫ `INVALID_FOR_COMPARISON` | Experimental protocol violated |

A failed or invalid run should **not be deleted**.

Preserve it and explain why it is not suitable for a particular comparison.

---

# 🔍 28. Evidence Hierarchy

When derived results and raw evidence disagree, use this hierarchy:

```text
1. Raw repository state
          ↓
2. Raw agent session
          ↓
3. Raw command output
          ↓
4. Run metadata
          ↓
5. Processed metrics
          ↓
6. Human interpretation
```

Derived data must never overwrite raw evidence.

---

# 📊 29. Processing Raw Results

The processing pipeline should be:

```text
results/raw/
      │
      ▼
Parse + Validate
      │
      ▼
Normalize
      │
      ▼
Classify
      │
      ▼
results/processed/
      │
      ▼
Charts / Tables
      │
      ▼
Publication
```

The raw run directory remains unchanged.

For example:

```text
results/raw/
  20260813-064832-task01-mac-m4-omlx/

results/processed/
  task01-mac-m4-omlx.json
```

The processed record must retain the original `run_id`.

---

# ⚖️ 30. Primary RTX vs M4 Experiment

The initial comparison is:

```text
                    Same Task 01
                         │
                         ▼
                  Same baseline
                         │
                         ▼
                  Qwen3.6-27B
                         │
                         ▼
                       Pi
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
       🟢 RTX 5060 Ti          🔵 M4 Pro
       Windows 11 Pro            macOS
       llama.cpp                 oMLX / MLX
       16 GB VRAM                64 GB unified
       55K context               55K context
              │                     │
              └──────────┬──────────┘
                         ▼
                    Compare
```

The primary comparison should focus on:

1. repair outcome;
2. wall-clock repair time;
3. test/validation result;
4. agent trajectory;
5. token consumption;
6. model/tool call behavior;
7. resource usage.

---

# 🧭 31. Current Task 01 Experimental Boundary

Task 01 is a real multi-file software-repair workload involving:

- autonomous optimization-loop behavior;
- parameter propagation;
- workflow sidecar mapping;
- iteration state;
- regression tests;
- validation.

The primary comparison uses the common baseline:

```text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

Primary benchmark branches:

```text
benchmark/task9-rtx5060ti-mtp
benchmark/task9-m4pro-omlx-mtp-55k
```

Separate exploratory branch:

```text
benchmark/task9-m4pro-omlx-mtp-unlimited
```

The 55K RTX/M4 pair is the primary hardware/runtime comparison.

---

# ⚠️ 32. Known Limitations of the Current Dataset

The initial benchmark should be presented transparently.

### Timing

Raw timing files preserve timestamps, but the derived elapsed-time fields are not reliable enough to use blindly.

**Method:** reconstruct elapsed time from preserved start/end timestamps.

### Mac test collection

The current Mac test artifact contains:

```text
pytest: command not found
```

This is an environment/collection issue.

It should be reported separately from software-repair correctness.

### Sample size

The current experiment is small.

Therefore, results should be described as:

> **an initial real-workload benchmark**

rather than a statistically comprehensive characterization of the hardware/runtime landscape.

---

# 📜 33. Publication Standard

Before a metric appears in:

- GitHub README
- benchmark report
- Hugging Face
- Reddit
- Hacker News
- X
- LinkedIn
- research notes

it should be traceable:

```text
Published claim
      │
      ▼
Processed metric
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
      └── final patch
      │
      ▼
Original repository state
```

> **If a published number cannot be traced back to raw evidence, it is not yet a benchmark result.**

---

# 🔬 34. Interpretation Rules

LCAB should avoid claims stronger than the experiment supports.

### Supported example

> “On this Task 01 workload, the tested M4 Pro + oMLX configuration completed the repair faster than the tested RTX 5060 Ti + llama.cpp configuration.”

### Unsupported leap

> “M4 Pro is faster than RTX 5060 Ti for coding agents.”

The second statement requires substantially more controlled workloads and repeated measurements.

Likewise:

```text
Observed:
M4 Pro + oMLX > RTX + llama.cpp
```

does not automatically imply:

```text
M4 Pro hardware > RTX hardware
```

because runtime, model format, operating system, memory architecture, and other configuration details participate in the observed result.

---

# 🧪 35. Quality-Control Checklist

Before accepting a comparison:

```text
☐ Same task
☐ Same task instructions
☐ Same baseline revision
☐ Same model family
☐ Same model revision where possible
☐ Context size verified
☐ MTP verified
☐ Agent version verified
☐ Runtime versions recorded
☐ Hardware recorded
☐ Baseline validation recorded
☐ Start/end timestamps preserved
☐ Timing independently verified
☐ Test output preserved
☐ Final patch preserved
☐ Agent session preserved
☐ Environment anomalies classified
☐ Raw evidence immutable
☐ Derived metrics traceable
☐ Claims limited to measured evidence
```

---

# 🌱 36. Future Expansion

The methodology is designed to grow from the current experiment into a broader benchmark.

Potential dimensions:

```text
                    LCAB
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    Hardware       Runtime       Agent
       │             │             │
   RTX / Mac     llama.cpp       Pi
   Future GPUs   MLX/oMLX     OpenHands
       │             │             │
       └─────────────┼─────────────┘
                     ▼
                   Model
                     │
               Qwen / future
                     │
                     ▼
                  Tasks
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        Bug       Feature    Integration
          │          │          │
          └──────────┼──────────┘
                     ▼
                 Validation
                     │
                     ▼
                📊 Benchmark
```

This structure allows future experiments without changing the fundamental methodology.

---

# 🎯 37. Core Principle

LCAB is not intended to answer:

> **“Which GPU is fastest?”**

It is intended to answer:

> **“Which local AI coding-agent configuration can solve real software-engineering problems effectively, reliably, and efficiently?”**

That distinction is central to the benchmark.

```text
⚡ Token Speed
      +
🧠 Model Capability
      +
🤖 Agent Architecture
      +
🔧 Tool Use
      +
📚 Context Management
      +
💻 Hardware
      +
⚙️ Runtime
      +
🧪 Validation
      │
      ▼
🏆 Real Software-Engineering Performance
```

The benchmark's strongest evidence therefore comes from the **complete repair trajectory and validated outcome**, not from a single inference-throughput number.
