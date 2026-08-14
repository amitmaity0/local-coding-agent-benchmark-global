# 🧪 Local Coding Agent Benchmark

> **Benchmarking local AI coding agents using real software-repair workloads**

[![Status](https://img.shields.io/badge/status-experimental-orange)](./)
[![Agent](https://img.shields.io/badge/agent-Pi%200.84.1-blue)](./)
[![Model](https://img.shields.io/badge/model-Qwen3.6--27B-purple)](./)
[![Context](https://img.shields.io/badge/context-55K-green)](./)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

## 🎯 What is this project?

**Local Coding Agent Benchmark (LCAB)** evaluates local AI coding agents by giving them **real software-repair tasks** and measuring the complete journey from problem statement to working code.

The benchmark is intentionally broader than a traditional LLM throughput test.

Instead of asking only:

> *How many tokens per second can this system generate?*

LCAB asks:

> **How quickly and reliably can a local AI coding agent investigate a real software problem, modify the repository, run tests, recover from failures, and produce a working repair?**

That distinction is the central idea behind this project:

> ## ⚡ Inference speed ≠ coding-agent speed

A coding agent spends time reasoning, reading a repository, invoking tools, editing files, running tests, interpreting failures, and iterating. A system with higher raw generation throughput is not automatically the system that completes a real software-engineering task faster or more reliably.

---

# 🧭 Current Benchmark

The initial benchmark compares two complete local-AI configurations running the same real software-repair workload.

```text
                         🧪 LCAB — Initial Experiment
                                  │
                         Real software repair
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
             🟢 Windows + RTX              🔵 macOS + M4 Pro
                    │                           │
             RTX 5060 Ti 16 GB             M4 Pro + 64 GB
                    │                           │
                llama.cpp                    oMLX / MLX
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                           Qwen3.6-27B
                                  │
                             Pi 0.84.1
                                  │
                              55K context
                                  │
                                  ▼
                         🔧 Software repair
                                  │
                                  ▼
                         🧪 Test validation
                                  │
                                  ▼
                     ⏱ End-to-end performance
```

## 🖥️ Configurations

| Component | 🟢 Windows / RTX | 🔵 macOS / M4 Pro |
|---|---|---|
| Hardware | NVIDIA RTX 5060 Ti | Apple M4 Pro |
| GPU / accelerator memory | 16 GB VRAM | 64 GB unified memory |
| System memory | 60 GB RAM | 64 GB unified memory |
| Operating system | Windows 11 | macOS |
| Inference runtime | llama.cpp | oMLX / MLX |
| Model | Qwen3.6-27B | Qwen3.6-27B |
| MTP | Enabled | Enabled |
| Coding agent | Pi 0.84.1 | Pi 0.84.1 |
| Context window | 55,000 | 55,000 |
| Workload | Real software repair | Same workload |
| Starting repository revision | `9ab2b50` | `9ab2b50` |

The raw run metadata records the Mac configuration as oMLX with `Qwen3.6-27B-oQ4-mtp` and a 55,000-token context. The RTX run records llama.cpp with `Qwen3.6-27B-MTP-4.5bpw-pure.gguf` and the same 55,000-token context. Both runs used Pi 0.84.1.

> ⚠️ **Interpretation:** this is a comparison of complete AI coding-agent configurations. It is not a universal hardware-only benchmark of RTX 5060 Ti versus M4 Pro.

---

# 🔬 Why benchmark real repairs?

Traditional local-LLM benchmarks are useful for measuring things such as:

- 🚀 generation throughput
- 📥 prompt-processing throughput
- 🧠 memory consumption
- 📊 model benchmark scores
- ⚙️ GPU utilization

Those measurements answer important questions about model inference.

They do not necessarily answer the question a developer ultimately cares about:

> **Can the local coding agent actually fix my software problem?**

A real repair trajectory looks more like this:

```text
📋 Understand task
       │
       ▼
🔎 Inspect repository
       │
       ▼
🧠 Reason about problem
       │
       ▼
✏️ Modify code
       │
       ▼
🧪 Run tests / tools
       │
       ▼
📖 Read failures
       │
       ▼
🔄 Iterate / recover
       │
       ├───────────────┐
       │               │
       ▼               │
🧪 Run validation      │
       │               │
       ▼               │
  ❌ Failure ──────────┘
       │
       ▼
  ✅ Successful repair
```

LCAB therefore measures the **entire agent trajectory**, not only the model's token-generation speed.

---

# 📏 What does LCAB measure?

The benchmark organizes measurements into four layers.

### 1. 🧠 Model / inference

Where available:

- input tokens
- output tokens
- total tokens
- prompt-processing tok/s
- generation tok/s
- MTP behavior
- context window
- context consumed
- inference configuration

### 2. 🤖 Agent behavior

- model calls
- tool calls
- iterations
- retries
- test attempts
- recovery events
- failed trajectories
- context resets
- time to first useful action

### 3. 🔧 Software-engineering outcome

These are the primary outcomes:

- repair success / failure
- tests passing / failing
- wall-clock time to successful repair
- final patch
- files modified
- regression behavior
- patch quality

### 4. 💻 System resources

Where available:

- GPU VRAM
- system / unified memory
- GPU utilization
- CPU utilization
- memory pressure
- power consumption
- energy consumption

The benchmark deliberately separates these measurements rather than collapsing everything into a single opaque score.

---

# 🏆 Primary benchmark philosophy

## Successful repair comes first

LCAB prioritizes:

1. **✅ Repair success**
2. **⏱ Wall-clock time to successful repair**
3. **🧪 Tests passing**
4. **🔄 Recovery / iteration behavior**
5. **🪙 Token consumption**
6. **🚀 Raw inference throughput**

A faster inference engine is not automatically better if the coding agent takes longer to reach a correct repair.

A useful conceptual metric is:

```text
             Successful repairs
Repair efficiency = ─────────────────────
                         Time
```

However, LCAB reports the underlying measurements separately so that readers can inspect the evidence rather than relying on a single composite score.

---

# 📦 Benchmark workload

The benchmark uses a real software repository and a real software-repair task.

Each task is intended to contain:

```text
📁 Repository
   +
📌 Known starting revision
   +
📝 Problem description
   +
🎯 Expected behavior
   +
🧪 Validation / test suite
```

The agent starts from the defined repository state and is expected to independently:

- inspect the codebase
- search for relevant implementation
- reason about the problem
- modify files
- execute commands
- run tests
- interpret failures
- iterate toward a repair

The benchmark should avoid manually guiding the agent toward the solution.

---

# 🧪 Initial experiment

The first recorded experiment uses a **MotionForge software-repair workload**.

The two primary runs were captured independently from the same baseline repository revision:

```text
Baseline
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
             │
       ┌─────┴─────┐
       ▼           ▼
   Mac / oMLX   RTX / llama.cpp
      55K           55K
       │             │
       └─────┬───────┘
             ▼
        Compare results
```

The raw benchmark records preserve:

- `git-before.txt`
- `git-after.txt`
- `diff-before.patch`
- `diff.patch`
- Pi session data
- Pi session HTML
- Pi session JSONL
- Pi version
- metadata
- timing information
- test output
- screenshots where captured

This raw evidence is retained so that published conclusions can be traced back to the original runs.

---

# 📊 Initial result status

The repository currently contains raw results for:

| Run | Platform | Runtime | Model | Context | Agent |
|---|---|---|---|---:|---|
| `20260813-064832-task01-mac-m4` | macOS / M4 Pro | oMLX | Qwen3.6-27B-oQ4-mtp | 55K | Pi 0.84.1 |
| `20260813-122237-task01-windows-rtx5060-llama` | Windows / RTX 5060 Ti | llama.cpp | Qwen3.6-27B-MTP-4.5bpw-pure.gguf | 55K | Pi 0.84.1 |

Both raw runs record the same baseline repository commit:

```text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

### ⚠️ Data-quality note

The current raw `timing.txt` files contain a known collection-format problem: the recorded wall-time fields are not valid elapsed-duration values. The start and end timestamps are preserved and can be used to reconstruct elapsed time during result processing.

The Mac `tests.txt` also records an environment error (`pytest: command not found`), so that file is **not treated as the authoritative source for final test results**.

LCAB favors transparent provenance over silently replacing or guessing missing measurements.

> **If a measurement has a collection problem, the benchmark should say so.**

---

# 🧩 Code-change provenance

The corresponding MotionForge benchmark branches are preserved separately from the benchmark repository.

The three benchmark branches are:

```text
benchmark/task9-m4pro-omlx-mtp-55k
benchmark/task9-m4pro-omlx-mtp-unlimited
benchmark/task9-rtx5060ti-mtp
```

The RTX and M4 Pro 55K branches both start from:

```text
repair/node-mapping-template
        │
        ▼
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
        │
   ┌────┴────┐
   ▼         ▼
 RTX       M4 Pro
55K         55K
```

This is important for experimental provenance: the primary hardware comparison is based on independently generated changes from the same starting revision.

The M4 unlimited-context branch is retained as a separate exploratory experiment because its code trajectory differs more substantially from the two 55K runs.

---

# 🧭 How to interpret the benchmark

LCAB compares **complete configurations**, not individual components in isolation.

For example:

```text
🟢 RTX configuration

RTX 5060 Ti
     +
Windows
     +
llama.cpp
     +
Qwen3.6-27B
     +
Pi
     +
55K context
```

versus:

```text
🔵 M4 configuration

M4 Pro
     +
macOS
     +
oMLX / MLX
     +
Qwen3.6-27B
     +
Pi
     +
55K context
```

Therefore, a conclusion such as:

> ❌ "The RTX 5060 Ti is faster than the M4 Pro."

would be too broad for this experiment.

A defensible conclusion is closer to:

> ✅ "Under the tested configuration, Qwen3.6-27B running through llama.cpp on the RTX 5060 Ti produced a different end-to-end software-repair result than the corresponding Qwen3.6-27B configuration running through oMLX on the M4 Pro."

Inference runtime, quantization, context configuration, batching, caching, MTP, and other runtime parameters can materially affect the result.

---

# 🗂️ Repository structure

The benchmark repository separates workload definitions, execution tooling, hardware descriptions, and experimental evidence.

```text
local-coding-agent-benchmark/
│
├── benchmark/
│   ├── ai_video_optimization_app/
│   └── scripts/
│       ├── initialize.sh
│       ├── run_benchmark.sh
│       └── stop_benchmark.sh
│
├── tasks/
│   ├── repair_task_coding_agent.md
│   ├── task01.md
│   └── run-procedure.md
│
├── hardware/
│   ├── m4pro.md
│   └── rtx5060ti.md
│
├── results/
│   ├── charts/
│   ├── processed/
│   └── raw/
│       ├── 20260813-064832-task01-mac-m4/
│       └── 20260813-122237-task01-windows-rtx5060-llama/
│
├── methodology.md
├── README.md
├── LICENSE
└── .gitignore
```

The raw run directories are intended to remain the **evidence layer**.

Processed data and visualizations should be derived from the raw evidence rather than replacing it.

---

# 🔁 Reproducibility model

Every published benchmark result should identify:

| Category | Required information |
|---|---|
| 💻 Hardware | CPU, GPU, memory |
| 🖥️ OS | OS and version |
| 🧠 Model | Exact model identifier / revision |
| 📦 Quantization | Format and quantization |
| ⚙️ Runtime | Runtime, version / commit |
| 🤖 Agent | Agent and version |
| 🧩 Agent config | Relevant settings |
| 📐 Context | Context limit |
| 🚀 MTP | Enabled / disabled |
| 🎛️ Sampling | Relevant sampling settings |
| 📁 Repository | Exact starting commit |
| 🧪 Workload | Task identifier and revision |
| ⏱️ Timing | Start/end and elapsed time |
| 🧪 Validation | Tests and final outcome |
| 📜 Evidence | Session logs and patches |

The objective is simple:

> **A benchmark number should be traceable to an actual experiment.**

---

# 🧠 Research questions

LCAB is intended to investigate questions that conventional inference benchmarks do not fully answer.

### ⚡ Does higher tok/s produce faster software repairs?

Not necessarily.

Agent behavior, tool execution, context processing, and recovery can dominate end-to-end time.

### 🧠 Does additional context improve repair performance?

Large context windows may help agents retain more repository information, but they can also increase prompt-processing work and memory requirements.

### 🚀 Does MTP improve real coding-agent productivity?

A higher generation rate is valuable only if it translates into faster successful repairs.

### 🤖 How much does agent architecture matter?

Different control loops, tool systems, retry strategies, and context-management approaches can cause the same model to behave very differently.

### 💻 What matters more: inference speed or agent efficiency?

The benchmark is designed to measure both.

### 🔄 Can local coding agents become a practical software-engineering tool?

That is the broader question motivating this project.

---

# 🛣️ Roadmap

LCAB is intended to grow into a repeatable experimental framework rather than remain a single hardware comparison.

## Phase 1 — Foundation

- [x] Define end-to-end benchmark philosophy
- [x] Create reproducible benchmark repository
- [x] Define real software-repair workload
- [x] Run initial M4 Pro experiment
- [x] Run initial RTX 5060 Ti experiment
- [x] Preserve raw Pi sessions
- [x] Preserve repository diffs
- [x] Preserve common baseline revision
- [ ] Normalize processed metrics
- [ ] Publish first comparison

## Phase 2 — Runtime / configuration experiments

- [ ] MTP vs non-MTP
- [ ] Context-size comparison
- [ ] llama.cpp configuration experiments
- [ ] oMLX / MLX configuration experiments
- [ ] Quantization comparison
- [ ] Resource-utilization analysis

## Phase 3 — Agent experiments

```text
              Same workload
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
       Pi                 OpenHands
        │                     │
        └──────────┬──────────┘
                   ▼
             Same model
                   │
                   ▼
          Same validation
```

Future work will extend the methodology to **OpenHands**, while keeping the workload and metrics framework as consistent as technically possible.

## Phase 4 — Larger benchmark set

- [ ] Multiple repair tasks
- [ ] Multiple difficulty levels
- [ ] Repeated runs
- [ ] Statistical aggregation
- [ ] Cross-hardware comparisons
- [ ] Cross-runtime comparisons
- [ ] Cross-agent comparisons
- [ ] Public benchmark reports

---

# 📚 Documentation

| Document | Purpose |
|---|---|
| [`methodology.md`](methodology.md) | Detailed benchmark methodology |
| [`tasks/task01.md`](tasks/task01.md) | Current software-repair workload |
| [`tasks/run-procedure.md`](tasks/run-procedure.md) | Benchmark execution procedure |
| [`hardware/m4pro.md`](hardware/m4pro.md) | M4 Pro test environment |
| [`hardware/rtx5060ti.md`](hardware/rtx5060ti.md) | RTX 5060 Ti test environment |
| `results/processed/` | Normalized benchmark measurements |
| `results/charts/` | Visualizations |
| `results/raw/` | Original benchmark evidence |

---

# 🔍 Benchmark principles

### 🧪 Real workloads over synthetic workloads

Whenever practical, benchmark agents on actual software-engineering problems.

### ⏱️ End-to-end performance over isolated throughput

Measure the entire repair trajectory.

### ✅ Success over activity

More tokens, more tool calls, and more iterations do not automatically mean better performance.

### 📜 Evidence over claims

Keep raw sessions, patches, timestamps, and validation output.

### ⚖️ Comparable configurations

Control variables whenever possible and explicitly document variables that change.

### 🔬 Transparent limitations

Do not hide collection errors, failed runs, or environmental anomalies.

### 🔁 Reproducibility

A published result should contain enough information for another researcher or developer to understand and reproduce the experiment.

---

# 🌱 Long-term vision

The goal is to build a practical benchmark for **local AI-assisted software engineering**.

The project is intentionally moving from:

```text
             "How fast is my local LLM?"
                         │
                         ▼
             "How fast is my coding agent?"
                         │
                         ▼
          "How reliably does it repair code?"
                         │
                         ▼
        "How efficiently can it do real
              software engineering?"
```

This creates a benchmark space where hardware, inference runtimes, models, agents, context strategies, and recovery mechanisms can be evaluated using the same underlying principle:

> ## 🔧 Measure what the agent actually accomplishes.

---

# 🤝 Contributions

Contributions are welcome, especially around:

- 🧪 new real-world repair tasks
- 📊 benchmark analysis
- 📈 visualization
- ⚙️ measurement tooling
- 💻 additional hardware
- 🧠 additional models
- 🚀 additional inference runtimes
- 🤖 additional coding agents
- 🔬 independent reproduction

When contributing benchmark results, preserve the complete configuration and raw evidence required to understand the run.

---

# 📄 License

This project is licensed under the **Apache License 2.0**.

See [`LICENSE`](LICENSE) for details.

---

## ⭐ The benchmark in one sentence

> **Local Coding Agent Benchmark measures how quickly and reliably local AI coding agents can perform real software repairs—not merely how many tokens they can generate per second.**

---

## 🙏 Model Attribution & Credits

The RTX 5060 Ti benchmark used the **Qwen3.6-27B 4.5bpw-pure GGUF** published by **huytd189**:

[Qwen3.6-27B-pure-GGUF](https://huggingface.co/huytd189/Qwen3.6-27B-pure-GGUF)

The benchmark used the published GGUF without modifying the model weights.

**Upstream model:** [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B)

The underlying model was developed by the **Qwen Team**. The GGUF repository is a quantized distribution of the upstream Qwen3.6-27B model.

Many thanks to **huytd189** for making the GGUF release available for local inference and benchmarking.