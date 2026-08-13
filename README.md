# Local Coding Agent Benchmark

> **Benchmarking local AI coding agents using real software-repair workloads**

This project evaluates the **end-to-end performance of local coding-agent systems** by measuring how effectively they solve real software-repair tasks.

The primary goal is not to determine which machine produces the most tokens per second.

The goal is to answer a more practical question:

> **How quickly and reliably can a local AI coding agent take a real software problem, investigate it, modify the code, run tests, recover from failures, and produce a working repair?**

---

## Why This Benchmark?

Traditional LLM benchmarks often focus on:

* tokens per second
* prompt processing speed
* model benchmark scores
* GPU utilization
* memory consumption

These measurements are useful, but they do not necessarily predict how well a **coding agent** performs.

A coding agent operates through an iterative loop:

```text
Understand task
     ↓
Inspect repository
     ↓
Reason about problem
     ↓
Modify code
     ↓
Run tests / tools
     ↓
Analyze results
     ↓
Modify again
     ↓
Recover from failures
     ↓
Run tests again
     ↓
Successful repair
```

Therefore:

> **Inference speed ≠ coding-agent speed**

A faster model runtime can still produce a slower or less reliable coding agent if it requires more iterations, generates more tokens, fails to recover from errors, or produces incorrect patches.

This benchmark measures the complete workflow.

---

## Initial Benchmark Configuration

The initial comparison focuses on two consumer-local AI systems running the same class of coding workload.

| Component         | Windows System           | Mac System            |
| ----------------- | ------------------------ | --------------------- |
| Hardware          | NVIDIA RTX 5060 Ti 16 GB | Apple M4 Pro          |
| System Memory     | 60 GB RAM                | 64 GB unified memory  |
| Operating System  | Windows                  | macOS                 |
| Model             | Qwen3.6-27B              | Qwen3.6-27B           |
| Inference Runtime | llama.cpp                | oMLX / MLX            |
| Coding Agent      | Local coding agent       | Local coding agent    |
| Workload          | Real software repairs    | Same software repairs |

The benchmark is intended to compare **complete configurations**, not isolated hardware components.

For example, the results should be interpreted as:

> Qwen3.6-27B + llama.cpp + RTX 5060 Ti + coding agent

versus:

> Qwen3.6-27B + oMLX/MLX + M4 Pro + coding agent

rather than as a universal claim that one processor or GPU is inherently faster than another.

---

# Benchmark Philosophy

## Primary Metric: Successful Repair per Unit Time

The most important outcome is whether the agent actually fixes the problem.

The benchmark therefore prioritizes:

1. **Repair success**
2. **Wall-clock time to successful repair**
3. **Tests passing**
4. **Number of attempts / recovery cycles**
5. **Total tokens consumed**

Raw inference throughput is treated as a supporting metric.

A system that generates more tokens per second but takes longer to produce a correct repair should not automatically be considered the better coding-agent system.

---

# Metrics

The benchmark collects measurements at several levels.

## 1. Model Performance

Where available:

* Prompt processing tokens/sec
* Generation tokens/sec
* MTP performance / acceptance
* Context window
* Context consumed
* KV-cache usage
* Total input tokens
* Total output tokens

## 2. Agent Performance

The benchmark also measures the behavior of the coding agent:

* Total model calls
* Total generated tokens
* Total tool calls
* Number of iterations
* Number of retries
* Failed trajectories
* Context resets
* Recovery events
* Time to first useful action
* Time to successful repair

## 3. Software-Engineering Performance

These are the most important benchmark outcomes:

* Repair success/failure
* Tests passing/failing
* Final patch quality
* Regression introduced
* Number of files modified
* Number of test attempts
* Successful repair rate
* Median repair time

## 4. Hardware / System Performance

When measurements are available:

* Peak VRAM usage
* Peak system RAM usage
* GPU utilization
* CPU utilization
* Memory pressure
* Power consumption
* Energy consumed

---

# Benchmark Workload

The benchmark uses **real software-repair tasks** rather than purely synthetic token-generation workloads.

Each benchmark task should contain:

```text
Repository
+
Problem description
+
Expected behavior
+
Existing implementation
+
Test suite
```

The agent starts from the repository's initial state and must independently investigate and repair the problem.

A task is considered successful when the required tests pass and the resulting implementation satisfies the task requirements.

---

# Benchmark Execution

Each system should run the same workload under equivalent conditions.

The benchmark should record the complete trajectory:

```text
Task Start
   │
   ├── Model request
   ├── Agent reasoning
   ├── Tool call
   ├── Repository inspection
   ├── Code modification
   ├── Test execution
   ├── Failure / recovery
   ├── Additional model request
   ├── Additional tool calls
   │
   └── Final result
          │
          ├── SUCCESS
          └── FAILURE
```

This makes it possible to analyze not only **whether** a repair succeeded, but **how** the agent reached the result.

---

# Results

Benchmark results will be stored in machine-readable form so that the published numbers can be independently analyzed.

A typical summary will look like:

| Metric                  | RTX 5060 Ti | M4 Pro |
| ----------------------- | ----------: | -----: |
| Repair success rate     |         TBD |    TBD |
| Median repair time      |         TBD |    TBD |
| Mean repair time        |         TBD |    TBD |
| Median generated tokens |         TBD |    TBD |
| Generation tok/s        |         TBD |    TBD |
| Prompt tok/s            |         TBD |    TBD |
| Model calls             |         TBD |    TBD |
| Tool calls              |         TBD |    TBD |
| Test attempts           |         TBD |    TBD |
| Peak VRAM/RAM           |         TBD |    TBD |
| Successful repairs/hour |         TBD |    TBD |

**Results will be populated as the benchmark dataset grows.**

---

# What This Benchmark Is Trying to Discover

The benchmark is designed to investigate questions such as:

### Does higher tokens/sec produce faster repairs?

Not necessarily.

A coding agent may spend its time performing tool calls, running tests, processing large contexts, or recovering from mistakes.

### Does more available memory improve coding-agent performance?

Potentially, particularly for large repositories and long-running agent trajectories.

However, memory capacity alone does not determine repair quality.

### Does MTP improve real coding-agent performance?

The benchmark can measure whether faster generation translates into shorter end-to-end repair times.

### How important is context length?

Large context windows can allow an agent to retain more repository information, but they can also increase prompt-processing costs and memory requirements.

### How important is agent architecture?

The same underlying model can behave very differently depending on the agent's control loop, tool handling, retry strategy, context management, and failure recovery.

---

# Repository Structure

The project is organized around reproducibility:

```text
local-coding-agent-benchmark/
│
├── README.md
├── methodology.md
│
├── benchmark/
│   ├── workloads/
│   ├── scripts/
│   └── runners/
│
├── hardware/
│   ├── rtx5060ti.md
│   └── m4pro.md
│
├── results/
│   ├── raw/
│   ├── processed/
│   └── charts/
│
└── LICENSE
```

The exact structure may evolve as the benchmark framework develops.

---

# Reproducibility

Every published result should document:

* Hardware
* Operating system
* Model
* Model quantization
* Inference runtime
* Runtime version / commit
* Coding-agent version
* Agent configuration
* Context length
* Sampling configuration
* MTP configuration
* Relevant runtime flags
* Repository revision
* Benchmark task revision

The objective is to make results reproducible rather than presenting unexplained benchmark numbers.

---

# Important Interpretation Rule

This benchmark compares **AI coding-agent configurations**, not hardware in isolation.

For example:

> "The RTX 5060 Ti is faster than the M4 Pro."

is **not** a conclusion supported by this benchmark.

A more accurate statement would be:

> "Under this benchmark configuration, Qwen3.6-27B running through llama.cpp on the RTX 5060 Ti achieved better/worse end-to-end software-repair performance than the corresponding Qwen3.6-27B configuration running through oMLX/MLX on the M4 Pro."

Inference configuration can have a significant effect on results, including context settings, batching, caching, Flash Attention, quantization, and other runtime parameters.

---

# Beyond Tokens per Second

The central idea of this benchmark is:

```text
             Traditional Benchmark
                     │
                     ▼
                tokens/sec
                     │
                     │
                     ▼
              Local Agent Benchmark
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    Model Performance       Agent Behavior
          │                     │
          └──────────┬──────────┘
                     ▼
              Software Repair
                     │
                     ▼
          ┌─────────────────────┐
          │  Did it actually    │
          │  fix the problem?   │
          └─────────────────────┘
                     │
                     ▼
              Time to Success
```

The benchmark therefore treats **successful software repair** as the ultimate outcome.

---

# Planned Experiments

The benchmark is intended to grow beyond the initial hardware comparison.

Potential future experiments include:

1. **RTX 5060 Ti vs M4 Pro for real coding-agent workloads**
2. **Qwen3.6-27B MTP vs non-MTP**
3. **Context length vs repair success and repair time**
4. **Different inference runtimes**
5. **Different local coding agents**
6. **Agent failure/restart strategies**
7. **OpenHands vs Pi**
8. **Qwen3.6-27B runtime and quantization comparisons**
9. **Memory usage vs repository size**
10. **What actually determines local coding-agent performance?**

The goal is to build a continuously expanding benchmark rather than a single hardware comparison.

---

# Benchmark Principles

The project follows several principles:

### Real workloads over synthetic workloads

Whenever practical, evaluate agents on actual software-repair tasks.

### End-to-end performance over isolated throughput

Measure the complete agent trajectory rather than only model generation speed.

### Reproducibility over cherry-picked results

Publish configurations, raw measurements, and methodology.

### Success over activity

Generating more tokens or making more tool calls does not constitute better performance.

### Transparent limitations

Benchmark results should clearly state what was and was not controlled.

### Comparable configurations

Keep the model, workload, agent behavior, and benchmark conditions as consistent as possible when comparing systems.

---

# Status

**Early-stage / experimental**

The benchmark methodology and data collection process are still being developed.

Initial focus:

> **Qwen3.6-27B + local coding agent + real software-repair workloads**

on:

> **RTX 5060 Ti 16 GB / Windows / llama.cpp**

versus:

> **M4 Pro 64 GB / macOS / oMLX/MLX**

More workloads, measurements, and systems will be added over time.

---

# Contributing

Contributions are welcome, particularly in the following areas:

* New real-world repair workloads
* Benchmark runners
* Measurement tooling
* Result visualization
* Additional hardware
* Additional inference runtimes
* Additional coding agents
* Independent reproduction of benchmark results

When contributing results, include the complete hardware, model, runtime, agent, and configuration details required to reproduce them.

---

# License

License information will be added as the benchmark repository is finalized.

---

## Research Question

The benchmark can ultimately be summarized by one question:

> **What is the fastest and most reliable way to perform real software engineering locally with an AI coding agent?**

Not:

> **Which machine has the highest tokens/sec?**
