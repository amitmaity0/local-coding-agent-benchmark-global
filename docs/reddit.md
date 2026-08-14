# Reddit — r/LocalLLaMA Publication Draft

> **Purpose:** A high-signal Reddit post for `r/LocalLLaMA` based on LCAB Task 01.
>
> **Posting style:** conversational, transparent, evidence-first, technically specific, and open to criticism.
>
> **Important:** Check the current `r/LocalLLaMA` rules/flair requirements immediately before posting. Reddit communities can change their self-promotion and link-post policies. The draft intentionally leads with the experiment and findings rather than with a project advertisement.

---

## Recommended title

**I benchmarked Pi + Qwen3.6-27B on a real coding task: RTX 5060 Ti vs M4 Pro at 55K context**

### Alternative titles

**Real coding-agent benchmark: RTX 5060 Ti + llama.cpp vs M4 Pro + oMLX**

**A real software-repair benchmark gave me a surprising RTX 5060 Ti vs M4 Pro result**

**31 min vs 119 min: local Qwen3.6-27B coding agent on RTX 5060 Ti vs M4 Pro**

**I stopped benchmarking tok/s and tested a local coding agent on a real repo**

---

# Post body

I've been experimenting with local coding agents and wanted to measure something more useful than raw tok/s:

> **How long does a local coding agent actually take to repair real software?**

So I built a small benchmark around **Pi + Qwen3.6-27B** and ran the same real MotionForge software-repair workload on two machines:

```text
🟢 Windows
RTX 5060 Ti 16GB
llama.cpp
Qwen3.6-27B
Pi 0.84.1
55K context

vs.

🔵 macOS
M4 Pro 64GB
oMLX / MLX
Qwen3.6-27B
Pi 0.84.1
55K context
```

Both runs started from the same repository revision.

## The result

| | RTX 5060 Ti | M4 Pro |
|---|---:|---:|
| Runtime | llama.cpp | oMLX / MLX |
| Context | 55K | 55K |
| Wall time | **31m 01s** | **118m 51s** |
| Messages | 166 | 237 |
| Tool calls | 80 | 121 |
| Input tokens | 2.12M | 4.11M |
| Output tokens | 36.3K | 39.0K |
| Total tokens | 2.16M | 4.15M |

So the recorded wall-clock difference was:

**3.83×**

The RTX run took about **26% of the M4 run's elapsed time**.

But the wall time wasn't the most interesting part.

## The agent trajectories were very different

The M4 run used:

- **43% more messages**
- **51% more tool calls**
- **94% more input tokens**
- **92% more total tokens**

while output tokens were only about **8% higher**.

In other words:

```text
                  RTX          M4

Messages          166          237
Tool calls         80          121
Input tokens     2.12M        4.11M
Output tokens   36.3K         39.0K
Total tokens     2.16M        4.15M
Wall time       31m 01s      118m 51s
```

Both runs had roughly the same cached-input share (~90.5%), so this doesn't look like a simple "one system had caching and the other didn't" situation.

## And both agents basically found the same repair

This is the part I found most interesting.

The task involved propagating a `steps` parameter through MotionForge's workflow:

```text
Experiment.steps
      ↓
Engine.generate()
      ↓
WorkflowLoader.set_steps()
      ↓
sidecar-aware mapping
      ↓
LTX scheduler node 206
```

The two agents independently converged on essentially the same production implementation and added regression coverage.

So I ended up with something like:

```text
             SAME REAL REPAIR
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
      RTX                      M4
        │                       │
   80 tools                 121 tools
   2.16M tokens             4.15M tokens
   31 minutes               119 minutes
        │                       │
        └───────────┬───────────┘
                    ▼
             similar repair
```

That makes me think **trajectory efficiency** deserves to be treated as a first-class metric for local coding-agent benchmarks.

---

## Why I don't think this proves "RTX is 3.83× faster than M4"

I want to be careful about this.

This is a comparison of **two complete stacks**, not a controlled hardware-only experiment.

The configurations differ in:

- hardware architecture;
- OS;
- inference runtime;
- model representation / quantization;
- memory architecture.

So I think the defensible claim is:

> On this particular real software-repair workload, the tested RTX 5060 Ti + llama.cpp configuration completed the recorded 55K-context Pi run substantially faster than the tested M4 Pro + oMLX configuration.

I would **not** claim:

> RTX 5060 Ti is universally 3.83× faster than M4 Pro for coding.

That's a much stronger claim than this experiment supports.

---

## There is also a validation caveat

The RTX run has recorded:

```text
230 tests + compileall
```

The Mac session reports:

```text
227 tests passed
```

but the raw Mac test artifact also contains:

```text
pytest: command not found
```

So I don't want to pretend the validation environments were perfectly symmetrical yet.

I'm treating this as an experimental-data caveat and plan to normalize the validation environment in the next round.

---

## Why I'm publishing this

I'm interested in whether local coding-agent benchmarking should move beyond:

```text
tok/s
VRAM
context length
```

and measure the complete loop:

```text
hardware
   ↓
inference
   ↓
agent trajectory
   ↓
tool calls
   ↓
context growth
   ↓
testing
   ↓
successful repair
   ↓
wall time
```

The first result makes me think that could be useful.

A model can generate tokens quickly, but if the agent needs many more interactions and processes much more accumulated context, the developer's actual experience can be very different.

---

## What I want to test next

The obvious next experiments are:

### 1. Repeatability

```text
RTX × 3
M4 × 3
```

to see how much run-to-run variance there is.

### 2. Context scaling

```text
16K
32K
55K
```

on both systems.

### 3. More real repair tasks

One task is interesting, but obviously isn't enough to make a broad hardware/runtime claim.

### 4. Per-turn timing

I want to break the Pi session down into:

```text
model generation
context processing
tool execution
tests
waiting / runtime overhead
```

That should tell me where the extra ~88 minutes actually went.

### 5. More agents

The current focus is Pi. I'd eventually like to run the same methodology with OpenHands and other local coding-agent stacks.

---

## Benchmark repository

I've published the benchmark repository here:

**https://github.com/amitmaity0/local-coding-agent-benchmark**

It contains the methodology, task definition, hardware information, processed results, and raw benchmark evidence.

The raw run artifacts are intentionally preserved rather than replacing them with only summarized numbers.

---

## I'd especially like feedback on the methodology

A few things I'm unsure about and would appreciate criticism on:

1. **Is comparing complete stacks more useful than trying to isolate hardware?**
2. **Should agent trajectory metrics become standard alongside tok/s?**
3. **What would you consider the minimum number of real repair tasks before making hardware/runtime conclusions?**
4. **What per-turn metrics would you want to see?**
5. **Would you normalize the model quantization more aggressively, even if that makes the practical hardware comparison less representative?**

I'm particularly interested in feedback from people running **Qwen + Pi/OpenCode/OpenHands/other coding agents locally**.

If you see a methodological flaw, please point it out. I'd rather fix the benchmark than defend a bad result.

---

## Compact result

```text
Task:        real MotionForge software repair
Agent:       Pi 0.84.1
Model:       Qwen3.6-27B
Context:     55K

RTX 5060 Ti + llama.cpp
31m 01s
80 tool calls
2.16M total tokens

M4 Pro + oMLX
118m 51s
121 tool calls
4.15M total tokens

Observed wall-time ratio: 3.83×
```

**The interesting question isn't just which machine won. It's why two local agents reached a similar repair through such different trajectories.**

---

# Optional first comment

If the post gets technical discussion, I would add this as the first author comment rather than making the main post even longer:

> **Raw evidence / methodology**
>
> The benchmark intentionally preserves the original Pi session artifacts and repository state. The current run has two known caveats: the timing files contain malformed elapsed-duration fields (start/end timestamps are preserved), and the Mac test artifact has a `pytest: command not found` environment issue. I'm treating those as data-quality items rather than silently correcting them.
>
> The next revision will automate extraction of per-turn timing, context growth, tool duration and validation events.
>
> Repo: https://github.com/amitmaity0/local-coding-agent-benchmark

---

# Posting notes

## Recommended flair

Use the closest currently available flair to:

```text
Benchmark
Research
Discussion
Showcase / Project
```

Do **not** invent a flair if the subreddit has a controlled flair list.

## Link strategy

For `r/LocalLLaMA`, I recommend making the **post itself self-contained** and putting the GitHub repository near the end.

Don't make the post read like:

> "I built a project, please click my GitHub."

Instead, make the benchmark result the useful content and the repository the evidence.

This matters because Reddit communities generally respond better to substantive technical posts than obvious self-promotion, and recent `r/LocalLLaMA` benchmark posts that perform well tend to provide concrete methodology, results, limitations, and a repository rather than only announcing a project. citeturn0reddit25turn0reddit27turn0reddit31

Reddit itself also recommends following each community's rules and prioritizing useful, authentic discussion over promotional content. citeturn0search0turn0search2

## What not to put in the title

Avoid:

```text
🔥 AMAZING RTX vs M4 RESULTS!!!
🚀 My new benchmark DESTROYS Apple
BEST LOCAL CODING MACHINE!!!
```

The data is interesting enough without hype.

## What I would do after posting

Stay available for methodology questions.

The likely high-value discussions are:

```text
"Why didn't you use the same quant?"
"Why only one task?"
"How does this compare with OpenCode?"
"What's the actual tok/s?"
"Can you publish the raw Pi session?"
"Can you test 32K?"
"How much RAM/VRAM was used?"
```

Those questions are useful because they naturally turn the Reddit thread into peer review of the benchmark.

---

# Evidence boundary

This post intentionally distinguishes:

- **measured results** — wall time, messages, tools, tokens;
- **code observations** — convergence of the two repairs;
- **interpretation** — trajectory/context differences;
- **future hypotheses** — why the time difference occurred.

The experiment does not establish a universal RTX-vs-M4 ranking, a universal llama.cpp-vs-oMLX ranking, or a causal decomposition of the 87m 50s wall-time difference.

---

**Model credit:** The RTX run used the 4.5bpw-pure GGUF release of Qwen3.6-27B published by **huytd189** on Hugging Face.

https://huggingface.co/huytd189/Qwen3.6-27B-pure-GGUF

Thanks to the author for making the GGUF available for local inference. The benchmark used the published model without modifying its weights.