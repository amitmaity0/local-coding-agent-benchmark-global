# Benchmark Methodology

## 1. Objective

The objective of the Local Coding Agent Benchmark is to measure the **end-to-end effectiveness and performance of local AI coding agents when solving real software-repair problems**.

The benchmark is intentionally designed around software engineering outcomes rather than isolated model inference metrics.

The primary research question is:

> **How quickly and reliably can a local coding-agent system solve a real software-repair task?**

A coding-agent system is considered the complete stack:

```text
Hardware
    ↓
Operating System
    ↓
Inference Runtime
    ↓
Model
    ↓
Coding Agent
    ↓
Tool Execution
    ↓
Repository
    ↓
Software Repair
    ↓
Tests
```

Therefore, benchmark results describe the performance of a **specific configuration**, rather than making universal claims about individual hardware components.

For example:

```text
RTX 5060 Ti
    +
Windows
    +
llama.cpp
    +
Qwen3.6-27B
    +
Pi
```

is compared with:

```text
M4 Pro
    +
macOS
    +
oMLX / MLX
    +
Qwen3.6-27B
    +
Pi
```

Future experiments may replace Pi with OpenHands while keeping the underlying benchmark methodology unchanged.

---

# 2. Current Scope

## 2.1 Current Coding Agent

The current benchmark uses:

> **Pi**

Pi is the primary coding agent for the initial benchmark series.

The benchmark will measure how Pi performs when operating against real software repositories and real repair tasks.

Pi-specific behavior, configuration, tool usage, context management, and recovery behavior should be recorded as part of each benchmark run.

---

## 2.2 Future Coding Agent

The methodology is intentionally agent-independent.

A future benchmark series will use:

> **OpenHands**

The OpenHands experiments should use the same benchmark workloads whenever technically possible.

This will allow comparisons such as:

```text
                 Same Workload
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
         Pi                   OpenHands
          │                       │
          ▼                       ▼
      Qwen3.6-27B            Qwen3.6-27B
          │                       │
          ▼                       ▼
    Local Runtime            Local Runtime
          │                       │
          ▼                       ▼
       Hardware                Hardware
```

The objective is not to declare one agent universally superior.

Instead, the benchmark should identify how different agent architectures affect:

* repair success
* repair time
* token consumption
* tool usage
* failure recovery
* resource consumption

---

# 3. Benchmark Unit

The fundamental unit of measurement is a:

> **Software Repair Task**

A benchmark task consists of a repository at a known revision plus a clearly defined software problem.

A task should include:

```text
Repository
    +
Known starting revision
    +
Problem description
    +
Expected behavior
    +
Test suite
    +
Known validation criteria
```

The agent starts from the same repository state for every system being compared.

---

# 4. Task Selection

Tasks should represent realistic software engineering problems rather than artificial model prompts.

Preferred tasks include:

* bugs
* incorrect behavior
* missing functionality
* broken integrations
* regression fixes
* API compatibility problems
* configuration problems
* test failures
* implementation defects
* multi-file repairs

Tasks should require the agent to perform genuine investigation and modification rather than simply generating an isolated code snippet.

---

## 4.1 Task Difficulty

Tasks should span multiple levels of complexity.

### Simple

Examples:

* single-file bug
* straightforward logic error
* obvious test failure

### Moderate

Examples:

* multiple interacting functions
* multi-file modification
* API behavior investigation
* test-driven debugging

### Complex

Examples:

* repository-wide investigation
* ambiguous failure
* multiple iterations
* interaction between several components
* failures requiring diagnosis and recovery

The benchmark should avoid drawing conclusions from only one difficulty level.

---

# 5. Repository Preparation

Every benchmark task must have a deterministic starting state.

Before a run:

1. Clone or restore the repository.
2. Checkout the exact benchmark revision.
3. Reset all working-tree changes.
4. Install required dependencies.
5. Verify that the baseline environment is functional.
6. Run the relevant baseline tests.
7. Record the repository commit.
8. Record the environment configuration.

The initial repository state must be identical for every compared system.

---

# 6. Agent Instructions

The agent should receive the same task description across benchmark configurations.

The task prompt should provide only the information that a normal developer would reasonably receive when assigned the problem.

The benchmark should avoid giving one system additional information that another system does not receive.

Where possible:

```text
Same repository
+
Same task description
+
Same tests
+
Same success criteria
```

The coding agent should be allowed to independently:

* inspect files
* search the repository
* read documentation
* execute tests
* execute shell commands
* modify files
* inspect failures
* iterate on the implementation

The benchmark should not manually guide the agent toward the solution.

---

# 7. Agent Configuration

Every benchmark run must record the complete coding-agent configuration.

For Pi, record at minimum:

* Pi version / commit
* model configuration
* inference endpoint
* system prompt configuration
* tool configuration
* context configuration
* sampling parameters
* timeout configuration
* retry configuration
* permission configuration
* working-directory configuration

Future OpenHands experiments should record the equivalent configuration.

The purpose is to prevent a benchmark result from depending on undocumented agent settings.

---

# 8. Model Configuration

The model configuration must be explicitly recorded.

For the initial benchmark:

> **Qwen3.6-27B**

Record:

* exact model identifier
* model revision
* quantization
* model format
* context length
* inference parameters
* sampling parameters
* temperature
* top-p
* top-k, if applicable
* repetition settings, if applicable
* MTP configuration, if applicable

The model should remain constant when comparing hardware or inference-runtime configurations whenever possible.

---

# 9. Inference Runtime

The inference runtime is considered part of the benchmark configuration.

Initial configurations include:

### NVIDIA / Windows

```text
llama.cpp
```

### Apple Silicon / macOS

```text
oMLX / MLX
```

The benchmark should record:

* runtime name
* runtime version
* commit
* build configuration
* acceleration backend
* quantization
* context configuration
* batch configuration
* cache configuration
* Flash Attention configuration
* MTP configuration
* other performance-related runtime options

Runtime configuration is important because inference performance can change significantly depending on these settings.

Therefore:

> **A benchmark result should never be interpreted as a hardware-only result when the inference runtime differs.**

---

# 10. Hardware Configuration

Each benchmark machine must be documented.

At minimum record:

* CPU
* GPU
* GPU VRAM
* system RAM
* operating system
* OS version
* driver version
* storage type
* power configuration
* thermal configuration

For example:

```text
Hardware
--------
GPU: NVIDIA RTX 5060 Ti
VRAM: 16 GB
System RAM: 60 GB
OS: Windows
Runtime: llama.cpp
Model: Qwen3.6-27B
Agent: Pi
```

and:

```text
Hardware
--------
CPU: Apple M4 Pro
Unified Memory: 64 GB
OS: macOS
Runtime: oMLX / MLX
Model: Qwen3.6-27B
Agent: Pi
```

Exact versions should be captured at the time of each benchmark run.

---

# 11. Benchmark Execution

Each benchmark run begins from a clean repository state.

The general execution sequence is:

```text
Prepare Environment
        ↓
Checkout Benchmark Revision
        ↓
Verify Baseline
        ↓
Start Agent
        ↓
Provide Task
        ↓
Agent Investigates
        ↓
Agent Modifies Repository
        ↓
Agent Runs Tests / Tools
        ↓
Agent Analyzes Results
        ↓
Agent Iterates
        ↓
Final Validation
        ↓
Record Result
```

The benchmark must capture the complete execution trajectory whenever possible.

---

# 12. Start and End Conditions

## 12.1 Start

The timer begins when the coding agent receives the benchmark task and begins execution.

The exact timing mechanism should be documented and applied consistently.

The following should not be included in the measured repair time unless explicitly defined as part of the experiment:

* model download
* initial dependency installation
* repository cloning
* machine boot
* manual environment preparation

These are infrastructure preparation costs rather than agent execution costs.

---

## 12.2 Successful End

A successful run ends when:

1. The agent has completed its repair.
2. The repository satisfies the benchmark's validation criteria.
3. Required tests pass.
4. The agent's final state is recorded.

The benchmark should use automated validation whenever possible.

---

## 12.3 Failed End

A run is considered unsuccessful when:

* the agent cannot complete the repair,
* the allowed execution limit is reached,
* the context becomes unusable,
* the agent enters an unrecoverable loop,
* required tests continue to fail,
* the agent produces an invalid implementation,
* or the benchmark's maximum runtime is exceeded.

Failures should be recorded rather than manually corrected.

---

# 13. Time Limits

Each task should have a predefined maximum execution time.

For example:

```text
Maximum wall-clock time: TBD
```

The exact value should be selected before large-scale benchmarking and applied consistently.

The benchmark should avoid extending the time limit selectively for systems that are performing poorly.

---

# 14. Primary Metrics

## 14.1 Repair Success Rate

The percentage of benchmark tasks successfully repaired.

```text
Repair Success Rate =
Successful Repairs / Total Tasks × 100
```

This is one of the most important quality metrics.

---

## 14.2 Time to Successful Repair

Wall-clock time from agent start until successful validation.

This measures actual end-to-end coding-agent productivity.

Report:

* mean
* median
* minimum
* maximum
* percentile values where sample size permits

Median should be emphasized because a small number of very long runs can distort the mean.

---

## 14.3 Successful Repairs per Hour

A practical productivity metric:

```text
Successful Repairs / Hour
```

This can provide an intuitive comparison between systems.

It should always be presented together with the underlying success rate and repair-time measurements.

---

# 15. Secondary Metrics

## 15.1 Token Consumption

Record:

* input tokens
* output tokens
* total tokens
* tokens per model call
* tokens per successful repair

This helps determine whether a system achieves better results because it is genuinely more efficient or simply because it consumes more inference.

---

## 15.2 Generation Throughput

Record:

* generation tokens/sec
* prompt-processing tokens/sec

These are important model/runtime measurements but are **not the primary benchmark outcome**.

The benchmark explicitly distinguishes:

> **Model throughput**

from:

> **End-to-end coding-agent performance**

---

## 15.3 Model Calls

Record:

* total model calls
* successful calls
* failed calls
* retries
* calls before first tool action
* calls before successful repair

This helps characterize agent behavior.

---

## 15.4 Tool Calls

Record:

* total tool calls
* shell commands
* file reads
* file searches
* test executions
* file modifications
* other available tool operations

Tool-call counts can help explain why two agents with identical models produce different end-to-end performance.

---

# 16. Agent Behavior Metrics

The benchmark should capture the agent's trajectory where technically possible.

Important measurements include:

### Time to First Useful Action

How long the agent spends reasoning before taking its first meaningful repository action.

### Iteration Count

Number of meaningful repair iterations.

### Test Attempts

Number of times tests are executed during the repair.

### Recovery Events

Number of times the agent encounters a failure and successfully recovers.

### Failed Trajectories

Runs where the agent becomes stuck, repeatedly performs ineffective actions, or otherwise fails to converge.

### Context Resets

Number of times the agent must restart or reset its working context.

These measurements become particularly important when comparing different coding-agent architectures.

---

# 17. Software Repair Quality

A successful test run is necessary but may not always be sufficient to determine patch quality.

Where appropriate, evaluate:

* required tests passing
* existing regression tests passing
* unintended behavior changes
* unnecessary code modifications
* modification scope
* code quality
* maintainability
* test coverage changes

The benchmark should distinguish:

```text
Functional Success
```

from:

```text
Patch Quality
```

A patch that passes the immediate test but introduces unrelated regressions should not receive the same qualitative assessment as a clean repair.

---

# 18. Resource Measurements

Where practical, collect:

* peak GPU VRAM
* peak system RAM
* GPU utilization
* CPU utilization
* memory pressure
* power consumption
* energy consumed

Resource measurements should be reported separately from repair quality.

For example:

```text
System A:
    Faster repair
    Higher memory usage

System B:
    Slower repair
    Lower memory usage
```

Both facts are useful, but they should not be collapsed into a single unexplained score.

---

# 19. Controlling Variables

The benchmark should keep the following constant whenever the experimental question allows it:

* repository
* repository revision
* task description
* model
* model revision
* quantization
* coding-agent instructions
* benchmark validation
* maximum runtime
* sampling parameters

Variables intentionally being tested may change.

For example, a hardware comparison may change:

```text
Hardware
Inference Runtime
```

while keeping:

```text
Model
Agent
Workload
```

constant.

---

# 20. Experimental Dimensions

The benchmark should clearly identify which variable is being investigated.

Examples:

## Hardware Experiment

```text
Variable:
Hardware

Constant:
Model
Agent
Runtime where possible
Workload
```

## Runtime Experiment

```text
Variable:
Inference Runtime

Constant:
Hardware
Model
Agent
Workload
```

## Agent Experiment

```text
Variable:
Coding Agent

Constant:
Hardware
Model
Workload
```

## Model Experiment

```text
Variable:
Model

Constant:
Hardware
Runtime
Agent
Workload
```

This prevents accidental conclusions caused by changing several variables simultaneously.

---

# 21. Repeated Runs

LLM-based agents are nondeterministic.

Therefore, a single successful or unsuccessful run should not normally be treated as definitive evidence.

For important comparisons, run each task multiple times when practical.

For example:

```text
Task 01
    Run 1
    Run 2
    Run 3

Task 02
    Run 1
    Run 2
    Run 3

...
```

Report both:

* per-run results
* aggregate results

Where sample size permits, report variance or confidence intervals.

---

# 22. Determinism

The benchmark should distinguish between:

### Deterministic components

* repository revision
* test suite
* benchmark task
* validation procedure
* hardware configuration

and:

### Nondeterministic components

* model generation
* agent decisions
* tool ordering where applicable
* recovery behavior

Random seeds should be fixed where supported.

If a component cannot be made deterministic, the benchmark should document that limitation rather than claiming exact reproducibility.

---

# 23. Benchmark Run Record

Every run should produce a machine-readable record.

A conceptual record may contain:

```json
{
  "task_id": "example-001",
  "agent": "pi",
  "model": "Qwen3.6-27B",
  "runtime": "llama.cpp",
  "hardware": "RTX 5060 Ti 16GB",
  "os": "Windows",
  "success": true,
  "wall_clock_seconds": 1234,
  "input_tokens": 100000,
  "output_tokens": 12000,
  "generation_tok_per_sec": 45.2,
  "model_calls": 18,
  "tool_calls": 37,
  "test_attempts": 4,
  "peak_vram_gb": 15.2
}
```

The exact schema will evolve as the benchmark implementation develops.

---

# 24. Raw Data

Raw benchmark data should be retained.

Do not publish only aggregated numbers.

Whenever possible, preserve:

* raw agent logs
* model usage statistics
* tool-call logs
* test results
* timing data
* system metrics
* final patches
* benchmark metadata

This allows independent analysis and helps identify anomalies.

---

# 25. Result Aggregation

Results should be aggregated at multiple levels.

## Task Level

```text
Task → individual run
```

## System Level

```text
System → all tasks
```

## Workload Level

```text
Workload category → all applicable tasks
```

This allows questions such as:

> Does the RTX configuration perform better overall?

and:

> Does it perform better specifically on multi-file debugging tasks?

---

# 26. Outlier Handling

Outliers should not be silently removed.

Potential causes include:

* transient system load
* network problems
* dependency installation issues
* runtime crashes
* agent loops
* model server failures
* unexpected repository behavior

Every excluded run should have a documented reason.

The default approach should be:

> **Keep the raw observation and explain the anomaly.**

---

# 27. Failure Classification

Failed runs should be classified when possible.

Suggested categories:

```text
MODEL_FAILURE
AGENT_FAILURE
TOOL_FAILURE
CONTEXT_LIMIT
RUNTIME_FAILURE
TEST_FAILURE
TIMEOUT
RESOURCE_LIMIT
ENVIRONMENT_FAILURE
UNKNOWN
```

This is especially important for local systems because a failure may not indicate a weakness in the underlying model.

For example:

```text
Context limit exceeded
```

is materially different from:

```text
Model generated an incorrect repair
```

---

# 28. Context Limit Analysis

Context length is an important variable for local coding agents.

The benchmark should record:

* configured context length
* peak context usage
* context usage at failure
* number of context resets
* whether context exhaustion caused failure
* time spent processing large contexts

This enables future experiments such as:

> **How does context length affect real software-repair success?**

---

# 29. MTP Analysis

If Multi-Token Prediction (MTP) is enabled, record it explicitly.

Compare:

```text
MTP Enabled
```

versus:

```text
MTP Disabled
```

when conducting an MTP experiment.

Measure:

* generation throughput
* total tokens
* wall-clock repair time
* model calls
* repair success rate
* resource consumption

The key question is not simply:

> Did MTP increase tokens/sec?

but:

> **Did MTP improve real end-to-end coding-agent performance?**

---

# 30. Agent Comparison: Pi vs OpenHands

When OpenHands is introduced, the benchmark should reuse the same workload definitions.

Conceptually:

```text
                    Same Task
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
           Pi                OpenHands
            │                     │
            ▼                     ▼
      Same Model              Same Model
            │                     │
            ▼                     ▼
       Same Hardware          Same Hardware
            │                     │
            ▼                     ▼
        Same Tests             Same Tests
            │                     │
            └──────────┬──────────┘
                       ▼
                 Compare Results
```

However, the benchmark should recognize that Pi and OpenHands may have fundamentally different agent architectures.

Therefore, the goal is not to force identical internal behavior.

Instead, compare their externally observable outcomes under equivalent task conditions.

---

# 31. Cross-Agent Fairness

When comparing Pi and OpenHands:

* use the same repository revision
* use the same task description
* use the same model where possible
* use equivalent context limits
* use equivalent execution limits
* use equivalent tool permissions
* use equivalent validation criteria

Agent-specific configuration should remain native to each agent where necessary.

The benchmark should document any unavoidable differences.

---

# 32. What the Benchmark Does Not Claim

The benchmark does **not** attempt to establish that:

* one GPU is universally faster than another
* one CPU is universally better for AI
* one inference runtime is universally superior
* one coding agent is universally superior
* one model is universally better
* benchmark results apply to every repository
* a single run represents general model capability

Instead, results should be interpreted as:

> **Performance of a specific local coding-agent configuration on a defined real-world software-repair workload.**

---

# 33. Primary Reporting Format

A benchmark report should prioritize results in this order:

### 1. Repair Success

```text
Did the agent solve the task?
```

### 2. Time to Success

```text
How long did it take?
```

### 3. Repair Efficiency

```text
How many successful repairs can the system perform per unit time?
```

### 4. Resource Consumption

```text
How much compute and memory did it require?
```

### 5. Agent Behavior

```text
How many tokens, calls, iterations, and recoveries were required?
```

### 6. Model Throughput

```text
How fast did the inference engine generate tokens?
```

This ordering is intentional.

---

# 34. Example Benchmark Summary

A published experiment might ultimately look like:

| Metric                  | RTX 5060 Ti + Pi | M4 Pro + Pi |
| ----------------------- | ---------------: | ----------: |
| Tasks                   |               20 |          20 |
| Successful repairs      |               17 |          15 |
| Success rate            |              85% |         75% |
| Median repair time      |          8.4 min |    10.1 min |
| Successful repairs/hour |              6.1 |         4.8 |
| Median output tokens    |            9,200 |       8,700 |
| Generation tok/s        |               48 |          32 |
| Median model calls      |               16 |          18 |
| Median tool calls       |               31 |          34 |
| Peak memory             |              TBD |         TBD |

The numbers above are **illustrative only** and must not be treated as benchmark results.

---

# 35. Reporting Negative Results

Negative results are valuable.

If an optimization increases generation throughput but does not reduce end-to-end repair time, report it.

For example:

```text
MTP increased generation throughput by X%

but:

Median repair time changed by Y%
Repair success changed by Z%
```

This is more informative than reporting only the improvement in tokens/sec.

---

# 36. Reproducibility Checklist

Before publishing a benchmark result, verify that the following are available:

* [ ] Hardware configuration
* [ ] Operating system version
* [ ] GPU driver version
* [ ] Inference runtime version
* [ ] Runtime configuration
* [ ] Model identifier
* [ ] Model revision
* [ ] Quantization
* [ ] Context configuration
* [ ] Sampling configuration
* [ ] Coding-agent version
* [ ] Coding-agent configuration
* [ ] Repository commit
* [ ] Benchmark task definition
* [ ] Validation procedure
* [ ] Maximum execution time
* [ ] Raw results
* [ ] Final success/failure state
* [ ] Relevant logs
* [ ] Known anomalies

---

# 37. Benchmark Evolution

The benchmark will evolve in stages.

## Phase 1 — Pi

Current focus:

```text
Pi
+
Qwen3.6-27B
+
Local inference
+
Real software-repair workloads
```

The initial experiments focus on comparing local hardware/runtime configurations.

---

## Phase 2 — Expanded Pi Experiments

Potential experiments:

```text
MTP
Context Length
Quantization
Runtime Configuration
Agent Configuration
Failure Recovery
```

---

## Phase 3 — OpenHands

Introduce:

```text
OpenHands
+
Same Benchmark Workloads
+
Same Models
+
Comparable Local Hardware
```

This enables direct study of how coding-agent architecture affects local software-repair performance.

---

## Phase 4 — Broader Benchmark

Potential future dimensions:

```text
Multiple Models
Multiple Agents
Multiple Runtimes
Multiple GPUs
Multiple Apple Silicon Systems
Multiple Repository Types
Multiple Task Difficulties
```

The benchmark should retain the same core task and measurement definitions as it expands.

---

# 38. Core Principle

The benchmark can be summarized by one principle:

> **Measure what the developer ultimately cares about: successful software repair.**

Tokens per second, prompt processing speed, memory usage, context size, MTP performance, and hardware utilization are all valuable measurements.

But they are supporting measurements.

The primary outcome is:

```text
                    Real Task
                       ↓
                  Coding Agent
                       ↓
                  Investigation
                       ↓
                   Iteration
                       ↓
                    Testing
                       ↓
                  Successful
                    Repair
                       ↓
                Time + Quality
```

The benchmark therefore treats:

> **End-to-end successful software repair**

as the central measure of local coding-agent performance.

---

# 39. Research Direction

The long-term objective is to build a practical benchmark for answering:

> **What combination of model, coding agent, inference runtime, and consumer hardware provides the best local software-engineering performance?**

The benchmark begins with:

```text
Pi
+
Qwen3.6-27B
+
llama.cpp / MLX
+
RTX 5060 Ti / M4 Pro
+
Real Software Repairs
```

and is designed to expand to:

```text
Pi
OpenHands
Other Coding Agents
        +
Multiple Models
        +
Multiple Runtimes
        +
Multiple Hardware Platforms
        +
Real Software-Repair Workloads
```

The benchmark's purpose is not to produce a single permanent winner.

It is to provide **transparent, reproducible evidence about what actually makes a local coding agent effective.**
