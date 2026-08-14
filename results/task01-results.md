# 📊 Task 01 — 55K Context Benchmark Results

> **RTX 5060 Ti + llama.cpp vs Apple M4 Pro + oMLX/MLX**
>
> Real software-repair benchmark using **Pi 0.84.1 + Qwen3.6-27B** on the MotionForge repository.

---

## 🏁 Executive Summary

This experiment compares two complete local coding-agent configurations on the same real software-repair workload and the same starting repository revision.

```text
                         🔧 MotionForge Task 01
                                  │
                                  ▼
                         Common baseline
                    9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
             🟢 RTX 5060 Ti                🔵 M4 Pro
             Windows + llama.cpp           macOS + oMLX
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                              🤖 Pi
                                  │
                           🧠 Qwen3.6-27B
                                  │
                                  ▼
                         🧪 Repair + Validation
```

### Headline result

| Metric | 🟢 RTX 5060 Ti | 🔵 M4 Pro |
|---|---:|---:|
| Runtime | llama.cpp | oMLX / MLX |
| Agent | Pi 0.84.1 | Pi 0.84.1 |
| Context target | **55K** | **55K** |
| Wall time | **31m 01s** | **118m 51s** |
| Messages | **166** | **237** |
| Tool calls | **80** | **121** |
| Input tokens | **2,124,213** | **4,110,678** |
| Cached input | **1,921,422** | **3,719,168** |
| Uncached input | **202,791** | **391,510** |
| Output tokens | **36,318** | **39,044** |
| Total tokens | **2,160,531** | **4,149,722** |
| Validation evidence | **230 tests + compileall** | **227 tests reported** |

### 🏆 Primary observation

The RTX configuration completed the recorded workload in approximately:

```text
31m 01s
```

versus:

```text
118m 51s
```

for the M4 Pro configuration.

That is a:

```text
118m 51s / 31m 01s ≈ 3.83×
```

wall-clock difference.

> ⚠️ This is a **complete-stack result**, not a universal hardware ranking. The two systems use different inference runtimes and model representations, and the Mac validation environment has a documented `pytest` collection issue.

---

# 🧪 1. What Was Tested?

The workload is a real multi-file software-repair task from the **MotionForge** project.

The benchmark starts from the common repository revision:

```text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

The primary benchmark branches are:

```text
benchmark/task9-rtx5060ti-mtp
benchmark/task9-m4pro-omlx-mtp-55k
```

A separate exploratory branch exists:

```text
benchmark/task9-m4pro-omlx-mtp-unlimited
```

The unlimited-context run is intentionally excluded from this primary hardware/runtime comparison because its implementation trajectory diverged more substantially from the other two benchmark branches.

The primary experiment therefore compares the **RTX 55K** and **M4 Pro 55K** configurations.

---

# 🖥️ 2. Benchmark Configurations

## 🟢 RTX 5060 Ti

```text
Windows 11 Pro
      │
      ▼
Intel i5-8600
      │
      ▼
RTX 5060 Ti — 16 GB VRAM
      │
      ▼
llama.cpp
      │
      ▼
Qwen3.6-27B
4.5 bpw pure GGUF / MTP
      │
      ▼
Pi 0.84.1
      │
      ▼
55K context target
```

## 🔵 Apple M4 Pro

```text
macOS
      │
      ▼
Apple M4 Pro — 64 GB unified memory
      │
      ▼
oMLX / MLX
      │
      ▼
Qwen3.6-27B
oQ4-MTP
      │
      ▼
Pi 0.84.1
      │
      ▼
55K context target
```

The two systems therefore share:

- the same coding-agent framework;
- the same model family;
- the same real repair workload;
- the same starting repository revision;
- the same target context size;
- the same maximum output target.

They differ in:

- hardware architecture;
- operating system;
- inference runtime;
- model representation / quantization.

Therefore this should be described as a **complete local coding-agent configuration comparison**.

---

# 🔗 3. Run Provenance

The recorded runs are:

| System | Run ID |
|---|---|
| 🔵 Mac M4 Pro | `20260813-064832-task01-mac-m4` |
| 🟢 Windows RTX | `20260813-122237-task01-windows-rtx5060-llama` |

Both runs preserve benchmark evidence including repository state, agent-session information, metadata and resulting patches.

The common baseline is:

```text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

Conceptually:

```text
                         BASELINE
                    9ab2b50bc2ce...
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          RTX benchmark        M4 benchmark
                 │                   │
          llama.cpp / 55K       oMLX / 55K
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    Compare results
```

This common baseline is important because it eliminates a major source of experimental variation: different starting repository states.

---

# ⏱️ 4. Wall-Clock Result

```text
RTX 5060 Ti   ████████                         31m 01s
M4 Pro        █████████████████████████████    118m 51s
```

### Relative result

```text
118m 51s / 31m 01s ≈ 3.83×
```

The M4 Pro run took approximately:

```text
87m 50s
```

longer.

Equivalently, the RTX run completed the recorded workload in approximately:

```text
31m 01s / 118m 51s ≈ 26%
```

of the M4 Pro wall-clock time.

This is the most striking result in the current experiment.

---

# 🤖 5. Agent Trajectory

| Metric | 🟢 RTX | 🔵 M4 Pro |
|---|---:|---:|
| Messages | **166** | **237** |
| Tool calls | **80** | **121** |
| Input tokens | **2.12M** | **4.11M** |
| Output tokens | **36.3K** | **39.0K** |
| Total tokens | **2.16M** | **4.15M** |

Relative to the RTX run, the M4 Pro run consumed approximately:

```text
1.43× more messages
1.51× more tool calls
1.94× more input tokens
1.92× more total tokens
```

while producing only:

```text
1.08× more output tokens
```

This means the wall-clock difference is not explained simply by the amount of generated output.

A substantial difference appears in the **interaction trajectory and context volume**.

```text
More input context
        +
More messages
        +
More tool calls
        +
Longer trajectory
        ↓
Much longer end-to-end repair time
```

This is an observation from the recorded runs, not yet a causal conclusion.

---

# 🧠 6. Token Accounting

## RTX 5060 Ti

```text
Input:       2,124,213
 ├─ cached:  1,921,422
 └─ uncached: 202,791

Output:         36,318
Total:       2,160,531
```

## M4 Pro

```text
Input:       4,110,678
 ├─ cached:  3,719,168
 └─ uncached: 391,510

Output:         39,044
Total:       4,149,722
```

| Token metric | RTX | M4 Pro |
|---|---:|---:|
| Cached input | 1.92M | 3.72M |
| Cache share | ~90.5% | ~90.5% |
| Uncached input | 202.8K | 391.5K |
| Output | 36.3K | 39.0K |
| Total | 2.16M | 4.15M |

The two runs have a remarkably similar cache proportion while the M4 trajectory processes almost twice as much total context.

This is important because it suggests the difference is not simply a binary **cached vs uncached** effect.

---

# 🛠️ 7. Tool-Use Behavior

```text
Tool calls

RTX 5060 Ti
████████████████ 80

M4 Pro
████████████████████████ 121
```

The M4 Pro run made:

```text
121 - 80 = 41
```

additional tool calls.

Relative increase:

```text
121 / 80 ≈ 1.51×
```

or approximately:

> **51% more tool calls.**

Coding-agent performance depends on the complete loop:

```text
Reason
  ↓
Inspect
  ↓
Edit
  ↓
Execute
  ↓
Observe
  ↓
Reason again
```

Consequently, interaction count is a meaningful benchmark dimension in addition to model throughput.

---

# 🧪 8. Validation Results

## 🟢 RTX 5060 Ti

The recorded RTX result contains:

```text
230 tests pass
+
compileall
```

This provides a strong recorded validation artifact for the RTX run.

## 🔵 M4 Pro

The Mac run reports:

```text
227 tests passed
```

However, the raw Mac test artifact also contains:

```text
pytest: command not found
```

Therefore the Mac validation result must be interpreted carefully.

### Correct interpretation

Do **not** summarize the evidence as:

> “RTX passed while Mac failed.”

The available evidence instead indicates:

```text
RTX
 └── 230 tests + compileall recorded

Mac
 ├── 227 tests reported in session evidence
 └── final automated test-collection artifact has pytest missing
```

This is a **validation-environment asymmetry**, not sufficient evidence that the Mac software repair itself failed.

Before making a definitive apples-to-apples correctness claim, the test environment should be normalized.

---

# 🔧 9. What the Agents Repaired

The benchmark task involves coordinated changes across the MotionForge execution path.

The central repair can be represented as:

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
```

Both benchmark configurations independently converged on essentially the same engineering approach.

The repair:

1. propagates `steps` from the experiment;
2. passes it through the engine;
3. extends workflow parameter mapping;
4. keeps the mapping sidecar-aware;
5. preserves generic KSampler behavior;
6. adds regression coverage;
7. connects optimization state to subsequent workflow generation.

This convergence is important because the benchmark is not comparing two completely different implementations.

---

# 📐 10. Patch / Engineering Convergence

The benchmark branches are also relatively close in their code-change profiles.

### RTX branch

The benchmark branch changes include:

| File | Change |
|---|---:|
| `orchestrator/engine.py` | +3 / -1 |
| `services/workflow.py` | +22 / -2 |
| `tests/test_autonomous_loop.py` | +525 / -1 |
| `tests/test_sidecar.py` | +9 |
| `tests/test_workflow.py` | +46 / -1 |
| `workflows/LTX2.3-Basic-API.yaml` | +6 / -1 |

### M4 Pro 55K branch

| File | Change |
|---|---:|
| `orchestrator/engine.py` | +4 / -1 |
| `services/workflow.py` | +20 / -2 |
| `tests/test_autonomous_loop.py` | +463 / -1 |
| `tests/test_sidecar.py` | +10 |
| `tests/test_workflow.py` | +49 |
| `workflows/LTX2.3-Basic-API.yaml` | +6 / -1 |

The similarity of the core implementation makes the trajectory difference particularly interesting.

---

# 🔬 11. What the Experiment Actually Shows

The strongest defensible statement is:

> **On this specific MotionForge Task 01 workload, the recorded RTX 5060 Ti + llama.cpp + Qwen3.6-27B + Pi configuration completed the repair substantially faster than the recorded M4 Pro + oMLX + Qwen3.6-27B + Pi configuration.**

Measured difference:

```text
RTX: 31m 01s
M4:  118m 51s

Difference: 87m 50s
Ratio:      3.83×
```

The M4 Pro run also exhibited:

```text
+43% messages
+51% tool calls
+94% input tokens
+92% total tokens
+8% output tokens
```

This makes the result interesting beyond a simple hardware-speed comparison.

---

# 🧩 12. Research Hypothesis

The initial result suggests a broader question:

> **Is end-to-end coding-agent performance dominated by raw generation speed, or by the interaction between inference latency, context processing and agent trajectory?**

```text
              End-to-End Repair Time
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   Inference          Context          Agent
    latency           processing      trajectory
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  Tool interactions
                         │
                         ▼
                    Test cycles
                         │
                         ▼
                  Final repair
```

The current dataset is too small to establish causality.

---

# ⚠️ 13. Experimental Caveats

## Single workload

This is currently one real software-repair task.

It should therefore be described as:

> **an initial real-workload benchmark**

rather than a statistically comprehensive characterization of local coding hardware.

## Different runtimes

```text
RTX → llama.cpp
M4  → oMLX / MLX
```

This is a complete-stack comparison, not a pure hardware comparison.

## Different model representations

```text
RTX:
Qwen3.6-27B-MTP-4.5bpw-pure.gguf

M4:
Qwen3.6-27B-oQ4-MTP
```

The observed difference therefore cannot be attributed entirely to hardware.

## Validation asymmetry

The Mac raw test artifact contains:

```text
pytest: command not found
```

despite 227 tests being reported in session evidence.

## Timing evidence

The benchmark methodology requires elapsed time to be reconstructed from preserved start/end timestamps rather than trusting malformed derived timing fields.

Raw timing evidence should remain immutable.

---

# 🧭 14. Primary Conclusion

```text
┌─────────────────────────────────────────────┐
│          Task 01 — 55K Context              │
├─────────────────────────────────────────────┤
│ RTX + llama.cpp      31m 01s                │
│ M4 + oMLX            118m 51s               │
├─────────────────────────────────────────────┤
│ RTX was ~3.83× faster in wall-clock time    │
└─────────────────────────────────────────────┘
```

The RTX configuration also used substantially fewer messages, tool calls, input tokens and total tokens while generating a similar amount of output.

### What we can say

> **On this workload, the tested RTX 5060 Ti + llama.cpp configuration was substantially faster end-to-end than the tested M4 Pro + oMLX configuration.**

### What we cannot say yet

```text
RTX 5060 Ti > M4 Pro
```

in general.

Nor:

```text
llama.cpp > oMLX
```

in general.

The experiment measures two complete configurations on one real repair workload.

---

# 🔬 15. Why This Benchmark Is Interesting

Synthetic benchmarks often ask:

```text
“How many tokens/sec?”
```

LCAB asks:

```text
“How long did the coding agent
take to actually repair the software?”
```

A system can have:

```text
Excellent tokens/sec
       +
Poor agent trajectory
       +
Many tool calls
       +
Large context processing
       ↓
Poor end-to-end repair time
```

Conversely:

```text
Lower tokens/sec
       +
Efficient agent trajectory
       +
Fewer interactions
       ↓
Competitive repair time
```

Task 01 demonstrates why real software-repair workloads complement synthetic inference benchmarks.

---

# 📈 16. Recommended Next Experiments

| Experiment | Research question |
|---|---|
| 📐 Context scaling | How do 16K / 32K / 55K contexts affect repair time? |
| 🔢 Output limit | Does maximum output materially affect trajectory? |
| ⚡ Runtime tuning | How much can llama.cpp / oMLX tuning reduce end-to-end time? |
| 🧠 Quantization | Does equivalent model representation change the result? |
| 🤖 Repeated runs | How stable are repair trajectories? |
| 🔧 More tasks | Does the observed RTX advantage persist across repairs? |
| 🧪 Validation normalization | Can both systems use exactly the same test environment? |
| 🔄 OpenHands | Does the hardware/runtime ranking change with another agent? |

The most valuable immediate follow-up is:

> **Run multiple real repair tasks with identical agent/runtime settings, then repeat selected tasks to measure trajectory variance.**

---

# 📚 17. Evidence Package

The raw evidence is preserved under:

```text
results/raw/
│
├── 20260813-064832-task01-mac-m4/
│   ├── metadata.txt
│   ├── git-before.txt
│   ├── git-after.txt
│   ├── diff.patch
│   ├── pi-session.jsonl
│   ├── pi-session.html
│   └── tests.txt
│
└── 20260813-122237-task01-windows-rtx5060-llama/
    ├── metadata.txt
    ├── git-before.txt
    ├── git-after.txt
    ├── diff.patch
    ├── pi-session.jsonl
    ├── pi-session.html
    └── test/session evidence
```

The benchmark evidence hierarchy is:

```text
Raw repository state
        ↓
Raw agent session
        ↓
Raw command output
        ↓
Run metadata
        ↓
Processed metrics
        ↓
Human interpretation
```

Derived results must never overwrite raw evidence.

---

# 🔍 18. Reproducibility Checklist

For each published result, retain:

```text
☑ Task ID
☑ Run ID
☑ Starting Git SHA
☑ Benchmark branch / commit
☑ Hardware configuration
☑ Operating system
☑ Inference runtime/version
☑ Model identifier
☑ Model representation / quantization
☑ Context target
☑ Maximum output target
☑ Pi version
☑ Start timestamp
☑ End timestamp
☑ Agent session
☑ Tool trajectory
☑ Test output
☑ Final Git state
☑ Final patch
☑ Anomalies / environment issues
```

This makes the result auditable rather than just a screenshot of a benchmark number.

---

# 🏷️ 19. Publication-Friendly Result

> ### 🏆 Task 01 — 55K Context
>
> On a real MotionForge software-repair task, **Pi + Qwen3.6-27B** completed the recorded workload in **31m 01s on an RTX 5060 Ti + llama.cpp**, compared with **118m 51s on an M4 Pro + oMLX**.
>
> The RTX run used **80 tool calls and 2.16M total tokens**, while the M4 Pro run used **121 tool calls and 4.15M total tokens**.
>
> That is a **3.83× wall-clock difference** on this workload.
>
> ⚠️ This is an initial real-workload result, not a universal hardware ranking. The systems use different inference runtimes and model representations, and the Mac validation environment has a documented `pytest` collection issue.

---

# 🎯 20. Bottom Line

```text
                 REAL SOFTWARE REPAIR
                         │
                         ▼
             ┌─────────────────────┐
             │     Task 01 / 55K   │
             └──────────┬──────────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       🟢 RTX 5060 Ti         🔵 M4 Pro
          llama.cpp              oMLX
             │                     │
             ▼                     ▼
          31m 01s               118m 51s
             │                     │
             └──────────┬──────────┘
                        ▼
                   **3.83×**
```

The important research question is not simply:

> **“Which machine is faster?”**

It is:

> **“Why did two local coding-agent stacks take such different paths to solve the same real software problem?”**

That is the question the next rounds of LCAB can answer.

---

## 📌 Evidence Boundary

This document reports the current Task 01 / 55K benchmark as an **initial real-workload comparison**.

It deliberately separates:

- measured benchmark observations;
- validation limitations;
- configuration differences;
- engineering convergence;
- hypotheses for future investigation.

It does **not** claim a universal ranking of RTX 5060 Ti vs M4 Pro, llama.cpp vs oMLX, or any model quantization.

The benchmark's value is the reproducible, end-to-end measurement of a real coding-agent repair workload.
