# Hacker News Submission — LCAB Task 01

> **Publication target:** Hacker News
>
> **Recommended submission type:** regular link submission to the long-form benchmark article, not Show HN.
>
> **Important:** Hacker News currently emphasizes curiosity, substantive technical content, factual/direct writing, and avoiding promotional framing. Its guidance also says not to use HN primarily for promotion. For this reason, this document is intentionally much shorter and more factual than the Reddit and Hugging Face versions. citeturn0search0turn0search2
>
> **Important author note:** HN's current guidance explicitly asks users not to use LLMs to generate or edit text posted to HN. Treat this file as a **research/structure draft** and rewrite it in your own voice before submitting. citeturn0search4

---

# 1. Recommended submission

## Title

**Benchmarking local coding agents on a real software repair: RTX 5060 Ti vs M4 Pro**

### Alternative titles

**31 minutes vs 119 minutes for a real local coding-agent repair**

**A real coding-agent benchmark: RTX 5060 Ti + llama.cpp vs M4 Pro + oMLX**

**What happens when you benchmark a local coding agent instead of tok/s?**

### Recommended URL

Use the published **Hugging Face long-form article** as the submission URL once it is live.

If the article is not live yet, submit the GitHub repository only if the repository itself provides enough context for the reader to understand the experiment.

The preferred path is:

```text
Hacker News
    │
    ▼
Hugging Face technical article
    │
    ├── methodology
    ├── benchmark results
    ├── trajectory analysis
    └── raw evidence
              │
              ▼
      GitHub benchmark repository
```

This gives HN readers a readable technical narrative while preserving the repository as the reproducibility source.

---

# 2. Submission blurb / opening

Use a short factual summary if you need to explain the submission in a comment:

> I benchmarked Pi + Qwen3.6-27B on a real MotionForge software-repair task at a 55K context target, comparing Windows + RTX 5060 Ti + llama.cpp with macOS + M4 Pro + oMLX. The RTX run took 31m 01s vs 118m 51s on the M4. More interestingly, the M4 trajectory used 121 tool calls and 4.15M total tokens vs 80 tool calls and 2.16M tokens on RTX, while both agents converged on essentially the same repair.

Keep the submission itself focused on the technical result. Do not turn the submission text into a marketing pitch.

---

# 3. The core technical finding

The benchmark compares two complete local coding-agent stacks:

```text
🟢 Windows
RTX 5060 Ti 16GB
llama.cpp
Qwen3.6-27B
Pi 0.84.1
55K context

              VS

🔵 macOS
M4 Pro 64GB
oMLX / MLX
Qwen3.6-27B
Pi 0.84.1
55K context
```

Recorded result:

| Metric | RTX 5060 Ti | M4 Pro |
|---|---:|---:|
| Wall time | **31m 01s** | **118m 51s** |
| Messages | 166 | 237 |
| Tool calls | 80 | 121 |
| Input tokens | 2.12M | 4.11M |
| Output tokens | 36.3K | 39.0K |
| Total tokens | 2.16M | 4.15M |

Observed wall-time ratio:

```text
118m 51s / 31m 01s ≈ 3.83×
```

The RTX configuration completed the recorded workload in approximately 26% of the M4 wall-clock time.

---

# 4. Why the result is more interesting than a hardware comparison

The agents did not produce radically different solutions.

The repair involved propagating a `steps` parameter through MotionForge:

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

The two implementations converged on essentially the same production architecture and added regression coverage.

The trajectories, however, differed substantially:

```text
                     RTX             M4

Tool calls            80             121
Total tokens        2.16M           4.15M
Wall time          31m 01s        118m 51s

                         │
                         ▼

                 Similar repair
```

The M4 run therefore had approximately:

```text
+43% messages
+51% tool calls
+94% input tokens
+92% total tokens
```

while output tokens differed by only about 8%.

That suggests that **agent trajectory and context amplification may be important dimensions of local coding-agent performance**.

---

# 5. What the experiment does not prove

This is a comparison of complete configurations, not a hardware-only controlled experiment.

The systems differ in:

```text
hardware
operating system
inference runtime
model representation / quantization
memory architecture
```

Therefore I would not claim:

```text
RTX 5060 Ti is universally 3.83× faster than M4 Pro.
```

The defensible claim is:

> On this particular real software-repair workload, the tested RTX 5060 Ti + llama.cpp configuration completed the recorded 55K-context Pi run substantially faster than the tested M4 Pro + oMLX configuration.

The benchmark also does not isolate how much of the wall-time difference came from:

- inference;
- context processing;
- tool execution;
- repository exploration;
- testing;
- agent trajectory;
- runtime overhead.

That is the next experiment.

---

# 6. Validation caveat

The recorded RTX run contains:

```text
230 tests + compileall
```

The Mac session reports:

```text
227 tests passed
```

but its raw test artifact also contains:

```text
pytest: command not found
```

Therefore I am treating the Mac validation environment as an experimental caveat rather than claiming a clean correctness win.

This is also why the raw benchmark artifacts are preserved.

---

# 7. The research question

The experiment started with:

> **Which local machine is faster for a coding agent?**

The more useful question now appears to be:

> **How efficiently does a local coding-agent stack transform model inference, context, tool interactions, and repository exploration into a correct software repair?**

Conceptually:

```text
Hardware
   ↓
Inference
   ↓
Context
   ↓
Agent trajectory
   ↓
Tool execution
   ↓
Testing
   ↓
Software repair
   ↓
Wall-clock time
```

This is the measurement model I want to explore with additional real repair tasks.

---

# 8. What I would test next

### Repeatability

```text
RTX × 3
M4 × 3
```

### Context scaling

```text
16K
32K
55K
```

### More repair tasks

A single task is not sufficient for a broad hardware/runtime conclusion.

### Per-turn measurements

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

The goal is to determine where the additional ~87m 50s in the M4 run actually accumulates.

---

# 9. Repository

The benchmark repository contains the methodology, task definition, hardware descriptions, processed results, code analysis, agent/tool trajectory analysis, and raw run evidence.

**https://github.com/amitmaity0/local-coding-agent-benchmark**

---

# 10. Suggested first author comment

Do not put all of the following into the submission title or opening. If the thread receives technical questions, use a comment like this:

> A few methodological details:
>
> - Both runs used Pi 0.84.1 + Qwen3.6-27B and a 55K context target.
> - The starting repository revision was the same.
> - The RTX model was a 4.5 bpw pure GGUF; the M4 used the recorded oQ4-MTP representation, so this is not a quantization-controlled comparison.
> - Both runs had approximately 90.5% cached-input share.
> - The Mac validation artifact has a `pytest: command not found` issue, so I am not treating the test counts as perfectly normalized.
> - The raw Pi session artifacts and repository patches are preserved in the benchmark repo.
>
> The next version will add repeated runs, context scaling, and per-turn timing.

---

# 11. Likely HN questions and concise answers

## “Why not compare tok/s?”

Because the purpose of this benchmark is to measure the **complete coding-agent loop**.

Tok/s is still useful and should be collected, but it does not capture:

```text
tool calls
context growth
repository exploration
testing
retries
agent trajectory
```

The current result is specifically interesting because total token volume and interaction count differed substantially.

---

## “Why are the quantizations different?”

They are the model/runtime configurations used for the current practical comparison.

That is also a limitation.

A future controlled experiment should compare more closely matched model representations where technically possible.

---

## “Isn't this just an RTX vs Apple Silicon benchmark?”

Not exactly.

It is an **end-to-end stack comparison**:

```text
hardware
+
OS
+
runtime
+
model representation
+
agent
+
workload
```

The benchmark deliberately does not attribute the entire 3.83× difference to the GPU.

---

## “Why only one task?”

Because this is the first real-workload experiment.

One task is enough to demonstrate the measurement methodology, but not enough to establish a general ranking.

The next stage is multiple repair tasks and repeated runs.

---

## “Could the M4 agent simply have taken a worse path?”

Possibly.

The aggregate data shows a longer trajectory:

```text
121 vs 80 tool calls
4.15M vs 2.16M total tokens
```

But it does not tell us whether those additional interactions were unnecessary.

That is why per-turn trajectory analysis is the next measurement.

---

## “What model are you actually using?”

Qwen3.6-27B.

The current configurations use:

```text
RTX → Qwen3.6-27B 4.5 bpw pure GGUF
M4  → Qwen3.6-27B oQ4-MTP
```

The benchmark records the model representation as part of the configuration rather than hiding it behind a generic model name.

---

## “Can you publish the raw logs?”

Yes.

The benchmark repository preserves the raw run artifacts, including Pi session data and repository evidence.

---

# 12. HN tone checklist

Before posting, edit the final text so that it sounds like **you**, not like a generated article.

Prefer:

```text
I measured...
I found...
The data shows...
I don't know yet...
This may indicate...
I'd like to test...
```

Avoid:

```text
revolutionary
groundbreaking
game-changing
blazing-fast
destroys
best
ultimate
industry-leading
```

Avoid unnecessary emojis in the actual HN submission.

Avoid a long project introduction.

Avoid asking readers to “support,” “star,” or “share” the repository.

Avoid claims broader than the experiment.

The technical result should be the reason to read the article.

---

# 13. Recommended submission format

For this project I recommend:

```text
HN link
  ↓
Hugging Face technical article
  ↓
GitHub repository
  ↓
Raw benchmark evidence
```

rather than:

```text
Show HN: My Benchmark Project
```

The benchmark is currently primarily a **research/publication artifact**, not a hosted interactive product that HN readers can immediately try.

Hacker News describes Show HN as being for something you have made that people can actually try; for this benchmark publication, a normal article submission is therefore the cleaner fit. citeturn0search4

---

# 14. Why this framing should work better on HN

The strongest HN angle is not:

> “I built a benchmark.”

It is:

> **“I measured a real coding agent and found that the end-to-end difference was much larger than a simple token-count comparison suggests.”**

That creates several technically interesting questions:

```text
Why did the trajectories diverge?

How much did context processing contribute?

How much was inference runtime?

How much was agent behavior?

Does the gap persist at 16K / 32K / 55K?

Does it persist across other repair tasks?
```

Those are questions that can generate technical discussion rather than a product-promotion thread.

HN's guidelines emphasize material that is interesting to technically minded readers and specifically caution against using HN primarily for promotion. citeturn0search0turn0search2

---

# 15. Final recommended title + link

### Title

**Benchmarking local coding agents on a real software repair: RTX 5060 Ti vs M4 Pro**

### Link

**The published Hugging Face article**

### First comment

Use the short methodology/evidence comment above only if useful.

---

# Evidence boundary

The benchmark directly measures:

```text
wall time
messages
tool calls
input tokens
cached input
output tokens
total tokens
```

The code comparison provides evidence of convergent engineering solutions.

The benchmark does **not** currently provide a causal decomposition of the wall-time difference.

The strongest current claim is therefore:

> **For this particular 55K-context MotionForge repair, the tested RTX 5060 Ti + llama.cpp configuration completed the recorded Pi workload substantially faster than the tested M4 Pro + oMLX configuration, while following a substantially smaller recorded agent trajectory.**

That is the claim the HN article should invite readers to examine and challenge.

---

**Model credit:** The RTX benchmark used the 4.5bpw-pure GGUF release of Qwen3.6-27B published by huytd189:

https://huggingface.co/huytd189/Qwen3.6-27B-pure-GGUF

The model was used as published without modifying the weights.