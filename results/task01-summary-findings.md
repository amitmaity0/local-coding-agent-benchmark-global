# 🏆 LCAB — Task 01 Benchmark Summary & Findings

> **Final publication-oriented summary of the 55K-context MotionForge repair benchmark**
>
> This document consolidates the Task 01 results, analysis, engineering convergence, and agent-trajectory observations into a concise research finding suitable as the foundation for a blog post, GitHub discussion, technical article, or social-media summary.
>
> **Primary comparison:** Windows + RTX 5060 Ti + llama.cpp vs macOS + M4 Pro + oMLX, using Pi 0.84.1 and Qwen3.6-27B on the same real software-repair workload.

---

# 🎯 1. Executive Summary

The first LCAB real-workload experiment compares two local coding-agent stacks on a multi-file MotionForge repair task with a **55K context target**.

```text
                         🔧 REAL REPAIR
                              │
                              ▼
                    MotionForge Task 01
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          🟢 RTX 5060 Ti              🔵 M4 Pro
          Windows + llama.cpp         macOS + oMLX
                 │                         │
                 ▼                         ▼
              Qwen3.6-27B             Qwen3.6-27B
                 │                         │
                 └────────────┬────────────┘
                              ▼
                           Pi 0.84.1
                              │
                              ▼
                       55K context target
```

### Headline result

| Metric | 🟢 RTX 5060 Ti | 🔵 M4 Pro |
|---|---:|---:|
| Wall time | **31m 01s** | **118m 51s** |
| Messages | **166** | **237** |
| Tool calls | **80** | **121** |
| Input tokens | **2.12M** | **4.11M** |
| Output tokens | **36.3K** | **39.0K** |
| Total tokens | **2.16M** | **4.15M** |
| Cache share | **~90.5%** | **~90.5%** |

The observed wall-clock difference is:

```text
118m 51s / 31m 01s ≈ 3.83×
```

The RTX configuration therefore completed this recorded workload in approximately **26% of the M4 Pro wall-clock time**.

---

# 🧠 2. The Most Important Finding

The most interesting result is **not simply that RTX finished faster**.

The two agents also converged on essentially the same engineering solution.

```text
                         SAME TASK
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
            RTX                          M4
              │                           │
       31m 01s / 80 tools          118m 51s / 121 tools
       2.16M total tokens          4.15M total tokens
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    Similar repair
```

This creates a useful research distinction:

> **Solution quality can converge even when agent trajectory efficiency differs dramatically.**

That is a stronger research observation than a simple hardware-speed comparison.

---

# 🔧 3. What Was Actually Repaired?

The task required a cross-layer repair involving the experiment's `steps` parameter.

The essential execution path is:

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
Sidecar-aware parameter mapping
       │
       ▼
LTX scheduler node 206
       │
       ▼
workflow["206"]["inputs"]["steps"]
```

The agents independently discovered and implemented essentially this same architecture.

The repair included:

- propagating `Experiment.steps`;
- passing the value through the engine;
- making `set_steps()` sidecar-aware;
- mapping `steps` to the LTX scheduler;
- retaining generic KSampler fallback behavior;
- adding regression tests;
- connecting optimization state to subsequent workflow generation.

This is important because the benchmark tests **repository-level understanding**, not just single-file code generation.

---

# 🏗️ 4. Engineering Convergence

The two benchmark branches changed substantially similar production areas.

| Area | 🟢 RTX | 🔵 M4 55K |
|---|---:|---:|
| `orchestrator/engine.py` | +3 / -1 | +4 / -1 |
| `services/workflow.py` | +22 / -2 | +20 / -2 |
| Autonomous-loop tests | +525 / -1 | +463 / -1 |
| Sidecar tests | +9 | +10 |
| Workflow tests | +46 / -1 | +49 |
| LTX sidecar | +6 / -1 | +6 / -1 |

The exact test implementations differ, but the production repair converges strongly.

### This matters because:

```text
Different trajectory
        ↓
Different exploration
        ↓
Different interaction volume
        ↓
Similar engineering destination
```

That makes Task 01 a useful example of **trajectory efficiency as a distinct benchmark dimension**.

---

# 📊 5. Agent-Trajectory Findings

The recorded metrics show:

```text
                    RTX          M4
Messages            166          237
Tool calls           80          121
Input tokens       2.12M        4.11M
Output tokens     36.3K         39.0K
Total tokens       2.16M        4.15M
```

Relative to RTX, the M4 run used approximately:

```text
+43% messages
+51% tool calls
+94% input tokens
+92% total tokens
+8% output tokens
```

The strongest observation is therefore:

> **The M4 trajectory processed substantially more accumulated context without producing proportionally more output.**

The input/output asymmetry is particularly notable:

```text
Input:   +94%
Output:   +8%
```

This suggests that context volume and interaction history deserve first-class measurement in local coding-agent benchmarks.

---

# 💾 6. Context and Caching

Both runs had approximately the same cached-input percentage:

```text
RTX ≈ 90.5%
M4  ≈ 90.5%
```

Therefore the benchmark does not support a simple explanation such as:

> “The M4 was slower because it did not use caching.”

Instead:

```text
Similar cache share
        +
Much larger M4 context volume
        ↓
Different context-processing workload
```

The current experiment cannot determine exactly how much of the wall-time difference came from context processing versus other runtime and trajectory effects.

---

# ⏱️ 7. Where the 87m 50s Difference Came From

The wall-clock difference is:

```text
118m 51s
-
31m 01s
────────
87m 50s
```

The current aggregate benchmark cannot allocate those 87m 50s precisely.

Possible contributors include:

```text
Inference latency
Context processing
Tool execution
Test execution
Repository exploration
Agent recovery
Runtime overhead
Waiting / service latency
```

Therefore:

### Supported conclusion

> The complete RTX configuration finished substantially faster.

### Unsupported conclusion

> The RTX GPU itself is 3.83× faster than the M4 Pro.

The latter requires controlled experiments that isolate hardware, runtime, model representation, and trajectory.

---

# ⚖️ 8. What This Benchmark Does — and Does Not — Compare

The experiment compares two **complete configurations**:

```text
RTX:
Windows
+ RTX 5060 Ti 16GB
+ llama.cpp
+ Qwen3.6-27B 4.5bpw GGUF/MTP
+ Pi 0.84.1
+ 55K target

M4:
macOS
+ M4 Pro 64GB
+ oMLX / MLX
+ Qwen3.6-27B oQ4-MTP
+ Pi 0.84.1
+ 55K target
```

Because multiple variables differ, the benchmark does **not** isolate:

```text
GPU performance alone
CPU performance alone
llama.cpp alone
oMLX alone
quantization alone
model representation alone
```

This distinction should remain explicit in all public material.

---

# 🧪 9. Validation Findings

The recorded RTX evidence includes:

```text
230 tests
+
compileall
```

The Mac evidence reports:

```text
227 tests passed
```

but also contains a documented:

```text
pytest: command not found
```

test-environment issue.

Therefore the current validation status should be represented as:

| Configuration | Validation status |
|---|---|
| 🟢 RTX | **Strong recorded validation** — 230 tests + compileall |
| 🟡 M4 | **Positive session evidence, environment anomaly** — 227 tests reported; final automated test artifact has missing `pytest` |

The correct publication language is **not**:

```text
RTX passed
M4 failed
```

The environment should first be normalized for a definitive correctness comparison.

---

# 🔬 10. Evidence Strength

| Finding | Evidence |
|---|---|
| RTX completed faster | 🟢 Direct |
| 3.83× wall-time ratio | 🟢 Direct |
| M4 used more tool calls | 🟢 Direct |
| M4 processed more tokens | 🟢 Direct |
| Output volumes were similar | 🟢 Direct |
| Cache shares were similar | 🟢 Direct |
| Production repairs converged | 🟢 Strong code evidence |
| M4 trajectory was longer | 🟢 Direct |
| Extra context caused all extra latency | 🟠 Not established |
| Hardware caused all extra latency | 🔴 Unsupported |
| llama.cpp is universally faster than oMLX | 🔴 Unsupported |
| RTX 5060 Ti is universally faster than M4 Pro | 🔴 Unsupported |
| M4 agent was intrinsically worse | 🔴 Unsupported |

This evidence boundary should be preserved in the public report.

---

# 🧭 11. What Task 01 Tells Us About LCAB

Task 01 suggests that local coding-agent benchmarking should have at least four measurement layers:

```text
                 ┌─────────────────────┐
                 │      HARDWARE       │
                 │ GPU / CPU / memory  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     INFERENCE      │
                 │ runtime / context │
                 │ generation / cache│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       AGENT        │
                 │ tools / messages  │
                 │ trajectory / retry│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  SOFTWARE REPAIR   │
                 │ patch / tests /    │
                 │ correctness / time │
                 └─────────────────────┘
```

A benchmark that reports only inference throughput sees only one layer.

LCAB can connect all four.

---

# 📈 12. Proposed LCAB Core Metrics

For each future benchmark run, collect:

### 🖥️ Hardware

```text
GPU
VRAM
CPU
RAM / unified memory
peak utilization
power where available
```

### ⚡ Inference

```text
runtime
model
quantization
context target
prompt processing
generation
cache statistics
```

### 🤖 Agent

```text
messages
tool calls
failed tool calls
retries
context growth
compactions
trajectory duration
```

### 🔧 Repair

```text
wall time
files changed
patch size
tests passed
tests failed
final Git SHA
correctness
```

The final benchmark should connect:

```text
Hardware
   ↓
Inference
   ↓
Agent
   ↓
Repair
```

---

# 🧪 13. Priority Follow-Up Experiments

## 1️⃣ Repeat the same task

Run:

```text
RTX × 3
M4 × 3
```

This establishes variance.

Report:

```text
mean
median
min
max
standard deviation
```

A single run should not become a universal ranking.

---

## 2️⃣ Scale context

Run:

```text
16K
32K
55K
```

on both configurations.

Measure:

```text
wall time
input tokens
tool calls
messages
output tokens
```

The result becomes a context-scaling curve rather than a single point.

---

## 3️⃣ Normalize validation

Ensure both systems run:

```text
same test command
same dependencies
same repository state
same test environment
```

This removes the current Mac `pytest` ambiguity.

---

## 4️⃣ Parse the full Pi trajectory

Convert:

```text
pi-session.jsonl
```

into:

```text
trajectory.json
```

with per-turn:

```text
timestamp
tool
input tokens
output tokens
context size
elapsed time
exit code
test activity
```

This would reveal where the extra wall time accumulates.

---

# 🔬 14. The Next Research Question

Task 01 changes the question from:

> **Which machine is faster?**

to:

> **How efficiently does a local coding-agent stack transform context, tool interactions, and inference into a correct software repair?**

A conceptual efficiency model is:

```text
                  Agent Efficiency
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
  Context cost       Tool cost       Inference cost
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                   Repair outcome
                         │
                         ▼
                    Wall-clock
```

This is not yet a formal LCAB score.

It is the research direction suggested by the first real-workload experiment.

---

# 🏆 15. Overall Task 01 Assessment

### 🟢 Strong findings

1. The RTX configuration completed the workload substantially faster.
2. The M4 trajectory involved substantially more recorded interaction.
3. The M4 trajectory processed almost twice the total token volume.
4. Output-token volume was relatively similar.
5. Both agents converged on a highly similar engineering solution.
6. The workload exercised real repository-level reasoning rather than a synthetic coding task.

### 🟡 Findings requiring more experiments

1. How much of the wall-time gap is context processing?
2. How much is runtime/inference performance?
3. How much comes from different agent trajectories?
4. How stable is the result across repeated runs?
5. Does the gap grow with context length?
6. Does the same ranking hold across other repair tasks?

### 🔴 Claims not supported by Task 01

```text
RTX 5060 Ti is universally 3.83× faster than M4 Pro.
llama.cpp is universally faster than oMLX.
The M4 Pro is unsuitable for local coding agents.
The M4 agent is inherently worse.
The hardware alone caused the observed result.
```

---

# 📌 16. Publication-Ready Summary

> ### 🏆 Local Coding-Agent Benchmark: RTX vs M4 Pro
>
> I benchmarked two complete local coding-agent configurations on the same real MotionForge software-repair workload using **Pi 0.84.1 + Qwen3.6-27B** with a **55K context target**.
>
> **RTX 5060 Ti + llama.cpp:** 31m 01s  
> **M4 Pro + oMLX:** 118m 51s
>
> The RTX run completed the recorded repair in approximately **3.83× less wall-clock time**.
>
> But the more interesting result was the agent trajectory. The RTX run used **80 tool calls and 2.16M total tokens**, while the M4 run used **121 tool calls and 4.15M total tokens**. Output-token volume was relatively close: **36.3K vs 39.0K**.
>
> Both configurations also converged on essentially the same engineering repair.
>
> This suggests that real coding-agent benchmarks need to measure more than model tokens/sec. **Context volume, tool interactions, trajectory efficiency, validation behavior, and final software-repair quality all matter.**
>
> This is an initial real-workload result, not a universal RTX-vs-M4 hardware ranking.

---

# 🧵 17. Short Social / Forum Version

> 🧪 **Local coding-agent benchmark: RTX 5060 Ti vs M4 Pro**
>
> Same real MotionForge repair. Same Pi 0.84.1 + Qwen3.6-27B. 55K context.
>
> 🟢 RTX + llama.cpp → **31m 01s**
>
> 🔵 M4 Pro + oMLX → **118m 51s**
>
> That's a **3.83× end-to-end difference**.
>
> But the interesting part:
>
> RTX → 80 tools / 2.16M tokens  
> M4 → 121 tools / 4.15M tokens
>
> Output tokens were much closer: 36.3K vs 39.0K.
>
> Both agents converged on essentially the same code repair.
>
> So the question isn't just “which GPU is faster?” It's:
>
> **How efficiently does the whole local coding-agent stack turn context + tool interactions + inference into a correct software repair?**
>
> More real-task runs coming.

---

# 🌐 18. Recommended Publication Assets

For public release, this document should be accompanied by:

```text
README.md
        │
        ├── Methodology
        ├── Hardware
        ├── Task definition
        └── Results
              │
              ├── Task 01 results
              ├── Task 01 analysis
              └── Task 01 trajectory
                    │
                    ▼
               Raw evidence
                    │
             ┌──────┴──────┐
             ▼             ▼
       pi-session.jsonl   diff.patch
```

Recommended visual assets:

### 📊 Chart 1 — Wall time

```text
RTX ████████ 31m
M4  █████████████████████████████ 119m
```

### 🧠 Chart 2 — Total tokens

```text
RTX ███████████ 2.16M
M4  █████████████████████ 4.15M
```

### 🛠️ Chart 3 — Tool calls

```text
RTX ████████████████ 80
M4  ████████████████████████ 121
```

### 🔄 Diagram — Agent trajectory

```text
Task
 ↓
Inspect
 ↓
Reason
 ↓
Tool
 ↓
Context grows
 ↓
Edit
 ↓
Test
 ↓
Repair
```

These visuals make the publication understandable without requiring readers to inspect raw logs.

---

# 📚 19. Reproducibility Standard

Every published benchmark result should retain:

```text
☑ Run ID
☑ Task ID
☑ Starting Git SHA
☑ Hardware
☑ OS
☑ Runtime
☑ Runtime version
☑ Model
☑ Quantization / model representation
☑ Agent version
☑ Context target
☑ Output target
☑ Start timestamp
☑ End timestamp
☑ Raw Pi session
☑ Raw test output
☑ Before/after Git state
☑ Patch
☑ Anomalies
```

The evidence hierarchy should remain:

```text
RAW EVIDENCE
     │
     ▼
DERIVED METRICS
     │
     ▼
ANALYSIS
     │
     ▼
PUBLIC CONCLUSION
```

Raw evidence should remain immutable.

---

# 🧭 20. LCAB Thesis Emerging from Task 01

Task 01 suggests the following working thesis:

> ### **Local coding-agent performance is an end-to-end systems property.**
>
> The useful unit of measurement is not only model generation throughput. It is the complete path from **hardware → inference runtime → context processing → agent interaction → tool execution → validation → correct software repair**.

In compact form:

```text
              ┌─────────────┐
              │   Hardware  │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │  Inference  │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │    Agent    │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │    Tools    │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │   Repair    │
              └──────┬──────┘
                     ▼
                Correctness
                     +
                 Wall time
```

This is the central research direction that future LCAB tasks should test.

---

# 🎯 21. Final Takeaway

Task 01 does **not** establish a universal winner between the RTX 5060 Ti and M4 Pro.

It establishes something more useful:

```text
Two local coding-agent stacks
             │
             ▼
Same real software repair
             │
             ├───────────────────┐
             ▼                   ▼
      Similar solution      Very different
          quality             trajectory
             │                   │
             │             tools / context
             │                   │
             └─────────┬─────────┘
                       ▼
              Very different
              end-to-end time
```

The strongest conclusion is:

> **On this 55K-context MotionForge repair, the tested RTX 5060 Ti + llama.cpp configuration reached a highly similar engineering solution substantially faster and with a substantially smaller recorded agent trajectory than the tested M4 Pro + oMLX configuration.**

The next step is not to declare a universal hardware winner.

The next step is to determine **why** the trajectories diverge, whether the result survives across additional repair tasks, and how context length, runtime, model representation, and agent behavior each contribute to end-to-end coding-agent performance.

---

## 📌 Evidence Boundary

This summary is based on the recorded Task 01 benchmark results, preserved agent-session metrics, branch-level code comparison, and documented validation evidence.

It intentionally distinguishes:

- direct measurements;
- engineering observations;
- analytical interpretation;
- future hypotheses.

Where the current experiment cannot isolate a cause, this document does not claim one.
