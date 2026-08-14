# 🤖 Task 01 — Agent Trajectory Analysis

> **Pi + Qwen3.6-27B on a real MotionForge repair**
>
> This document analyzes the agent-side execution trajectory behind Task 01: interaction count, context consumption, tool usage, and the relationship between the final patch and the path taken to reach it.

## 🎯 1. Why Agent Trajectory Matters

A conventional local-LLM benchmark emphasizes tokens/sec and memory. A coding-agent benchmark must also measure:

```text
REAL SOFTWARE REPAIR
        │
        ▼
 Agent trajectory
        │
 ┌──────┼────────┐
 ▼      ▼        ▼
Context Tools  Iterations
growth  calls  / recovery
 │      │        │
 └──────┼────────┘
        ▼
   Final repair
        │
        ▼
  Wall-clock time
```

Task 01 is particularly useful because the two configurations reached highly similar engineering solutions while their trajectories were substantially different.

---

## 📊 2. Recorded Trajectory Metrics

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

The key observation is:

> **The M4 Pro trajectory processed almost twice as much input/total context and performed substantially more interactions, while producing only about 8% more output tokens.**

---

## ⏱️ 3. Wall Time vs Agent Activity

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

This separates two questions:

- **Inference/runtime speed:** how quickly the stack processes work.
- **Agent efficiency:** how much work the agent needs to perform.

Task 01 measures both simultaneously.

---

## 🔢 4. Message Efficiency

The M4 run produced **237 messages** versus **166** for RTX:

```text
237 - 166 = 71 additional messages
237 / 166 ≈ 1.43×
```

The M4 trajectory therefore contains approximately **43% more recorded messages**.

This does **not** prove that every additional message was unnecessary; it establishes that the recorded interaction path was longer.

---

## 🛠️ 5. Tool-Call Efficiency

```text
RTX: 80
M4:  121

121 - 80 = 41
121 / 80 ≈ 1.51×
```

The M4 trajectory performed approximately **51% more tool calls**.

This matters because coding agents repeatedly cross the boundary between:

```text
LLM inference
      ↕
shell / filesystem / git / tests
```

Every additional interaction can contribute to end-to-end latency.

---

## 🧠 6. Context Consumption

Input tokens:

```text
RTX: 2,124,213
M4:  4,110,678
```

Therefore:

```text
4,110,678 / 2,124,213 ≈ 1.94×
```

Total tokens:

```text
RTX: 2,160,531
M4:  4,149,722
```

Therefore:

```text
4,149,722 / 2,160,531 ≈ 1.92×
```

The M4 trajectory required nearly **twice the total token processing**.

---

## 💾 7. Cached Context

Both runs have approximately the same cache share:

```text
RTX:
1,921,422 / 2,124,213 ≈ 90.5%

M4:
3,719,168 / 4,110,678 ≈ 90.5%
```

This is important.

The difference is not primarily that one trajectory had caching while the other did not.

Instead:

```text
Both
 │
 ├── ~90.5% cached input
 │
 ▼
Different total amount of context processed
```

---

## ✍️ 8. Output Tokens Tell a Different Story

```text
RTX: 36,318
M4:  39,044
```

The M4 run generated only about:

```text
39,044 / 36,318 ≈ 1.08×
```

the RTX output.

So the experiment shows an unusual asymmetry:

```text
Input tokens:   +94%
Output tokens:   +8%
```

The extra work is therefore overwhelmingly on the **input/context side**, not output generation volume.

---

## 🔬 9. Context Amplification Indicator

A descriptive ratio is:

```text
input tokens / output tokens
```

RTX:

```text
2,124,213 / 36,318 ≈ 58.5
```

M4:

```text
4,110,678 / 39,044 ≈ 105.3
```

The M4 run processed roughly **105 input tokens per output token**, versus roughly **59** for RTX.

⚠️ This is **not** a pure model-efficiency metric. Input tokens include conversation history, tool results, repository information and repeated context. It is best treated as a trajectory-level context-amplification indicator.

---

## 🧩 10. Why the Result Is Interesting

The final engineering repair was highly convergent:

```text
Experiment.steps
      ↓
Engine.generate()
      ↓
WorkflowLoader.set_steps()
      ↓
LTX sidecar
      ↓
node 206
```

Yet:

```text
RTX → 80 tools → 2.16M tokens → 31m
M4  → 121 tools → 4.15M tokens → 119m
```

This suggests that the major performance difference is associated with the **trajectory to the solution**, not simply the complexity of the final patch.

This is an observation, not proof of causality.

---

## ⚠️ 11. Do Not Interpret 3.83× as Pure GPU Speed

The measured wall-clock ratio:

```text
118m 51s / 31m 01s ≈ 3.83×
```

should **not** be published as:

> “The RTX GPU is 3.83× faster than the M4 Pro.”

The experiment simultaneously changes:

```text
hardware
operating system
inference runtime
model representation
agent trajectory
context volume
tool-call count
```

The defensible quantity is:

> **End-to-end repair time for two complete local coding-agent configurations.**

---

## 🔍 12. What Could Explain the Extra M4 Work?

The aggregate evidence supports several possibilities, but does not establish their individual contributions.

| Possible factor | Evidence / interpretation |
|---|---|
| Repository exploration | More messages and tool calls may indicate a longer discovery path |
| Context accumulation | More interaction history can create larger subsequent prompts |
| Runtime behavior | RTX uses llama.cpp; M4 uses oMLX/MLX |
| Model representation | RTX uses 4.5bpw GGUF; M4 uses oQ4-MTP |
| Agent stochasticity | Tool outputs and sampling can change trajectories |
| Validation behavior | Different testing/recovery paths can add interactions |

These should be tested experimentally rather than inferred from the aggregate counts.

---

## 📈 13. Proposed LCAB Trajectory Metrics

Task 01 suggests adding two descriptive metrics.

### Context Amplification Ratio

```text
CAR = run input tokens / reference input tokens
```

Using RTX as the reference:

```text
M4 CAR ≈ 1.94×
```

### Tool Interaction Amplification

```text
TIA = run tool calls / reference tool calls
```

Using RTX as the reference:

```text
M4 TIA ≈ 1.51×
```

These metrics complement raw tokens/sec because they measure **how much work the agent generated**, not merely how quickly the backend generated tokens.

---

## 🧮 14. Aggregate Interaction Density

A simple descriptive calculation gives:

```text
RTX:
31m 01s / 80 ≈ 23.3 seconds per tool call

M4:
118m 51s / 121 ≈ 58.9 seconds per tool call
```

This is **not inference latency**. A tool call can include generation, shell execution, filesystem operations, tests and waiting.

Nevertheless, it shows that the complete M4 trajectory consumed approximately **2.53× more wall time per recorded tool call**.

---

## 📊 15. Trajectory Scorecard

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

## 🔬 16. Core Research Finding

The strongest defensible observation is:

> **Task 01 produced substantially different agent trajectories despite producing highly convergent final engineering solutions.**

```text
          TRAJECTORY                         OUTCOME

RTX ────────┐
            │
            ├──────────────► Similar repair
            │
M4 ─────────┘

RTX → 80 tools → 2.16M tokens → 31m
M4  → 121 tools → 4.15M tokens → 119m
```

This is precisely the kind of behavior that a real coding-agent benchmark can expose and a pure inference benchmark cannot.

---

## ⚠️ 17. What This Dataset Cannot Establish

Task 01 cannot isolate:

```text
GPU effect
CPU effect
runtime effect
quantization effect
model-format effect
agent stochasticity
context-length effect
```

because these variables were not independently controlled.

It also cannot establish:

```text
more tool calls = worse agent
```

or:

```text
more tokens = inefficient reasoning
```

The correct conclusion is narrower:

> **The M4 run required substantially more recorded interaction and context processing to complete this particular repair.**

---

## 🧪 18. Recommended Follow-Up Experiment

For future runs, LCAB should generate a per-turn table:

| Turn | Timestamp | Event | Tool | Input tok | Output tok | Elapsed | Context |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | … | reasoning | — | … | … | … | … |
| 2 | … | repository inspection | shell | … | … | … | … |
| 3 | … | file read | tool | … | … | … | … |
| 4 | … | edit | tool | … | … | … | … |
| 5 | … | test | shell | … | … | … | … |

This would allow LCAB to answer:

> **Where exactly did the extra 87m 50s accumulate?**

Possible categories:

```text
Inference generation
Context processing
Tool execution
Testing
Repository exploration
Agent recovery
Waiting / service latency
```

---

## 🧭 19. Recommended Trajectory Pipeline

```text
pi-session.jsonl
       │
       ▼
trajectory parser
       │
       ├── turn count
       ├── tool calls
       ├── timestamps
       ├── input tokens
       ├── output tokens
       ├── cache tokens
       ├── tool duration
       ├── test commands
       ├── failed commands
       └── context size
       │
       ▼
trajectory.json
       │
       ├── trajectory.md
       ├── charts
       └── benchmark summary
```

This should eventually become an automated LCAB reporting stage.

---

## 📋 20. Proposed Machine-Readable Trajectory Schema

```json
{
  "run_id": "20260813-122237-task01-windows-rtx5060-llama",
  "turns": 166,
  "tool_calls": 80,
  "input_tokens": 2124213,
  "output_tokens": 36318,
  "cached_input_tokens": 1921422,
  "uncached_input_tokens": 202791,
  "total_tokens": 2160531,
  "wall_seconds": 1861
}
```

The corresponding M4 record can then be compared mechanically.

---

## 🏆 21. Publication-Ready Finding

> ### 🤖 The interesting result was the trajectory, not just the clock.
>
> On the same real MotionForge repair, the RTX configuration completed the task in **31m 01s using 80 tool calls and 2.16M total tokens**. The M4 Pro configuration took **118m 51s, 121 tool calls and 4.15M total tokens**.
>
> The final engineering patches were highly convergent, but the M4 run processed **~1.94× more input tokens** and made **~1.51× more tool calls**, while producing only **~1.08× more output tokens**.
>
> This suggests that real coding-agent benchmarking should measure **trajectory efficiency and context amplification**, not only model generation speed.

---

## 🎯 22. Bottom Line

```text
                  CODING AGENT PERFORMANCE
                             │
             ┌───────────────┴───────────────┐
             ▼                               ▼
       SOLUTION QUALITY                 TRAJECTORY
             │                               │
       Similar repair                  Very different
             │                               │
             │                    ┌──────────┼──────────┐
             │                    ▼          ▼          ▼
             │                 Tools      Tokens      Time
             │                    │          │          │
             │                 80/121    2.16/4.15M 31/119m
             │                    │          │          │
             └────────────────────┴──────────┴──────────┘
```

### Emerging LCAB thesis

> **For local coding agents, the fastest system is not necessarily the system with the highest standalone token throughput. What matters is how efficiently the entire agent trajectory converts context, tool interactions and inference into a correct software repair.**

Task 01 provides an initial real-world example of why that distinction deserves to be measured explicitly.

---

## 📚 Evidence Boundary

This analysis uses the recorded Task 01 aggregate benchmark metrics and the preserved Pi session artifacts in the benchmark repository.

Where a conclusion depends on aggregate counts, it is stated as an observation.

Where a claim would require turn-by-turn session reconstruction, it is explicitly presented as a **future measurement**, rather than inferred from aggregate data.

That distinction keeps LCAB publication results reproducible and defensible.
