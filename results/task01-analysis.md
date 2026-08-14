# 🔬 Task 01 — Benchmark Analysis

> **Interpreting the 55K real software-repair result**
>
> This document is the analytical companion to [`results/task01-results.md`](task01-results.md). The results document records **what happened**; this document examines **what the measurements may mean**, what can and cannot be inferred, and which hypotheses should be tested next.

---

## 🧭 1. Analysis Scope

Task 01 compares two complete local coding-agent configurations on the same MotionForge repair workload:

```text
🟢 Windows + RTX 5060 Ti + llama.cpp
                 │
                 ▼
          Qwen3.6-27B
                 │
                 ▼
             Pi 0.84.1
                 │
                 ▼
              55K
```

versus:

```text
🔵 macOS + M4 Pro + oMLX
                 │
                 ▼
          Qwen3.6-27B
                 │
                 ▼
             Pi 0.84.1
                 │
                 ▼
              55K
```

The measured wall-clock result is:

```text
RTX: 31m 01s
M4:  118m 51s

M4 / RTX ≈ 3.83×
```

The purpose of this document is **not** to turn that observation into an unsupported hardware ranking.

Instead, the analysis asks:

> **What changed between the two runs, and what does that tell us about real local coding-agent performance?**

---

# 🏆 2. The Main Finding

The most important observation is not simply:

> **RTX was 3.83× faster.**

The more interesting finding is:

```text
                 SAME REPAIR
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
        RTX                    M4
          │                     │
      31m 01s                118m 51s
          │                     │
      80 tools               121 tools
      2.16M tokens           4.15M tokens
          │                     │
          └──────────┬──────────┘
                     ▼
              Similar repair
```

The two configurations appear to have reached essentially the same engineering destination, but the M4 run traversed a substantially larger interaction/context path.

That creates a useful benchmark distinction:

> **Solution convergence can be high even when trajectory efficiency is very different.**

---

# 📊 3. The Performance Difference Has Multiple Components

The wall-clock ratio is:

```text
118m 51s / 31m 01s ≈ 3.83×
```

But the agent workload is also different.

| Dimension | RTX | M4 | M4 / RTX |
|---|---:|---:|---:|
| Wall time | 31m 01s | 118m 51s | **3.83×** |
| Messages | 166 | 237 | **1.43×** |
| Tool calls | 80 | 121 | **1.51×** |
| Input tokens | 2.12M | 4.11M | **1.94×** |
| Total tokens | 2.16M | 4.15M | **1.92×** |
| Output tokens | 36.3K | 39.0K | **1.08×** |

This means the experiment does **not** isolate one bottleneck.

The total result is better represented as:

```text
End-to-end repair time
        │
        ├── inference performance
        ├── context processing
        ├── agent trajectory
        ├── tool execution
        ├── testing
        └── environment/runtime overhead
```

The current data measures the sum.

---

# 🧠 4. Context Volume Is the Most Striking Difference

Input tokens nearly doubled:

```text
RTX: 2,124,213
M4:  4,110,678
```

Ratio:

```text
≈ 1.94×
```

Total tokens show the same pattern:

```text
RTX: 2,160,531
M4:  4,149,722

≈ 1.92×
```

Yet output tokens are relatively close:

```text
RTX: 36,318
M4:  39,044

≈ 1.08×
```

This produces an important asymmetry:

```text
                 RTX        M4
Input           2.12M      4.11M
Output          36.3K      39.0K

Input growth:              +94%
Output growth:              +8%
```

### Interpretation

The M4 run's additional token burden is overwhelmingly on the **input/context side**.

That is exactly the dimension that becomes important in long-context coding-agent workloads.

---

# 💾 5. Cache Behavior Does Not Explain the Difference by Itself

Both runs have approximately the same cached-input proportion:

```text
RTX:
1,921,422 / 2,124,213 ≈ 90.5%

M4:
3,719,168 / 4,110,678 ≈ 90.5%
```

So:

```text
                Cache share
RTX              ~90.5%
M4               ~90.5%
```

The distinction is the **amount of context being processed**, not simply whether context was cached.

A useful conceptual model is:

```text
Cache efficiency
       +
Total context volume
       ↓
Actual context-processing workload
```

Task 01 changes both the agent trajectory and total context volume, so cache percentage alone is insufficient to characterize performance.

---

# 🛠️ 6. Tool-Interaction Difference

The M4 run made:

```text
121 tool calls
```

versus:

```text
80 tool calls
```

for RTX.

That is:

```text
+41 tool calls
≈ +51%
```

This matters because an agent run is a repeated control loop:

```text
Model
  ↓
Tool
  ↓
Tool result
  ↓
Model
  ↓
Tool
  ↓
...
```

Every additional cycle can increase:

- wall-clock time;
- context size;
- tool-result accumulation;
- test execution;
- repository exploration.

However:

> **More tool calls do not automatically mean worse agent behavior.**

An additional tool call can be necessary and productive.

Therefore the correct statement is:

> The M4 run had a substantially larger interaction trajectory.

Not:

> The M4 agent reasoned inefficiently.

The latter requires turn-level analysis.

---

# 🔎 7. Message Count Shows the Same Pattern

The M4 run recorded:

```text
237 messages
```

versus:

```text
166 messages
```

for RTX.

That is:

```text
+71 messages
≈ +43%
```

Together with the tool-call difference:

```text
RTX → 166 messages / 80 tools
M4  → 237 messages / 121 tools
```

the evidence strongly supports a longer M4 interaction path.

But again, this is **trajectory evidence**, not a causal explanation for the 3.83× wall-time difference.

---

# 🧩 8. Why Patch Convergence Matters

The engineering changes are unusually useful for interpreting the benchmark.

Both runs converged on the same basic architecture:

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
```

The RTX and M4 55K benchmark branches have similar core production changes:

| Area | RTX | M4 55K |
|---|---:|---:|
| `orchestrator/engine.py` | +3 / -1 | +4 / -1 |
| `services/workflow.py` | +22 / -2 | +20 / -2 |
| Autonomous-loop tests | +525 / -1 | +463 / -1 |
| Sidecar tests | +9 | +10 |
| Workflow tests | +46 / -1 | +49 |
| LTX sidecar | +6 / -1 | +6 / -1 |

This does not prove identical reasoning.

But it does show strong **solution convergence**.

---

# 🧠 9. Solution Quality vs Trajectory Efficiency

This suggests two distinct benchmark dimensions:

```text
                Coding-Agent Performance
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      Solution quality          Trajectory efficiency
            │                         │
       Did it repair?           How much work?
            │                         │
       Tests / patch             tools / tokens
            │                         │
            └────────────┬────────────┘
                         ▼
                  End-to-end time
```

Task 01 appears to show:

```text
Solution convergence: HIGH
Trajectory convergence: LOW
```

That is an important result.

A benchmark that only records final correctness would miss most of this difference.

---

# ⚡ 10. Why 3.83× Wall Time Is Larger Than the 1.92× Token Difference

This is one of the most important questions raised by Task 01.

The M4 run has approximately:

```text
1.92× total tokens
```

but:

```text
3.83× wall time
```

Therefore token volume alone does not explain the observed wall-clock ratio.

Possible contributors include:

```text
1. Larger context-processing cost
2. Different inference-runtime characteristics
3. Different model representation
4. More tool interactions
5. More repository/test activity
6. Different per-turn latency
7. Different trajectory structure
8. Environment/runtime overhead
```

The current experiment cannot assign a percentage contribution to these factors.

That is precisely why the next benchmark phase should capture **per-turn timing**.

---

# 🧪 11. The Most Important Missing Measurement

The current aggregate data tells us:

```text
RTX = 31m
M4  = 119m
```

But it does not tell us exactly where the difference accumulated.

Future LCAB runs should divide elapsed time into:

```text
┌─────────────────────────────┐
│        Total wall time      │
├─────────────────────────────┤
│ Model generation            │
│ Context processing          │
│ Tool execution              │
│ Test execution              │
│ File/system operations      │
│ Agent waiting / idle        │
│ Other runtime overhead      │
└─────────────────────────────┘
```

This would transform the benchmark from:

> **“Which system finished faster?”**

into:

> **“Where does each system spend its time?”**

That is a much stronger research instrument.

---

# 🔬 12. Hypotheses to Test

## H1 — Long-context processing dominates

If true:

```text
As context grows:
M4 time increases faster than RTX time
```

Test:

```text
16K
32K
55K
```

using otherwise identical workloads.

---

## H2 — Agent trajectory dominates

If true:

```text
Same hardware/runtime
Different trajectory
        ↓
Large wall-time difference
```

Test with repeated runs and trajectory normalization.

---

## H3 — Runtime implementation matters

If true:

```text
Same model
Same agent
Different runtime
        ↓
Large end-to-end difference
```

Test by comparing equivalent runtime/model configurations where practical.

---

## H4 — Quantization/model representation matters

Current configurations are not bit-for-bit equivalent:

```text
RTX → 4.5bpw pure GGUF
M4  → oQ4-MTP
```

A future controlled experiment should explicitly document the model representation and, where possible, compare equivalent quantization.

---

## H5 — Agent stochasticity contributes significantly

Repeated runs may produce:

```text
Run A → 30 min
Run B → 45 min
Run C → 32 min
```

even on the same machine.

If variance is large, a single run cannot support strong ranking claims.

---

# 📐 13. What Should Be Controlled Next?

The strongest next experiment would hold constant:

```text
Repository baseline
Task prompt
Pi version
Model weights
Model quantization
Context target
Maximum output
Sampling parameters
Agent configuration
Tool environment
Test environment
```

and vary **one factor at a time**.

For example:

```text
Experiment A
RTX + llama.cpp + 16K

Experiment B
RTX + llama.cpp + 32K

Experiment C
RTX + llama.cpp + 55K
```

Then repeat:

```text
M4 + oMLX + 16K
M4 + oMLX + 32K
M4 + oMLX + 55K
```

This would produce a much more scientifically useful context-scaling curve.

---

# 📈 14. Recommended Benchmark Matrix

```text
                 Context
              16K   32K   55K
             ┌─────┬─────┬─────┐
RTX + llama  │  A  │  B  │  C  │
             ├─────┼─────┼─────┤
M4 + oMLX    │  D  │  E  │  F  │
             └─────┴─────┴─────┘
```

Then repeat selected cells:

```text
A × 3
C × 3
D × 3
F × 3
```

This separates:

- hardware/runtime behavior;
- context scaling;
- run-to-run variance.

---

# ⚠️ 15. The Validation Caveat Must Stay Visible

The Mac run has a documented test-environment issue:

```text
pytest: command not found
```

while the session evidence reports:

```text
227 tests passed
```

The RTX run records:

```text
230 tests + compileall
```

Therefore the publication should avoid a simplistic:

```text
RTX = pass
M4 = fail
```

classification.

The correct current status is:

| System | Current evidence |
|---|---|
| RTX | 🟢 230 tests + compileall |
| M4 | 🟡 227 tests reported, test collection artifact has missing `pytest` |

Before using validation as a primary ranking metric, normalize the environment.

---

# 🧱 16. What the Unlimited-Context Run Means

The repository also contains an M4 Pro unlimited-context experiment.

It should be treated separately.

The unlimited branch changed substantially more implementation code than the RTX and M4-55K branches, including additional engine and web-route behavior.

Therefore:

```text
M4 55K
   vs
M4 unlimited
```

is useful as an **agent/context-management experiment**, but not as a clean context-window-only comparison unless the implementation differences are accounted for.

This distinction is important for publication integrity.

---

# 📊 17. Current Evidence Strength

| Claim | Evidence strength |
|---|---|
| RTX completed faster on Task 01 | 🟢 Strong |
| Wall-clock ratio ≈ 3.83× | 🟢 Strong |
| M4 used more tool calls | 🟢 Strong |
| M4 processed more context | 🟢 Strong |
| Output volumes were relatively similar | 🟢 Strong |
| Final engineering approaches converged | 🟢 Strong |
| RTX hardware itself is 3.83× faster | 🔴 Unsupported |
| llama.cpp is universally faster than oMLX | 🔴 Unsupported |
| M4 agent was “worse” | 🟠 Not established |
| Extra context caused all extra latency | 🟠 Not established |
| Hardware caused all extra latency | 🔴 Unsupported |

This table should guide the wording of any public article.

---

# 🏷️ 18. Recommended Public Framing

### Strong framing

> **On a real MotionForge repair workload, the RTX 5060 Ti + llama.cpp configuration completed the recorded 55K-context coding-agent run in 31 minutes, compared with 119 minutes for the M4 Pro + oMLX configuration. The M4 run also generated a substantially larger interaction/context trajectory, making this an interesting example of why local coding-agent benchmarks should measure end-to-end repair behavior rather than standalone tokens/sec.**

### Avoid

> **The RTX 5060 Ti is 3.83× faster than Apple's M4 Pro for coding.**

The second statement overclaims what the experiment can establish.

---

# 🔎 19. The Strongest Research Story

The strongest story emerging from Task 01 is:

```text
                SAME REAL TASK
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
        RTX                       M4
          │                         │
      31 minutes               119 minutes
          │                         │
     2.16M tokens             4.15M tokens
          │                         │
      80 tools                 121 tools
          │                         │
          └────────────┬────────────┘
                       ▼
                Similar repair
```

Therefore:

> **Local coding-agent performance is a property of the entire agent/inference/runtime/hardware stack, not simply a property of model tokens-per-second.**

Task 01 is an initial demonstration of that principle.

---

# 🚀 20. What This Enables for LCAB

Task 01 suggests that future LCAB reports should have four layers:

```text
Layer 1 — Hardware
    VRAM / RAM / CPU / GPU

Layer 2 — Inference
    prompt throughput / generation / context processing

Layer 3 — Agent
    messages / tools / retries / context amplification

Layer 4 — Software repair
    success / tests / patch / wall time
```

The final benchmark report can then show:

```text
Hardware → Inference → Agent → Repair
```

rather than a single tokens/sec number.

That is the central methodological opportunity for this project.

---

# 🧪 21. Recommended Next Measurement Set

For every future benchmark run, collect:

### Timing

```text
start_timestamp
end_timestamp
wall_seconds
per-turn duration
model generation duration
tool duration
test duration
```

### Agent

```text
message_count
tool_call_count
failed_tool_calls
retry_count
compaction_count
context_tokens_per_turn
```

### Tokens

```text
input_tokens
cached_input_tokens
uncached_input_tokens
output_tokens
total_tokens
```

### System

```text
peak_vram
peak_ram
gpu_utilization
cpu_utilization
power
```

### Software result

```text
tests_before
tests_after
tests_passed
tests_failed
patch_size
files_changed
final_git_sha
```

This would allow LCAB to move from a benchmark report to a genuine **local coding-agent measurement framework**.

---

# 🎯 22. Final Analysis

Task 01 should be interpreted as an **initial signal**, not a universal hardware verdict.

The strongest evidence is:

```text
RTX + llama.cpp
31m 01s
80 tool calls
2.16M total tokens

             VS

M4 + oMLX
118m 51s
121 tool calls
4.15M total tokens
```

The final repair approaches were highly convergent.

The most interesting difference therefore lies in:

```text
trajectory
context volume
interaction count
runtime behavior
```

The central unresolved question is:

> **Why does the M4 configuration require almost twice the token processing and 51% more tool interactions, yet ultimately produce a similar repair?**

Answering that question requires the next generation of LCAB measurements: per-turn timing, context growth, tool duration, repeated runs, and controlled context-scaling experiments.

---

## 📌 Evidence Boundary

This analysis is derived from the recorded Task 01 aggregate benchmark results, benchmark branch comparisons, preserved agent-session artifacts, and documented validation evidence.

Where the evidence directly establishes a measurement, it is presented as a result.

Where the evidence supports only a possible explanation, it is presented as a hypothesis.

No causal claim is made about hardware, runtime, quantization, or agent behavior that cannot be isolated by the current experiment.
