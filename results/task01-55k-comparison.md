# 📊 Task 01 --- 55K Context Comparison

> **RTX 5060 Ti + llama.cpp vs Apple M4 Pro + oMLX/MLX**\
> Real software-repair benchmark using **Pi + Qwen3.6-27B** on the
> MotionForge repository.

## 🏁 Executive Summary

This experiment compares two local coding-agent systems on the same real
software-repair workload:

``` text
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

  Metric                         🟢 RTX 5060 Ti                🔵 M4 Pro
  ---------------- ---------------------------- ------------------------
  Runtime                             llama.cpp               oMLX / MLX
  Agent                               Pi 0.84.1                Pi 0.84.1
  Context target                            55K                      55K
  Wall time                         **31m 01s**             **118m 51s**
  Tool calls                             **80**                  **121**
  Messages                              **166**                  **237**
  Input tokens                    **2,124,213**            **4,110,678**
  Cached input                    **1,921,422**            **3,719,168**
  Uncached input                    **202,791**              **391,510**
  Output tokens                      **36,318**               **39,044**
  Total tokens                    **2,160,531**            **4,149,722**
  Validation         **230 tests + compileall**   **227 tests reported**

The RTX run completed the recorded repair in approximately **3.83× less
wall-clock time** than the 55K M4 Pro run.

> ⚠️ This is a **complete-stack result**, not a universal hardware
> ranking. The two systems use different inference runtimes and model
> representations, and the Mac validation environment has a documented
> collection issue.

------------------------------------------------------------------------

# 🧪 1. What Was Tested?

The workload is a real software-repair task from the **MotionForge**
project.

The benchmark starts from the same repository revision:

``` text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

The two recorded runs are:

  System           Run ID
  ---------------- ------------------------------------------------
  🔵 Mac M4 Pro    `20260813-064832-task01-mac-m4`
  🟢 Windows RTX   `20260813-122237-task01-windows-rtx5060-llama`

Both runs preserve repository state, agent-session data, metadata and
resulting patches. The Mac metadata records oMLX, Pi,
Qwen3.6-27B-oQ4-MTP, a 55,000-token context window and 18,384 maximum
output tokens. fileciteturn37file0 The RTX metadata records
llama.cpp, Pi, Qwen3.6-27B-MTP-4.5bpw-pure.gguf, the same 55,000-token
context target and 18,384 maximum output tokens. fileciteturn40file0
Both runs began from the same baseline SHA. fileciteturn39file0
fileciteturn42file0

------------------------------------------------------------------------

# 🖥️ 2. Systems

## 🟢 RTX 5060 Ti

``` text
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
Qwen3.6-27B — 4.5 bpw pure GGUF
      │
      ▼
Pi 0.84.1
```

## 🔵 M4 Pro

``` text
macOS
      │
      ▼
Apple M4 Pro — 64 GB unified memory
      │
      ▼
oMLX / MLX
      │
      ▼
Qwen3.6-27B — oQ4-MTP
      │
      ▼
Pi 0.84.1
```

The two systems therefore share the coding-agent/model-family/workload
concept but use different hardware architectures, operating systems,
inference runtimes and model representations.

------------------------------------------------------------------------

# ⏱️ 3. Wall-Clock Result

``` text
RTX 5060 Ti   ████████                     31m 01s
M4 Pro        ███████████████████████████ 118m 51s
```

### Relative result

``` text
118m 51s / 31m 01s ≈ 3.83×
```

The M4 Pro run took approximately **87m 50s longer**.

Equivalently, the RTX run completed the recorded workload in
approximately **26% of the M4 Pro wall-clock time**.

This is the most striking result in the current experiment.

------------------------------------------------------------------------

# 🔢 4. Agent Trajectory

  Metric            🟢 RTX   🔵 M4 Pro
  --------------- -------- -----------
  Messages             166         237
  Tool calls            80         121
  Input tokens       2.12M       4.11M
  Output tokens      36.3K       39.0K
  Total tokens       2.16M       4.15M

The M4 Pro run consumed approximately:

``` text
1.42× more messages
1.51× more tool calls
1.94× more input tokens
1.92× more total tokens
```

while producing only approximately:

``` text
1.08× more output tokens
```

The wall-time difference is therefore **not explained simply by
output-token volume**. A substantial difference appears in the
interaction trajectory itself:

``` text
More input context
        +
More messages
        +
More tool calls
        +
Longer agent trajectory
        ↓
Much longer end-to-end repair time
```

This is an observation from the recorded runs, not yet a causal
conclusion.

------------------------------------------------------------------------

# 🧠 5. Token Accounting

## RTX

``` text
Input:       2,124,213
 ├─ cached:  1,921,422
 └─ uncached: 202,791

Output:         36,318
Total:       2,160,531
```

## M4 Pro

``` text
Input:       4,110,678
 ├─ cached:  3,719,168
 └─ uncached: 391,510

Output:         39,044
Total:       4,149,722
```

  Metric                 RTX    M4 Pro
  ---------------- --------- ---------
  Cached input         1.92M     3.72M
  Cache share        \~90.5%   \~90.5%
  Uncached input      202.8K    391.5K

The two runs show a similar proportion of cached input while the M4 Pro
trajectory processes almost twice as much total context.

------------------------------------------------------------------------

# 🛠️ 6. Tool-Use Behavior

``` text
Tool calls

RTX 5060 Ti
████████████████ 80

M4 Pro
████████████████████████ 121
```

The M4 Pro run made **41 more tool calls**, or approximately **51%
more**.

This is important because real coding-agent performance depends on
convergence behavior, not just raw model throughput.

------------------------------------------------------------------------

# 🧪 7. Validation Results

## 🟢 RTX

The recorded RTX result contains:

``` text
230 tests pass
+
compileall
```

## 🔵 M4 Pro

The Mac run reports:

``` text
227 tests passed
```

However, its raw `tests.txt` artifact also contains:

``` text
pytest: command not found
```

fileciteturn38file0

Therefore the Mac validation result must be treated carefully.

### Correct interpretation

Do **not** summarize this as:

> "RTX passed while Mac failed."

The available evidence instead indicates:

``` text
RTX
 └── 230 tests + compileall recorded

Mac
 ├── 227 tests reported in session evidence
 └── final automated test-collection artifact has pytest missing
```

The validation environment should be normalized before claiming a clean
apples-to-apples pass/fail comparison.

------------------------------------------------------------------------

# 🔬 8. What the Experiment Actually Shows

The strongest defensible statement is:

> **On this specific MotionForge Task 01 workload, the recorded RTX 5060
> Ti + llama.cpp + Qwen3.6-27B + Pi run completed substantially faster
> than the recorded M4 Pro + oMLX + Qwen3.6-27B + Pi run.**

Measured difference:

``` text
RTX: 31m 01s
M4:  118m 51s

Difference: 87m 50s
Ratio:      3.83×
```

The M4 Pro run also exhibited:

``` text
+43% messages
+51% tool calls
+94% input tokens
+92% total tokens
+8% output tokens
```

This makes the result interesting beyond a simple hardware-speed
comparison.

------------------------------------------------------------------------

# 🧩 9. Research Hypothesis

The initial results suggest a useful question:

> **Is end-to-end coding-agent performance dominated by raw generation
> speed, or by the interaction between inference latency, context
> processing and agent trajectory?**

``` text
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

The current dataset is too small to establish causality. That makes this
an important direction for the next benchmark series.

------------------------------------------------------------------------

# ⚠️ 10. Experimental Caveats

### Single workload

This is currently **one real software-repair task**. It should be
described as an initial benchmark, not a general performance
characterization.

### Different runtimes

``` text
RTX → llama.cpp
M4  → oMLX / MLX
```

This is a complete-stack comparison, not a pure hardware comparison.

### Different model representations

``` text
RTX:
Qwen3.6-27B-MTP-4.5bpw-pure.gguf

M4:
Qwen3.6-27B-oQ4-MTP
```

Therefore the observed difference cannot be attributed entirely to
hardware.

### Validation asymmetry

The Mac raw test artifact contains `pytest: command not found`, despite
227 tests being reported in the agent/session evidence.
fileciteturn38file0

### Timing evidence

Elapsed time should be derived from preserved start/end timestamps
rather than trusting malformed derived fields. Raw timing evidence
should remain immutable.

------------------------------------------------------------------------

# 🧭 11. Primary Conclusion

``` text
┌─────────────────────────────────────────────┐
│          Task 01 — 55K Context              │
├─────────────────────────────────────────────┤
│ RTX + llama.cpp      31m 01s                │
│ M4 + oMLX            118m 51s               │
├─────────────────────────────────────────────┤
│ RTX was ~3.83× faster in wall-clock time    │
└─────────────────────────────────────────────┘
```

The RTX configuration also used substantially fewer messages, tool
calls, input tokens and total tokens while generating a similar amount
of output.

### What we can say

> On this workload, the tested RTX 5060 Ti + llama.cpp configuration was
> substantially faster end-to-end than the tested M4 Pro + oMLX
> configuration.

### What we cannot say yet

``` text
RTX 5060 Ti > M4 Pro
```

in general.

Nor:

``` text
llama.cpp > oMLX
```

in general.

The experiment measures two complete configurations on one real repair
workload.

------------------------------------------------------------------------

# 🔬 12. Why This Benchmark Is Interesting

Synthetic benchmarks often ask:

``` text
“How many tokens/sec?”
```

LCAB asks:

``` text
“How long did the coding agent
take to actually repair the software?”
```

A system can have:

``` text
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

``` text
Lower tokens/sec
       +
Efficient agent trajectory
       +
Fewer interactions
       ↓
Competitive repair time
```

The Task 01 result demonstrates why **real software-repair workloads
complement synthetic inference benchmarks**.

------------------------------------------------------------------------

# 📈 13. Recommended Next Experiments

  -----------------------------------------------------------------------
  Experiment                          Question
  ----------------------------------- -----------------------------------
  📐 Context scaling                  16K vs 32K vs 55K: how does repair
                                      time change?

  🔢 Output limit                     Does max-output configuration
                                      materially affect trajectory?

  ⚡ Runtime tuning                   How much can llama.cpp / oMLX
                                      tuning reduce end-to-end time?

  🧠 Quantization                     Does equivalent model
                                      representation change the result?

  🤖 Repeated runs                    Is the observed trajectory stable?

  🔧 More tasks                       Does the RTX advantage persist
                                      across different repairs?

  🧪 Validation normalization         Can both systems use exactly the
                                      same test environment?

  🔄 OpenHands                        Does the hardware ranking change
                                      with another agent architecture?
  -----------------------------------------------------------------------

The most valuable immediate follow-up is **multiple real repair tasks
with identical agent/runtime settings**, followed by repeated runs.

------------------------------------------------------------------------

# 📚 14. Evidence

Raw evidence is preserved under:

``` text
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

The two runs share the same starting commit, independently recorded in
their `git-before.txt` artifacts. fileciteturn39file0
fileciteturn42file0

------------------------------------------------------------------------

# 🏷️ 15. Publication-Friendly Result

> ### 🏆 Task 01 --- 55K Context
>
> On a real MotionForge software-repair task, **Pi + Qwen3.6-27B**
> completed the recorded workload in **31m 01s on an RTX 5060 Ti +
> llama.cpp**, compared with **118m 51s on an M4 Pro + oMLX**.
>
> The RTX run used **80 tool calls and 2.16M total tokens**, while the
> M4 Pro run used **121 tool calls and 4.15M total tokens**.
>
> That's a **3.83× wall-clock difference** on this workload.
>
> ⚠️ This is an initial real-workload result, not a universal hardware
> ranking. The systems use different inference runtimes and model
> representations, and the Mac validation environment has a documented
> `pytest` collection issue.

------------------------------------------------------------------------

# 🎯 Bottom Line

``` text
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

The important research question is now not simply **"which machine is
faster?"**

It is:

> **Why did the two local coding-agent stacks take such different paths
> to solve the same real software problem?**

That is the question the next rounds of LCAB can answer.
