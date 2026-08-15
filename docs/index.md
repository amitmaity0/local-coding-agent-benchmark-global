---
layout: default
title: Local Coding Agent Benchmark
description: Real-world benchmarking of local AI coding agents on software-repair workloads.
---

# 🤖 Local Coding Agent Benchmark

> **Measuring local AI coding agents on real software-repair workloads.**

LCAB — the **Local Coding Agent Benchmark** — is an experimental benchmark project focused on measuring the complete journey from local model inference to a working software repair.

Instead of evaluating coding agents only with tokens/second or synthetic coding prompts, LCAB uses **real repository-level repair tasks** and records the agent trajectory, tool usage, context processing, validation, and wall-clock completion time.

---

## 🔬 Featured Research

### Task 01 — RTX 5060 Ti vs M4 Pro at 55K Context

**Pi 0.84.1 + Qwen3.6-27B on a real `ai_video_optimization_app` repair**

| | 🟢 RTX 5060 Ti | 🔵 M4 Pro |
|---|---:|---:|
| Inference runtime | llama.cpp | oMLX / MLX |
| Agent | Pi 0.84.1 | Pi 0.84.1 |
| Model | Qwen3.6-27B 4.5bpw-pure GGUF | Qwen3.6-27B oQ4-MTP |
| Context target | 55K | 55K |
| Wall time | **31m 01s** | **118m 51s** |
| Tool calls | **80** | **121** |
| Total tokens | **2.16M** | **4.15M** |

### ⚡ Headline result

> **The observed wall-clock ratio was approximately 3.83× in favor of the RTX configuration.**

The two agents nevertheless converged on essentially the same engineering solution while following substantially different trajectories.

[**Read the complete Task 01 research report →**](research/task01-rtx5060ti-vs-m4pro)

---

## 🎯 What LCAB Measures

LCAB treats a coding-agent benchmark as an end-to-end systems measurement:

```text
┌─────────────────────────────┐
│          HARDWARE           │
│ GPU / CPU / VRAM / RAM      │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         INFERENCE           │
│ runtime / model / context   │
│ caching / generation        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│           AGENT             │
│ messages / tools / retries  │
│ context / trajectory        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       SOFTWARE REPAIR       │
│ patch / tests / correctness │
│ wall-clock completion       │
└─────────────────────────────┘
```

The benchmark records measurements such as:

- ⏱️ Wall-clock completion time
- 💬 Agent messages
- 🔧 Tool calls
- 📥 Input and cached-input tokens
- 📤 Output tokens
- 🧠 Total context processed
- 🧪 Validation and test results
- 📝 Repository changes and patches
- 📦 Raw agent-session evidence

The objective is not to reduce these dimensions to a single opaque score. The raw measurements are preserved so that the results can be independently inspected.

---

## 🧪 Task 01 at a Glance

The first LCAB experiment used a real software-repair workload involving propagation of the `steps` parameter through an autonomous optimization workflow.

The required path was:

```text
Experiment.steps
       │
       ▼
Engine.generate()
       │
       ▼
WorkflowLoader.set_steps()
       │
       ▼
Sidecar-aware mapping
       │
       ▼
LTX scheduler node 206
       │
       ▼
Workflow input
```

Both local coding-agent configurations independently converged on essentially the same core repair architecture.

The major difference was the **trajectory used to reach the repair**.

---

## 💻 Benchmark Configurations

### 🟢 Windows + RTX 5060 Ti

```text
Windows 11
    │
    ▼
Intel i5-8600
    │
    ▼
NVIDIA RTX 5060 Ti
16 GB VRAM
    │
    ▼
llama.cpp
    │
    ▼
Qwen3.6-27B 4.5bpw-pure GGUF
    │
    ▼
Pi 0.84.1
    │
    ▼
55K context
```

### 🔵 macOS + M4 Pro

```text
macOS
    │
    ▼
Apple M4 Pro
64 GB unified memory
    │
    ▼
oMLX / MLX
    │
    ▼
Qwen3.6-27B oQ4-MTP
    │
    ▼
Pi 0.84.1
    │
    ▼
55K context
```

> **Experimental boundary:** Task 01 compares two complete configurations. It is not a pure hardware-only benchmark. Hardware, operating system, inference runtime, model representation, and memory architecture all differ.

---

## 📊 The First Result

The key measurements from Task 01 are:

```text
                         RTX              M4

Wall time              31m 01s         118m 51s
Messages                   166              237
Tool calls                  80              121
Input tokens            2.12M            4.11M
Output tokens           36.3K            39.0K
Total tokens             2.16M            4.15M
```

The M4 trajectory recorded:

```text
+43% messages
+51% tool calls
+94% input tokens
+92% total tokens
```

while output-token volume differed by only approximately 8%.

This is one of the reasons LCAB treats **agent trajectory** as an important benchmark dimension alongside inference performance.

---

## 🧭 Research Direction

The first experiment leads to a broader question:

> **How efficiently does a local coding-agent stack transform model inference, context, tool interactions, and repository exploration into a correct software repair?**

Future LCAB experiments are intended to investigate:

### 🔁 Repeatability

Run identical repairs multiple times on each system and measure variance.

### 📐 Context scaling

Compare:

```text
16K
32K
55K
```

and measure how context size affects trajectory and wall time.

### ⏱️ Per-turn trajectory analysis

Capture:

```text
turn
timestamp
tool
input tokens
cached tokens
output tokens
context size
elapsed time
test activity
```

to identify where time accumulates.

### 🔬 More real repair tasks

Expand beyond a single task so that conclusions are based on multiple independent software repairs.

### 🤖 More local coding agents

Apply the same methodology to additional local coding-agent systems, including OpenHands.

---

## 📚 Documentation

### Research

- [**Task 01 — RTX 5060 Ti vs M4 Pro at 55K Context**](research/task01-rtx5060ti-vs-m4pro)

### Source Repository

The complete benchmark source, methodology, raw evidence, analysis, and supporting artifacts are maintained in the GitHub repository:

[**amitmaity0/local-coding-agent-benchmark-global →**](https://github.com/amitmaity0/local-coding-agent-benchmark-global)

---

## 🙏 Model Credits

The RTX benchmark uses the **Qwen3.6-27B 4.5bpw-pure GGUF** published by **huytd189** on Hugging Face:

[**Qwen3.6-27B-pure-GGUF →**](https://huggingface.co/huytd189/Qwen3.6-27B-pure-GGUF)

The benchmark used the published GGUF without modifying the model weights.

**Upstream model:** [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B)

Many thanks to **huytd189** for making the GGUF release available for local inference and benchmarking.

---

## ⚠️ Experimental Status

Task 01 is the first LCAB real-workload experiment and currently represents **one software-repair task and one recorded run per configuration**.

It should therefore be interpreted as an initial systems comparison, not as a statistically general hardware ranking.

The benchmark intentionally preserves limitations and evidence boundaries rather than hiding them. The next experiments will add repeated runs, context scaling, per-turn analysis, and additional real repair workloads.

---

## 🔗 Project

**Local Coding Agent Benchmark (LCAB)**

Real software.  
Real local models.  
Real agent trajectories.  
Reproducible evidence.

[**View the GitHub repository →**](https://github.com/amitmaity0/local-coding-agent-benchmark-global)

