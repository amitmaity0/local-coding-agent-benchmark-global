# 🤖 Task 01 — Agent & Tool Trajectory Analysis

> **From “how fast did it finish?” to “how much agent work did it take?”**
>
> This document is the trajectory-analysis layer of the LCAB publication. It examines the recorded Pi agent metrics for the **55K-context MotionForge repair** on the RTX 5060 Ti and M4 Pro configurations.
>
> It should be read after `results/task01-results.md` and `results/task01-analysis.md`.

---

# 🎯 1. Purpose

A conventional LLM benchmark can often be summarized with:

```text
tokens/sec
time-to-first-token
memory
context length
```

A coding-agent benchmark has another dimension:

```text
                    REAL SOFTWARE REPAIR
                            │
                            ▼
                     Agent trajectory
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          Context         Tools         Messages
          growth          calls         / turns
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                         Testing
                            │
                            ▼
                      Final patch
                            │
                            ▼
                       Wall time
```

Task 01 is useful because the two configurations produced **highly convergent engineering repairs**, while their recorded trajectories were substantially different.

---

# 📊 2. Recorded Trajectory Metrics

| Metric | 🟢 RTX 5060 Ti | 🔵 M4 Pro | M4 / RTX |
|---|---:|---:|---:|
| Wall time | **31m 01s** | **118m 51s** | **3.83×** |
| Messages | **166** | **237** | **1.43×** |
| Tool calls | **80** | **121** | **1.51×** |
| Input tokens | **2,124,213** | **4,110,678** | **1.94×** |
| Cached input | **1,921,422** | **3,719,168** | **1.94×** |
| Uncached input | **202,791** | **391,510** | **1.93×** |
| Output tokens | **36,318** | **39,044** | **1.08×** |
| Total tokens | **2,160,531** | **4,149,722** | **1.92×** |

The first major observation is:

> **The M4 Pro run processed almost twice as much input/total context and performed substantially more interactions, while producing only about 8% more output tokens.**

This is a trajectory observation. It is not, by itself, evidence that the additional interactions were unnecessary.

---

# ⏱️ 3. Wall Time vs Agent Work

```text
                         TASK 01
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        🟢 RTX 5060 Ti              🔵 M4 Pro
              │                           │
          31m 01s                    118m 51s
              │                           │
           166 msgs                    237 msgs
            80 tools                    121 tools
           2.16M tok                   4.15M tok
              │                           │
              └─────────────┬─────────────┘
                            ▼
                    Similar final repair
```

The benchmark therefore measures two things simultaneously:

### Runtime performance

How quickly the complete inference/runtime stack processes the agent workload.

### Trajectory efficiency

How much context, interaction and tool activity the agent requires to reach the repair.

These should not be conflated.

---

# 💬 4. Message Trajectory

The recorded message counts are:

```text
RTX → 166
M4  → 237
```

Difference:

```text
237 - 166 = 71 messages
```

Relative increase:

```text
237 / 166 ≈ 1.43×
```

So the M4 trajectory contains approximately:

> **43% more recorded messages.**

A message-count difference can arise from many causes:

- more repository exploration;
- more intermediate reasoning turns;
- more tool-result processing;
- more validation cycles;
- more retries;
- different agent decisions.

The aggregate metric cannot distinguish these categories.

Therefore this document does **not** label the additional messages as wasted work.

---

# 🛠️ 5. Tool-Call Trajectory

The recorded tool counts are:

```text
RTX: 80
M4:  121
```

Difference:

```text
41 additional tool calls
```

Relative increase:

```text
121 / 80 ≈ 1.51×
```

The M4 run therefore performed approximately:

> **51% more recorded tool interactions.**

A coding agent operates through a loop like:

```text
┌───────────────┐
│    Reason     │
└───────┬───────┘
        ▼
┌───────────────┐
│     Tool      │
└───────┬───────┘
        ▼
┌───────────────┐
│  Tool result  │
└───────┬───────┘
        ▼
┌───────────────┐
│ Update model  │
│    context    │
└───────┬───────┘
        │
        └──────────────► next turn
```

Every additional cycle can increase both execution time and subsequent context size.

But a tool call can also be highly productive. Tool count alone is therefore not a quality metric.

---

# 🧠 6. Context-Processing Trajectory

Input-token volume is the largest aggregate difference.

```text
RTX: 2,124,213
M4:  4,110,678
```

Ratio:

```text
4,110,678 / 2,124,213 ≈ 1.94×
```

Total tokens:

```text
RTX: 2,160,531
M4:  4,149,722
```

Ratio:

```text
4,149,722 / 2,160,531 ≈ 1.92×
```

This means the M4 trajectory processed approximately **1.9× the total token volume** recorded for RTX.

---

# 💾 7. Cached vs Uncached Context

The cache figures are:

```text
RTX
cached input   = 1,921,422
uncached input =   202,791

M4
cached input   = 3,719,168
uncached input =   391,510
```

Approximate cache share:

```text
RTX ≈ 90.5%
M4  ≈ 90.5%
```

This is an important observation:

```text
                 Cache share
RTX                 ~90.5%
M4                  ~90.5%
```

The difference is therefore primarily the **amount of context processed**, not simply whether caching was available.

The larger M4 trajectory generated more cached context because its overall interaction history was larger.

---

# ✍️ 8. Output Tokens Are Surprisingly Similar

Output tokens:

```text
RTX: 36,318
M4:  39,044
```

Ratio:

```text
39,044 / 36,318 ≈ 1.08×
```

So:

```text
Input tokens:   +94%
Output tokens:   +8%
```

This asymmetry is one of the most interesting trajectory observations in Task 01.

The M4 run did not produce dramatically more generated text. Instead, it processed dramatically more accumulated input/context.

---

# 🔬 9. Input-to-Output Amplification

A descriptive ratio is:

```text
input tokens / output tokens
```

### RTX

```text
2,124,213 / 36,318 ≈ 58.5
```

### M4

```text
4,110,678 / 39,044 ≈ 105.3
```

So the recorded trajectories have approximately:

```text
RTX → 58.5 input tokens / output token
M4  → 105.3 input tokens / output token
```

This should be called a **trajectory context-amplification indicator**, not a model-efficiency score.

Input tokens include:

- conversation history;
- tool results;
- repository content;
- repeated context;
- cached context.

---

# 🔄 10. Trajectory Model

A useful LCAB representation is:

```text
                    User task
                        │
                        ▼
                Repository discovery
                        │
                        ▼
                 Problem hypothesis
                        │
                        ▼
                  Tool interaction
                        │
                        ▼
                Context accumulation
                        │
                        ▼
                  Code modification
                        │
                        ▼
                     Testing
                        │
               ┌────────┴────────┐
               ▼                 ▼
             PASS              FAIL
               │                 │
               ▼                 ▼
            Continue          Diagnose
                                 │
                                 └──────► more context
                                          / tool calls
```

A longer path through this loop can create a compounding effect:

```text
More interactions
       ↓
More tool results
       ↓
More accumulated context
       ↓
Larger future inputs
       ↓
More context-processing work
```

Task 01's aggregate metrics are consistent with this pattern, but they do not prove that this exact mechanism caused the M4 result.

---

# 🧩 11. Why Patch Convergence Matters

The trajectory metrics become more interesting because the final engineering changes were highly convergent.

Both systems independently arrived at the same broad repair path:

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

This means the benchmark is not comparing:

```text
Good implementation
       vs
Completely different implementation
```

It is closer to:

```text
Different paths
       ↓
Similar engineering destination
```

That is exactly the situation in which trajectory metrics become valuable.

---

# ⚖️ 12. Solution Quality vs Trajectory Efficiency

Task 01 suggests separating two dimensions:

```text
                 Coding-agent performance
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
       Solution quality            Trajectory efficiency
             │                           │
      Correct repair?              How much work?
             │                           │
      Tests / patch                 tools / tokens
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    End-to-end time
```

The current Task 01 result can therefore be summarized as:

```text
Solution convergence  → HIGH
Trajectory convergence → LOW
```

This is an interpretation of the aggregate evidence, not a formal score.

---

# ⏱️ 13. Aggregate Time per Tool Call

A simple descriptive calculation:

### RTX

```text
31m 01s / 80
≈ 23.3 seconds/tool call
```

### M4

```text
118m 51s / 121
≈ 58.9 seconds/tool call
```

Ratio:

```text
58.9 / 23.3 ≈ 2.53×
```

⚠️ This is **not tool latency** and should not be presented as such.

A single tool call can contain:

- model generation;
- shell execution;
- filesystem operations;
- test execution;
- waiting;
- multiple internal operations.

It is only an aggregate **wall-time-per-recorded-tool-call indicator**.

---

# 📈 14. Trajectory Scorecard

| Dimension | 🟢 RTX | 🔵 M4 | Observation |
|---|---:|---:|---|
| Wall time | 31m 01s | 118m 51s | RTX much shorter |
| Messages | 166 | 237 | M4 +43% |
| Tool calls | 80 | 121 | M4 +51% |
| Input tokens | 2.12M | 4.11M | M4 +94% |
| Output tokens | 36.3K | 39.0K | M4 +8% |
| Total tokens | 2.16M | 4.15M | M4 +92% |
| Cache share | ~90.5% | ~90.5% | Similar |
| Final repair | Similar | Similar | Strong convergence |

---

# 🔬 15. What the Aggregate Data Can Establish

### Strong observations

The recorded data supports:

- RTX completed the benchmark faster.
- M4 generated more recorded messages.
- M4 used more recorded tool calls.
- M4 processed substantially more input tokens.
- M4 processed substantially more total tokens.
- Output-token counts were relatively close.
- Cache shares were approximately similar.
- The final engineering repairs were highly convergent.

### Claims that remain unproven

The aggregate data does **not** establish:

```text
More tools = worse agent
More tokens = worse reasoning
M4 hardware is slower by 3.83×
oMLX is slower than llama.cpp by 3.83×
M4 spent all extra time in inference
M4's extra trajectory was unnecessary
```

Those require controlled or turn-level measurements.

---

# 🔎 16. Where Did the Extra 87m 50s Go?

The wall-clock difference is:

```text
118m 51s
-
31m 01s
────────
87m 50s
```

The current aggregate data cannot allocate those 87m 50s.

A future trajectory parser should divide the run into:

```text
┌─────────────────────────────────┐
│         Total wall time         │
├─────────────────────────────────┤
│ Model generation                │
│ Context processing              │
│ Tool execution                  │
│ Test execution                  │
│ Repository / filesystem work    │
│ Agent waiting / idle            │
│ Runtime overhead                │
└─────────────────────────────────┘
```

That would turn an interesting observation into an explainable measurement.

---

# 🧪 17. Recommended Per-Turn Dataset

For future LCAB runs, record a row for every agent turn:

| Field | Example |
|---|---|
| `turn` | 42 |
| `timestamp_start` | `...` |
| `timestamp_end` | `...` |
| `event_type` | `tool_call` |
| `tool_name` | `shell` |
| `input_tokens` | `...` |
| `cached_input_tokens` | `...` |
| `output_tokens` | `...` |
| `context_tokens` | `...` |
| `elapsed_ms` | `...` |
| `command` | `pytest ...` |
| `exit_code` | `0` |
| `test_count` | `230` |

This would allow LCAB to identify exactly where trajectory divergence occurs.

---

# 🧭 18. Recommended Trajectory Pipeline

```text
             pi-session.jsonl
                    │
                    ▼
              parser / ETL
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Messages      Tool calls    Tokens
       │            │            │
       └────────────┼────────────┘
                    ▼
              Per-turn data
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Timing    Context    Errors
          │         │         │
          └─────────┼─────────┘
                    ▼
             trajectory.json
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
      Markdown    Charts   Summary
```

This should eventually be automated as part of LCAB rather than manually assembled for each publication.

---

# 📋 19. Proposed Trajectory Schema

A future machine-readable run record could contain:

```json
{
  "run_id": "20260813-122237-task01-windows-rtx5060-llama",
  "turns": 166,
  "tool_calls": 80,
  "input_tokens": 2124213,
  "cached_input_tokens": 1921422,
  "uncached_input_tokens": 202791,
  "output_tokens": 36318,
  "total_tokens": 2160531,
  "wall_seconds": 1861
}
```

A corresponding M4 record can then be compared mechanically.

The important design principle is:

> **Preserve raw session data and derive metrics from it; do not manually overwrite the raw evidence with computed summaries.**

---

# 🔬 20. Future Trajectory Metrics

Once per-turn data is available, LCAB should add:

| Metric | Purpose |
|---|---|
| ⏱️ Time to first tool call | Startup/agent activation cost |
| 🔍 Time to first repository inspection | Discovery latency |
| 🧩 Time to first code edit | Problem-understanding phase |
| 🧪 Time to first test | Validation strategy |
| ✅ Time to first passing test | Repair convergence |
| 🔄 Retry count | Recovery behavior |
| ❌ Failed tool-call count | Execution friction |
| 📚 Peak context size | Context pressure |
| 📈 Context growth rate | Context accumulation |
| 🛠️ Tools per successful edit | Interaction efficiency |
| 🧠 Tokens per successful edit | Context/agent efficiency |
| 🏁 Time to final patch | Repair convergence |
| 📦 Patch size | Engineering scope |

These metrics are potentially much more informative than a single tokens/sec figure.

---

# 🧪 21. Controlled Follow-Up Experiments

The trajectory findings suggest four immediate experiments.

## Experiment A — Repeatability

Run the same benchmark multiple times:

```text
RTX × 3
M4 × 3
```

Measure:

```text
mean
median
min/max
standard deviation
```

This determines whether Task 01 is representative or an outlier.

---

## Experiment B — Context Scaling

Run:

```text
16K
32K
55K
```

on both systems.

```text
                16K     32K     55K
RTX             A       B       C
M4              D       E       F
```

Plot:

```text
context size → wall time
context size → input tokens
context size → tool calls
```

This can test whether the observed difference grows with context.

---

## Experiment C — Trajectory Normalization

Compare repeated runs and classify each turn:

```text
discovery
inspection
editing
testing
recovery
completion
```

Then determine whether one configuration systematically produces more work in a specific phase.

---

## Experiment D — Runtime Isolation

Where technically practical, keep the model and agent configuration as constant as possible while changing only the inference backend.

This is difficult across Windows/NVIDIA and Apple Silicon, but it would provide stronger evidence about runtime effects.

---

# 🧠 22. Research Question Emerging from Task 01

Task 01 suggests a more interesting question than:

> **Which GPU is faster?**

Instead:

> **How efficiently does a local coding-agent stack transform context, tool interactions and model inference into a correct software repair?**

A conceptual LCAB efficiency model is:

```text
                 Agent Efficiency
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   Context cost     Tool cost      Inference cost
       │               │               │
       └───────────────┼───────────────┘
                       ▼
                 Repair outcome
                       │
                       ▼
                  Wall-clock
```

This is a research direction, not yet a formal benchmark score.

---

# 🏷️ 23. Publication-Ready Finding

> ### 🤖 The trajectory was almost as important as the clock.
>
> On the same real MotionForge repair, the RTX configuration completed the 55K-context run in **31m 01s using 80 tool calls and 2.16M total tokens**. The M4 Pro configuration took **118m 51s, 121 tool calls and 4.15M total tokens**.
>
> The M4 trajectory therefore contained approximately **1.51× the tool interactions and 1.92× the total token processing**, while producing only **1.08× the output tokens**.
>
> Because the two configurations converged on highly similar engineering repairs, Task 01 suggests that real coding-agent benchmarks should measure **trajectory efficiency and context amplification**, not only model generation speed.

---

# ⚠️ 24. Evidence Boundary

This document intentionally distinguishes between:

### Directly measured

```text
wall time
messages
tool calls
input tokens
cached input
uncached input
output tokens
total tokens
```

and:

### Future measurements

```text
per-turn inference time
tool duration
context growth
retry classification
test duration
repository exploration phase
```

The current aggregate data does **not** allow the 87m 50s wall-time difference to be causally decomposed.

It also does not establish that the M4 agent was inefficient.

The defensible statement is:

> **The M4 configuration required substantially more recorded interaction and context processing to complete this particular benchmark workload.**

---

# 🎯 25. Bottom Line

```text
                  TASK 01
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
       🟢 RTX                  🔵 M4
          │                     │
       80 tools              121 tools
       2.16M tokens          4.15M tokens
       31m 01s               118m 51s
          │                     │
          └──────────┬──────────┘
                     ▼
              Similar repair
```

The central lesson from Task 01 is:

> **A real coding-agent benchmark needs to measure not only whether an agent solves the task, but how much context, interaction and time it consumes while doing so.**

The next-generation LCAB trajectory collector should therefore preserve the complete Pi session and derive **per-turn timing, context growth, tool duration, validation cycles and recovery behavior** automatically.

That would allow future publications to move from:

```text
“Machine A finished in X minutes.”
```

to:

```text
“Machine A finished faster because its coding-agent
trajectory used less context, fewer interactions,
and/or lower per-turn processing time.”
```

The second statement is the level of explanation LCAB should ultimately aim to support.
