---
title: "Benchmarking Local Coding Agents on Real Software Repairs: RTX 5060 Ti vs M4 Pro at 55K Context"
description: "An end-to-end benchmark of Pi + Qwen3.6-27B on a real ai_video_optimization_app repair workload, comparing Windows + RTX 5060 Ti + llama.cpp with macOS + M4 Pro + oMLX."
tags:
  - coding-agents
  - local-llms
  - benchmarking
  - qwen
  - llama-cpp
  - mlx
  - software-engineering
  - inference
---

# Benchmarking Local Coding Agents on Real Software Repairs: RTX 5060 Ti vs M4 Pro at 55K Context

> **A real software-repair benchmark of Pi + Qwen3.6-27B running locally on two very different machines.**

## Abstract

Local LLM benchmarking usually starts with a familiar question:

> ⚠️ **Experimental status**
>
> This is the first LCAB real-workload experiment and currently represents **one software-repair task and one recorded run per configuration**. The result is an initial systems comparison, not a statistically general hardware ranking.

> **How many tokens per second can this machine generate?**

For coding agents, that is only part of the story.

A coding agent does not simply generate text. It explores a repository, reads files, invokes tools, forms hypotheses, edits code, runs tests, interprets failures, and repeats the loop until it reaches a useful result.

This experiment asks a different question:

> **How does a complete local coding-agent stack perform when it has to repair real software?**

I ran the same ai_video_optimization_app software-repair workload with [Pi 0.84.1](https://github.com/badlogic/pi-mono) and Qwen3.6-27B on two local systems:

- **Windows + NVIDIA RTX 5060 Ti 16 GB + llama.cpp**
- **macOS + Apple M4 Pro 64 GB + oMLX / MLX**

Both runs targeted a **55,000-token context window** and started from the same repository revision.

The recorded result was striking:

| | 🟢 RTX 5060 Ti | 🔵 M4 Pro |
|---|---:|---:|
| Inference runtime | llama.cpp | oMLX / MLX |
| Agent | Pi 0.84.1 | Pi 0.84.1 |
| Model | Qwen3.6-27B 4.5bpw-pure GGUF | Qwen3.6-27B oQ4-MTP |
| Context target | 55K | 55K |
| Wall time | **31m 01s** | **118m 51s** |
| Tool calls | **80** | **121** |
| Messages | **166** | **237** |
| Input tokens | **2.12M** | **4.11M** |
| Output tokens | **36.3K** | **39.0K** |
| Total tokens | **2.16M** | **4.15M** |


The observed wall-clock ratio was approximately **3.83×** in favor of the RTX configuration.
But the more interesting finding is that the two agents converged on essentially the same engineering solution while taking very different paths to get there.

This suggests that **real coding-agent performance is an end-to-end systems property** involving hardware, inference runtime, context processing, agent trajectory, tool interaction, and validation—not simply model tokens/second.

---

## 📚 Contents

- [1. Why benchmark coding agents with real repairs?](#1-why-benchmark-coding-agents-with-real-repairs)
- [2. The LCAB measurement model](#2-the-lcab-measurement-model)
- [3. Experimental setup](#3-experimental-setup)
  - [3.1 Common agent and workload](#31-common-agent-and-workload)
  - [3.2 Windows + RTX 5060 Ti](#32-windows--rtx-5060-ti)
  - [3.3 macOS + M4 Pro](#33-macos--m4-pro)
  - [3.4 An important experimental boundary](#34-an-important-experimental-boundary)
- [4. The workload: a real ai_video_optimization_app repair](#4-the-workload-a-real-aivideooptimizationapp-repair)
- [5. The headline result](#5-the-headline-result)
- [6. But the clock is only part of the story](#6-but-the-clock-is-only-part-of-the-story)
  - [6.1 More interactions](#61-more-interactions)
  - [6.2 Almost twice the input context](#62-almost-twice-the-input-context)
  - [6.3 Output volume was surprisingly similar](#63-output-volume-was-surprisingly-similar)
- [7. Cache behavior](#7-cache-behavior)
- [8. Did both agents actually solve the same problem?](#8-did-both-agents-actually-solve-the-same-problem)
- [9. Solution quality vs trajectory efficiency](#9-solution-quality-vs-trajectory-efficiency)
- [10. Validation](#10-validation)
- [11. Why the 3.83× result should not be over-interpreted](#11-why-the-383-result-should-not-be-over-interpreted)
- [12. Why the trajectory difference matters](#12-why-the-trajectory-difference-matters)
- [13. A useful way to think about coding-agent efficiency](#13-a-useful-way-to-think-about-coding-agent-efficiency)
- [14. What would make the next experiment stronger?](#14-what-would-make-the-next-experiment-stronger)
  - [Experiment A — Repeatability](#experiment-a--repeatability)
  - [Experiment B — Context scaling](#experiment-b--context-scaling)
  - [Experiment C — Per-turn trajectory analysis](#experiment-c--per-turn-trajectory-analysis)
  - [Experiment D — Runtime isolation](#experiment-d--runtime-isolation)
- [15. The next-generation LCAB data model](#15-the-next-generation-lcab-data-model)
- [16. What this benchmark does establish](#16-what-this-benchmark-does-establish)
- [17. What this benchmark does not establish](#17-what-this-benchmark-does-not-establish)
- [18. The broader research question](#18-the-broader-research-question)
- [19. Reproducibility](#19-reproducibility)
- [20. Lessons from the first experiment](#20-lessons-from-the-first-experiment)
  - [Lesson 1 — Measure the repair, not only the model](#lesson-1--measure-the-repair-not-only-the-model)
  - [Lesson 2 — Record the trajectory](#lesson-2--record-the-trajectory)
  - [Lesson 3 — Preserve raw evidence](#lesson-3--preserve-raw-evidence)
  - [Lesson 4 — Separate observation from explanation](#lesson-4--separate-observation-from-explanation)
- [21. Final takeaway](#21-final-takeaway)
- [Appendix A — Task 01 result snapshot](#appendix-a--task-01-result-snapshot)
- [Model Attribution & Credits](#model-attribution--credits)
- [Appendix B — Evidence boundary](#appendix-b--evidence-boundary)

---

## 1. Why benchmark coding agents with real repairs?

Synthetic inference benchmarks are extremely useful.

They can tell us about:

- prompt-processing throughput;
- generation throughput;
- memory consumption;
- context capacity;
- model quality;
- accelerator utilization.

But a software engineer does not normally ask a model to generate 10,000 tokens in isolation.

The actual workflow looks more like this:

```text
                    REAL SOFTWARE TASK
                           │
                           ▼
                    Understand problem
                           │
                           ▼
                    Inspect repository
                           │
                           ▼
                    Form hypothesis
                           │
                           ▼
                      Use tools
                           │
                           ▼
                     Edit code
                           │
                           ▼
                      Run tests
                           │
                    ┌──────┴──────┐
                    │             │
                   PASS          FAIL
                    │             │
                    │             ▼
                    │        Diagnose failure
                    │             │
                    │             └──────► more tools
                    │
                    ▼
               Validate repair
                    │
                    ▼
              Working software
```

Every stage can contribute to the final elapsed time.

A machine with excellent generation throughput can still lose an end-to-end coding-agent workload if the agent:

- takes a longer trajectory;
- invokes more tools;
- processes substantially more context;
- repeats work;
- spends more time waiting on inference;
- or needs more validation cycles.

That is the motivation behind the **Local Coding Agent Benchmark (LCAB)** project.

---

# 2. The LCAB measurement model

LCAB treats a coding-agent benchmark as a stack rather than a single number.

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

The goal is not to collapse all of these dimensions into an opaque score.

Instead, the benchmark preserves the underlying measurements so that readers can ask their own questions.

---

# 3. Experimental setup

## 3.1 Common agent and workload

Both systems used:

- **Pi 0.84.1**
- **Qwen3.6-27B**
- **55,000-token context target**
- the same ai_video_optimization_app repair workload
- the same starting repository revision

The baseline revision was:

```text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

The benchmark repository preserves the run metadata, Pi session artifacts, repository state, patches, timing information, and validation output.

Project repository:

**https://github.com/amitmaity0/local-coding-agent-benchmark-global**

---

## 3.2 Windows + RTX 5060 Ti

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
Qwen3.6-27B 4.5 bpw pure GGUF
    │
    ▼
Pi 0.84.1
    │
    ▼
55K context
```

The recorded model configuration was:

```text
Qwen3.6-27B-MTP-4.5bpw-pure.gguf
```

---

## 3.3 macOS + M4 Pro

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
Qwen3.6-27B-oQ4-MTP
    │
    ▼
Pi 0.84.1
    │
    ▼
55K context
```

The recorded model configuration was:

```text
Qwen3.6-27B-oQ4-MTP
```

---

## 3.4 An important experimental boundary

This is a comparison of **complete configurations**.

It is not a pure hardware benchmark.

Several variables differ between the systems:

```text
Hardware architecture
        +
Operating system
        +
Inference runtime
        +
Model representation / quantization
        +
Memory architecture
```

Therefore this experiment can legitimately answer:

> **How did these two complete local coding-agent configurations perform on this workload?**

It cannot legitimately establish:

> **The RTX 5060 Ti is universally 3.83× faster than the M4 Pro for coding agents.**

That distinction is important.

---

# 4. The workload: a real ai_video_optimization_app repair

The benchmark is based on a real software-repair task in ai_video_optimization_app rather than a synthetic coding prompt.

The defect involved propagation of the `steps` parameter through an autonomous optimization workflow.

Conceptually, the required path was:

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
workflow["206"]["inputs"]["steps"]
```

The repair required the agent to understand several layers of the repository rather than simply modify one obvious line.

The core engineering changes involved:

1. propagating `Experiment.steps` through `Engine.generate()`;
2. making workflow parameter handling sidecar-aware;
3. mapping the LTX-specific `steps` input to node `206`;
4. preserving generic KSampler fallback behavior;
5. adding regression coverage;
6. ensuring optimization changes affected subsequent workflow generation.

This makes the workload useful as a coding-agent benchmark because the agent must connect a user-level parameter to a workflow-level implementation detail.

---

# 5. The headline result

The recorded elapsed times were:

```text
🟢 RTX 5060 Ti + llama.cpp

31m 01s
████████


🔵 M4 Pro + oMLX

118m 51s
████████████████████████████████
```

The ratio is:

```text
118m 51s
────────
31m 01s

≈ 3.83×
```

The absolute difference is:

```text
118m 51s - 31m 01s
= 87m 50s
```

Equivalently, the RTX run completed the recorded workload in approximately **26% of the M4 wall-clock time**.

This is the primary end-to-end result.

---

# 6. But the clock is only part of the story

The agent trajectories were also different.

| Metric | 🟢 RTX | 🔵 M4 | M4 / RTX |
|---|---:|---:|---:|
| Wall time | 31m 01s | 118m 51s | **3.83×** |
| Messages | 166 | 237 | **1.43×** |
| Tool calls | 80 | 121 | **1.51×** |
| Input tokens | 2,124,213 | 4,110,678 | **1.94×** |
| Cached input | 1,921,422 | 3,719,168 | **1.94×** |
| Uncached input | 202,791 | 391,510 | **1.93×** |
| Output tokens | 36,318 | 39,044 | **1.08×** |
| Total tokens | 2,160,531 | 4,149,722 | **1.92×** |

Three differences stand out immediately.

### 6.1 More interactions

The M4 run recorded:

```text
237 messages
121 tool calls
```

versus:

```text
166 messages
80 tool calls
```

for RTX.

That is approximately:

```text
+43% messages
+51% tool calls
```

---

### 6.2 Almost twice the input context

The M4 run processed:

```text
4.11M input tokens
```

versus:

```text
2.12M
```

for RTX.

That is approximately:

```text
+94% input tokens
```

Total token volume was also approximately:

```text
4.15M / 2.16M ≈ 1.92×
```

---

### 6.3 Output volume was surprisingly similar

Output tokens were:

```text
RTX: 36,318
M4:  39,044
```

Only about:

```text
+8%
```

This creates an interesting asymmetry:

```text
Input tokens      +94%
Output tokens      +8%
```

The M4 trajectory therefore appears to have accumulated and processed much more input/context without producing proportionally more generated output.

That does **not** mean the additional context was unnecessary. It simply means that the extra work was predominantly on the input/context side rather than output generation.

---

# 7. Cache behavior

The cached-input proportions were approximately equal:

```text
RTX
1,921,422 / 2,124,213 ≈ 90.5%

M4
3,719,168 / 4,110,678 ≈ 90.5%
```

So the benchmark does not support a simple explanation such as:

> “The M4 was slower because caching was not working.”

Both runs show roughly the same cache share.

The more obvious difference is the **absolute amount of context being processed**.

```text
Similar cache percentage
          +
Much larger M4 input volume
          ↓
Different context-processing workload
```

The current experiment does not isolate how much of the final 87m 50s difference came from context processing itself.

---

# 8. Did both agents actually solve the same problem?

This is where the experiment becomes more interesting.

The final production changes were highly convergent.

Both agents independently arrived at the same broad architecture:

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
                     Sidecar mapping
                           │
                           ▼
                  LTX scheduler node 206
                           │
                           ▼
                     Workflow input
```

Both patches:

- propagated the experiment-level `steps`;
- retained a default value;
- passed the sidecar to the workflow layer;
- added sidecar-aware mapping;
- mapped the LTX scheduler's `steps` input;
- retained generic KSampler fallback;
- added regression tests.

This is strong evidence of **solution convergence**.

It does not prove that the agents reasoned identically. They may have explored different files, issued different commands, or reached the same design through different intermediate hypotheses.

But the final engineering destination was highly similar.

---

# 9. Solution quality vs trajectory efficiency

This suggests two different dimensions for coding-agent evaluation.

```text
                 CODING-AGENT PERFORMANCE
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Solution quality          Trajectory efficiency
              │                         │
        Did it repair?             How much work?
              │                         │
       Tests / patch               Tools / tokens
              │                         │
              └────────────┬────────────┘
                           ▼
                     Wall-clock time
```

Task 01 shows:

```text
Solution convergence       HIGH
Trajectory convergence     LOW
```

That distinction is important.

A benchmark that reports only final correctness could conclude that both systems performed similarly.

A benchmark that reports only tokens/second could miss the agent's actual interaction behavior.

The end-to-end result reveals both.

---

# 10. Validation

The recorded RTX evidence contains:

```text
230 tests
+
compileall
```

The Mac session evidence reports:

```text
227 tests passed
```

However, the Mac raw test artifact also contains:

```text
pytest: command not found
```

This creates a validation asymmetry.

The correct interpretation is **not**:

```text
RTX = passed
M4  = failed
```

Instead:

```text
RTX
 └── 230 tests + compileall recorded

M4
 ├── 227 tests reported in session evidence
 └── test artifact has a pytest environment problem
```

The Mac environment should be normalized before using test counts as a clean apples-to-apples correctness ranking.

This is an example of why preserving raw evidence matters.

---

# 11. Why the 3.83× result should not be over-interpreted

The wall-clock ratio is real:

```text
3.83×
```

But the experiment changes several variables simultaneously.

The RTX configuration uses:

```text
NVIDIA GPU
+
Windows
+
llama.cpp
+
4.5 bpw pure GGUF
```

The M4 configuration uses:

```text
Apple Silicon
+
macOS
+
oMLX / MLX
+
oQ4-MTP
```

Therefore the result cannot isolate:

- GPU architecture;
- CPU architecture;
- llama.cpp;
- oMLX;
- quantization;
- model representation;
- operating system;
- memory architecture.

The strongest defensible statement is:

> **On this specific ai_video_optimization_app repair workload, the tested RTX 5060 Ti + llama.cpp configuration completed the recorded 55K-context coding-agent run substantially faster than the tested M4 Pro + oMLX configuration.**

That is both useful and reproducible.

---

# 12. Why the trajectory difference matters

Suppose two systems both reach the same patch:

```text
System A:
80 tools
2.16M tokens
31 minutes

System B:
121 tools
4.15M tokens
119 minutes
```

A conventional benchmark might report only:

```text
Correct
Correct
```

and call them equivalent.

But for a developer choosing a local coding-agent machine, the operational difference is substantial.

The developer experiences:

```text
time spent waiting
+
context processed
+
tool interactions
+
test cycles
+
machine utilization
```

That is the actual user-facing performance of the coding agent.

This is why LCAB treats **agent trajectory** as a first-class measurement.

---

# 13. A useful way to think about coding-agent efficiency

A coding agent can be viewed as a closed-loop controller:

```text
                  ┌──────────────┐
                  │   Problem    │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │     Model    │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │     Tool     │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │ Tool result  │
                  └──────┬───────┘
                         ▼
                  ┌──────────────┐
                  │ Context grows│
                  └──────┬───────┘
                         │
                         └──────────► next model turn
```

A longer trajectory can create a feedback effect:

```text
More tool interactions
        ↓
More tool results
        ↓
More accumulated context
        ↓
Larger future inputs
        ↓
More context-processing work
        ↓
Longer end-to-end time
```

Task 01 is consistent with this pattern.

However, the current aggregate data is not sufficient to establish that this exact causal loop explains the entire performance gap.

---

# 14. What would make the next experiment stronger?

The next step is not another isolated hardware comparison.

The next step is **controlled scaling**.

## Experiment A — Repeatability

Run the same task multiple times:

```text
RTX × 3
M4 × 3
```

Report:

- mean;
- median;
- minimum;
- maximum;
- standard deviation.

A single run is an observation. Repeated runs establish variance.

---

## Experiment B — Context scaling

Run the same workload at:

```text
16K
32K
55K
```

on both systems.

Measure:

```text
context size
    ↓
wall time

context size
    ↓
input tokens

context size
    ↓
tool calls

context size
    ↓
messages
```

This would reveal whether the performance gap grows as context increases.

---

## Experiment C — Per-turn trajectory analysis

Instead of only recording aggregate totals, capture:

```text
turn
timestamp
tool
input tokens
cached tokens
output tokens
context size
elapsed time
exit code
test activity
```

Then the benchmark can answer:

> **Where exactly did the extra time accumulate?**

---

## Experiment D — Runtime isolation

Where practical, hold model and agent configuration constant and vary the inference backend.

This is difficult across Windows/NVIDIA and Apple Silicon, but it is the experiment needed to attribute more of the observed difference to the runtime layer.

---

# 15. The next-generation LCAB data model

The benchmark can eventually turn each Pi session into a structured trajectory:

```text
pi-session.jsonl
       │
       ▼
     parser
       │
       ▼
trajectory.json
       │
       ├──────────────┬───────────────┐
       ▼              ▼               ▼
    Timing         Context          Tools
       │              │               │
       └──────────────┼───────────────┘
                      ▼
                Derived metrics
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        Charts      Report      Dataset
```

Future LCAB releases should preserve raw sessions and derive all higher-level measurements from them.

That creates an auditable chain:

```text
RAW EVIDENCE
     ↓
DERIVED METRICS
     ↓
ANALYSIS
     ↓
PUBLIC CONCLUSION
```

---

# 16. What this benchmark does establish

The current experiment provides strong evidence for the following statements:

### 1. The RTX configuration completed the recorded task faster.

```text
31m 01s vs 118m 51s
```

### 2. The M4 trajectory was substantially larger.

```text
+43% messages
+51% tool calls
+94% input tokens
+92% total tokens
```

### 3. Output-token volume was relatively similar.

```text
36.3K vs 39.0K
```

### 4. Cache share was approximately similar.

```text
~90.5% on both runs
```

### 5. The engineering solutions converged strongly.

Both patches implemented the same core `steps` propagation and sidecar-aware workflow mapping.

---

# 17. What this benchmark does not establish

The experiment does **not** establish:

```text
RTX 5060 Ti is universally 3.83× faster than M4 Pro.

llama.cpp is universally faster than oMLX.

The M4 Pro is unsuitable for local coding agents.

The M4 agent is intrinsically worse.

Hardware alone caused the performance difference.

The extra M4 context was unnecessary.

```

Those are questions for future controlled experiments.

---

# 18. The broader research question

The first LCAB result leads to a more useful question than:

> **Which GPU is faster?**

The question is:

> **How efficiently does a local coding-agent stack transform model inference, context, tool interactions, and repository exploration into a correct software repair?**

A conceptual model is:

```text
                 LOCAL CODING AGENT
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Hardware         Inference          Agent
        │                │                │
        │          context / cache       │
        │                │          tools / retries
        └────────────────┼────────────────┘
                         ▼
                    Tool execution
                         │
                         ▼
                      Testing
                         │
                         ▼
                  Software repair
                         │
                         ▼
                    Wall-clock
```

This is the direction LCAB is intended to explore.

---

# 19. Reproducibility

The benchmark repository retains the evidence needed to inspect the experiment:

- starting repository revision;
- final repository state;
- before/after patches;
- Pi version;
- model/runtime metadata;
- session logs;
- session HTML;
- session JSONL;
- timing data;
- test output;
- screenshots where captured.

The raw results are organized by run:

```text
results/raw/
├── 20260813-064832-task01-mac-m4/
└── 20260813-122237-task01-windows-rtx5060-llama/
```

The benchmark repository is:

**https://github.com/amitmaity0/local-coding-agent-benchmark-global**

The ai_video_optimization_app code changes used for the benchmark are maintained separately so that the benchmark evidence and the software-under-test remain independently inspectable.

---

# 20. Lessons from the first experiment

There are four lessons I would carry forward.

## Lesson 1 — Measure the repair, not only the model

Tokens/sec is useful, but the developer ultimately cares about:

```text
working software
```

---

## Lesson 2 — Record the trajectory

Two agents can reach the same patch through very different paths.

That difference is operationally important.

---

## Lesson 3 — Preserve raw evidence

A benchmark should not silently "fix" inconvenient data.

The Mac `pytest` issue and malformed timing fields are part of the experiment record and should remain visible until corrected through a documented processing step.

---

## Lesson 4 — Separate observation from explanation

The benchmark observed:

```text
3.83× wall-time difference
```

It did not yet prove a single cause.

That distinction makes the benchmark more useful, not less.

---

# 21. Final takeaway

The most interesting result from this first LCAB experiment is not simply:

```text
RTX: 31 minutes
M4: 119 minutes
```

It is this:

```text
                     SAME REAL REPAIR
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
            RTX                          M4
              │                           │
          80 tools                    121 tools
          2.16M tokens                4.15M tokens
          31m 01s                     118m 51s
              │                           │
              └─────────────┬─────────────┘
                            ▼
                  Similar engineering
                       solution
```

The two configurations reached a highly similar repair, but the recorded paths were substantially different.

That leads to the central LCAB hypothesis:

> ## **Local coding-agent performance is an end-to-end systems property.**

Hardware matters.

Inference runtime matters.

Context processing matters.

Agent behavior matters.

Tool execution matters.

Validation matters.

And the only useful way to understand the final developer experience is to measure the whole journey.

---

## Appendix A — Task 01 result snapshot

| Category | RTX 5060 Ti | M4 Pro |
|---|---:|---:|
| OS | Windows 11 | macOS |
| Accelerator | RTX 5060 Ti 16 GB | M4 Pro 64 GB unified |
| Runtime | llama.cpp | oMLX / MLX |
| Model | Qwen3.6-27B MTP | Qwen3.6-27B oQ4-MTP |
| Agent | Pi 0.84.1 | Pi 0.84.1 |
| Context target | 55K | 55K |
| Wall time | **31m 01s** | **118m 51s** |
| Messages | 166 | 237 |
| Tool calls | 80 | 121 |
| Input tokens | 2,124,213 | 4,110,678 |
| Cached input | 1,921,422 | 3,719,168 |
| Uncached input | 202,791 | 391,510 |
| Output tokens | 36,318 | 39,044 |
| Total tokens | 2,160,531 | 4,149,722 |
| Recorded validation | 230 tests + compileall | 227 tests reported; environment caveat |


---

## 🙏 Model Attribution & Credits

The RTX 5060 Ti benchmark used the **Qwen3.6-27B 4.5bpw-pure GGUF** published by **huytd189** on Hugging Face:

[Qwen3.6-27B-pure-GGUF](https://huggingface.co/huytd189/Qwen3.6-27B-pure-GGUF)

The benchmark used the published GGUF without modifying the model weights.

**Upstream model:** [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B)

The underlying model was developed by the **Qwen Team**.

Many thanks to **huytd189** for making the GGUF release available for local inference and benchmarking.

---

## Appendix B — Evidence boundary

This article distinguishes three levels of statement:

### Direct measurements

Values recorded in the benchmark artifacts, including wall time, token counts, message counts, tool calls, and session metadata.

### Engineering observations

Conclusions derived by comparing the actual patches produced by the two agents.

### Research hypotheses

Possible explanations for trajectory and performance differences that require additional controlled experiments.

Where the current experiment cannot isolate a cause, this article does not claim one.

---

## Appendix C — Project documentation

The LCAB repository contains the methodology, workload definition, hardware descriptions, benchmark procedure, detailed Task 01 results, code analysis, agent/tool trajectory analysis, summary findings, and raw evidence.

Start here:

**https://github.com/amitmaity0/local-coding-agent-benchmark-global**

---
