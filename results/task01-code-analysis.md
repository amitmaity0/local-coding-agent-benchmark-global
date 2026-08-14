# 🔧 Task 01 — Code Repair Analysis

> **How the two local coding-agent runs repaired the same MotionForge defect**
>
> This document analyzes the actual patches produced by the **RTX 5060 Ti + llama.cpp** and **M4 Pro + oMLX** benchmark runs, focusing on engineering behavior, patch convergence, test strategy, and differences between the two agent trajectories.

## 🎯 1. Why Analyze the Patch?

A coding-agent benchmark should not stop at:

```text
⏱️ RTX = 31m 01s
⏱️ M4  = 118m 51s
```

The more interesting question is:

> **Did both systems independently discover and implement the same engineering solution?**

For Task 01, the answer is broadly **yes**.

Both runs converged on the same central repair:

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
LTXVScheduler node 206
      │
      ▼
workflow["206"]["inputs"]["steps"]
```

This convergence matters because the large runtime difference was not simply caused by one system finding a completely different solution.

---

## 🧩 2. The Defect Being Repaired

The core defect involved the `steps` parameter in the autonomous optimization workflow.

Before the repair, `Engine.generate()` applied several experiment parameters:

```text
prompt
seed
cfg
noise
```

but did not propagate:

```text
steps
```

into the workflow.

At the same time, `WorkflowLoader.set_steps()` was designed around a generic `KSampler` assumption.

That is insufficient for the LTX workflow because the relevant node is:

```text
Node: 206
Class: LTXVScheduler
Input: steps
```

The repair therefore needed two related changes:

1. **Propagate `Experiment.steps` through `Engine.generate()`.**
2. **Make `WorkflowLoader.set_steps()` understand workflow sidecar mappings.**

---

## 🏗️ 3. Before the Repair

Conceptually:

```text
Experiment
   │
   ├── prompt ────────────────┐
   ├── seed ──────────────────┤
   ├── cfg ───────────────────┤
   ├── noise ─────────────────┤
   │                           ▼
   │                    WorkflowLoader
   │                           │
   │                           ▼
   │                       Workflow
   │
   └── steps ──X──> workflow
```

The missing `steps` propagation meant that changing the experiment's optimization state did not necessarily change the actual LTX workflow.

---

## 🛠️ 4. Shared Core Repair

Both agents independently added the equivalent of:

```python
workflow = loader.set_steps(
    workflow,
    getattr(exp, "steps", 30) or 30,
    sidecar=sidecar,
)
```

### 🟢 RTX patch

```python
cur_steps = getattr(exp, "steps", 30) or 30
workflow = loader.set_steps(workflow, cur_steps, sidecar=sidecar)
```

### 🔵 M4 patch

```python
workflow = loader.set_steps(
    workflow, getattr(exp, "steps", 30) or 30, sidecar=sidecar
)
```

Both solutions correctly:

- read the experiment-level `steps`;
- preserve a default of `30`;
- pass the sidecar;
- apply the parameter during workflow generation.

This is strong patch convergence.

---

## 🔗 5. Sidecar-Aware Workflow Mapping

Both agents changed `set_steps()` from a generic KSampler-only implementation to a sidecar-aware implementation.

### Before

```text
steps
  │
  ▼
find KSampler
  │
  ▼
set "steps"
```

### After

```text
set_steps()
     │
     ▼
Does sidecar define "steps"?
     │
   ┌─┴─────────────┐
   │               │
  yes              no
   │               │
   ▼               ▼
Use mapped       Generic
target(s)        KSampler
   │
   ▼
Set node/input
```

This is a better abstraction because workflow-specific mapping belongs in the sidecar rather than being hard-coded into the generic workflow loader.

---

## 🧭 6. LTX Sidecar Change

Both agents added the essential mapping to:

```text
workflows/LTX2.3-Basic-API.yaml
```

```yaml
steps:
  ...
  node_id: "206"
  input: "steps"
```

Therefore:

```text
Experiment.steps = 45
        │
        ▼
WorkflowLoader.set_steps(..., 45, sidecar)
        │
        ▼
Sidecar:
  node_id = 206
  input   = steps
        │
        ▼
workflow["206"]["inputs"]["steps"] = 45
```

This is the critical integration point.

---

## 🔬 7. Engineering Convergence

| Repair area | RTX | M4 Pro |
|---|---|---|
| `Engine.generate()` calls `set_steps()` | ✅ | ✅ |
| Uses experiment `steps` | ✅ | ✅ |
| Default `steps=30` | ✅ | ✅ |
| Passes sidecar | ✅ | ✅ |
| `set_steps()` understands sidecar mappings | ✅ | ✅ |
| LTX sidecar maps `steps` → node 206 | ✅ | ✅ |
| Generic KSampler fallback retained | ✅ | ✅ |
| Unsupported sidecar handling | ✅ | ✅ |
| Regression tests added | ✅ | ✅ |

The two agents therefore arrived at essentially the same architectural repair.

---

## 🧪 8. Test Strategy — RTX

The RTX patch added broad coverage in:

```text
tests/test_autonomous_loop.py
```

It covers:

### 🔗 Full parameter propagation

```text
prompt
seed
cfg
steps
```

### 🔢 Steps propagation

```text
Experiment.steps = 45
        ↓
WorkflowLoader.set_steps()
        ↓
LTX node 206 = 45
```

### 🔄 Optimization propagation

```text
Iteration 1
steps = 30
    ↓
optimizer
new_steps = 45
    ↓
Experiment.steps = 45
    ↓
Iteration 2
steps = 45
```

### 🧮 Candidate semantics

Checks that:

```text
candidates_per_iteration = 3
```

does not accidentally become three autonomous loop iterations.

### 🧊 Iteration immutability

Checks that:

```text
Iteration 1:
steps_used = 30
```

remains 30 after optimization changes the experiment to:

```text
steps = 50
```

### 🧵 Background execution

Checks that the loop-start endpoint dispatches execution to a background thread.

### 🎯 Target-score semantics

Adds explicit coverage for:

```text
score == target
```

and:

```text
score < target
```

---

## 🧪 9. Test Strategy — M4 Pro

The M4 patch also added substantial coverage, but with a different emphasis.

It explicitly imports:

```python
ExperimentORM
```

and uses database-backed experiment state.

One notable test captures the actual workflow passed to:

```text
ComfyUIService.generate()
```

and verifies:

```text
captured_workflow["206"]["inputs"]["steps"] == 42
```

This is a strong integration-style check.

---

## 🔍 10. M4's Strong Integration Test

The Mac patch constructs this chain:

```text
ExperimentORM.steps = 42
          │
          ▼
Engine.run_loop()
          │
          ▼
Engine.generate()
          │
          ▼
WorkflowLoader.set_steps()
          │
          ▼
ComfyUIService.generate()
          │
          ▼
captured workflow
          │
          ▼
node 206 / steps = 42
```

That verifies that the value reaches the service boundary, rather than only verifying the helper method.

---

## ⚖️ 11. Test-Suite Differences

### 🟢 RTX emphasis

```text
Broad behavioral coverage
        +
Autonomous-loop semantics
        +
Parameter persistence
        +
Iteration invariants
        +
Termination behavior
```

### 🔵 M4 emphasis

```text
End-to-end propagation
        +
Database-backed experiment state
        +
Workflow capture
        +
Parameter mapping
        +
Iteration snapshots
```

Both approaches are useful.

The RTX patch is particularly broad, while the M4 patch includes a particularly useful service-boundary integration test.

---

## 🧠 12. Significant Difference in the Patches

The RTX patch makes the sidecar `steps` mapping:

```yaml
required: false
```

The M4 patch makes it:

```yaml
required: true
```

This is a real semantic difference.

### RTX interpretation

```text
steps mapping exists but is optional
```

### M4 interpretation

```text
steps mapping is required for this workflow
```

For the LTX workflow, both patches still map:

```text
206.steps
```

correctly.

However, this difference should be resolved deliberately before selecting a canonical patch.

---

## ⚠️ 13. Unsupported `steps` Handling

Both implementations account for a sidecar explicitly marking `steps` unsupported:

```text
sidecar has steps?
       │
      yes
       │
       ▼
unsupported?
   ┌───┴───┐
  yes      no
   │        │
   ▼        ▼
preserve   apply
workflow   mapping
```

The behavior is equivalent for the workflow.

The RTX implementation additionally logs the attempted value; the M4 implementation logs that the parameter is unsupported.

---

## 🧱 14. Generic Fallback

Both patches preserve:

```python
self._replace_by_class(
    workflow,
    "KSampler",
    {"steps": steps},
)
```

The architecture becomes:

```text
                    set_steps()
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       Sidecar mapping          No sidecar mapping
             │                       │
             ▼                       ▼
      Workflow-specific          KSampler fallback
          target(s)
```

This preserves backward compatibility for existing workflows.

---

## 🔄 15. Patch Scope

Both agents modified essentially the same functional areas:

```text
orchestrator/engine.py
services/workflow.py
tests/test_autonomous_loop.py
tests/test_sidecar.py
tests/test_workflow.py
workflows/LTX2.3-Basic-API.yaml
```

That is a strong sign that both agents understood the repository architecture rather than applying unrelated local workarounds.

---

## 📐 16. Patch Size

| Patch | Recorded size |
|---|---:|
| 🟢 RTX | ~27.3 KB |
| 🔵 M4 | ~26.1 KB |

The difference is primarily due to test implementation and formatting rather than a fundamentally different production repair.

Most of the patch expansion is:

```text
🧪 regression tests
```

rather than:

```text
🏗️ production implementation
```

That is generally a positive characteristic for a bug-fix benchmark.

---

## 🧩 17. Production-Code Complexity

The production repair is relatively compact:

```text
Engine
  + one parameter propagation step

WorkflowLoader
  + sidecar-aware mapping
  + unsupported handling
  + existing fallback preserved

Workflow sidecar
  + one mapping
```

The task is therefore not primarily about writing a large amount of new code.

Its difficulty comes from understanding:

```text
Experiment
    ↓
Engine
    ↓
WorkflowLoader
    ↓
Sidecar
    ↓
LTX workflow node
```

That makes it a useful test of repository-level investigation and cross-layer reasoning.

---

## 🧭 18. What This Says About Agent Capability

The patch convergence suggests that both local configurations were capable of:

- navigating a multi-module repository;
- identifying the missing propagation point;
- understanding the sidecar abstraction;
- identifying the LTX-specific scheduler node;
- implementing the workflow mapping;
- adding regression coverage;
- preserving the generic fallback behavior.

That is stronger evidence of coding-agent capability than a synthetic single-file coding problem.

---

## ⏱️ 19. Connecting Code Quality to Runtime

The benchmark results were:

```text
RTX
31m 01s
80 tool calls
2.16M tokens
```

versus:

```text
M4
118m 51s
121 tool calls
4.15M tokens
```

Yet the production patches converge closely.

This suggests an important distinction:

```text
                 Same engineering destination
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
          RTX trajectory              M4 trajectory
          shorter                      longer
          fewer tools                  more tools
          less context                 more context
                │                           │
                └─────────────┬─────────────┘
                              ▼
                     Similar final repair
```

In other words:

> **The observed performance difference appears primarily in the path to the solution, not in the final engineering idea.**

This is an observation, not proof of causality.

---

## 🔬 20. Important Caveat

Patch similarity does **not** prove that the two agents reasoned identically.

They may have:

- explored different files;
- executed different commands;
- made different intermediate edits;
- discovered the architecture in different orders;
- tested different hypotheses;
- recovered from different failures.

The final patch is only the endpoint.

The preserved `pi-session.jsonl` and `pi-session.html` artifacts should therefore be used for trajectory-level analysis.

---

## 📊 21. Patch-Convergence Scorecard

| Dimension | Finding |
|---|---|
| Core production fix | 🟢 Strong convergence |
| `steps` propagation | 🟢 Same solution |
| Sidecar architecture | 🟢 Same solution |
| LTX node mapping | 🟢 Same target: node 206 |
| Generic fallback | 🟢 Preserved |
| Unsupported behavior | 🟢 Preserved |
| Regression testing | 🟢 Both extensive |
| Test philosophy | 🟡 Different emphasis |
| Sidecar `required` flag | 🟡 Difference |
| Final engineering direction | 🟢 Highly convergent |

---

## 🏆 22. Overall Engineering Assessment

### What both agents did well

Both agents:

1. identified the missing `steps` propagation;
2. avoided hard-coding the LTX node directly into `Engine`;
3. extended the existing sidecar abstraction;
4. retained generic KSampler behavior;
5. added regression tests;
6. tested the LTX mapping;
7. connected optimization state to subsequent workflow generation.

This is a structurally sound repair pattern.

---

## 🔎 23. The Most Interesting Benchmark Finding

The benchmark reveals:

```text
                 SAME MODEL FAMILY
                        │
                        ▼
                 SAME CODING AGENT
                        │
                        ▼
                 SAME REAL TASK
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
         RTX + llama.cpp      M4 + oMLX
              │                   │
              ▼                   ▼
       shorter trajectory    longer trajectory
              │                   │
              ▼                   ▼
        ~27 KB patch          ~26 KB patch
              │                   │
              └─────────┬─────────┘
                        ▼
                 Similar repair
```

This makes **agent trajectory efficiency** a particularly valuable metric for future LCAB experiments.

---

## 🧪 24. What Should Be Tested Next?

| Metric | Why it matters |
|---|---|
| 🔎 Time to first repository inspection | Detect startup/reasoning overhead |
| 📂 Files inspected | Measure exploration breadth |
| 🔧 Tool calls | Measure interaction overhead |
| 🧪 Test executions | Measure validation strategy |
| ❌ Failed commands | Measure recovery burden |
| 🔄 Repeated edits | Detect inefficient loops |
| 📚 Context growth | Measure long-context cost |
| 🧠 Compaction events | Measure context management |
| ⏱️ Time between tool calls | Approximate inference/processing latency |
| 🏁 Time to first correct patch | Separate discovery from validation |
| ✅ Final patch convergence | Measure solution quality |

This can turn LCAB from a simple timing benchmark into a **coding-agent trajectory benchmark**.

---

## 📌 25. Publication Takeaway

> **Both local coding-agent configurations independently converged on essentially the same multi-layer repair: propagate `Experiment.steps` through `Engine.generate()`, make `WorkflowLoader.set_steps()` sidecar-aware, and map the parameter to the LTX scheduler's node 206. The RTX run reached that solution in 31m 01s with 80 tool calls and 2.16M total tokens, while the M4 Pro run took 118m 51s with 121 tool calls and 4.15M total tokens. The striking difference was therefore not the final engineering approach, but the amount of interaction and context processing required to reach it.**

---

## 🎯 Bottom Line

Task 01 provides evidence of **strong solution convergence but very different execution efficiency**.

```text
                     TASK 01
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
       🟢 RTX 5060 Ti          🔵 M4 Pro
            │                       │
      80 tool calls            121 tool calls
      2.16M tokens             4.15M tokens
      31m 01s                  118m 51s
            │                       │
            ▼                       ▼
       ┌────────────────────────────────┐
       │      Similar engineering fix   │
       │                                │
       │ Experiment.steps → Engine      │
       │ → sidecar → node 206           │
       └────────────────────────────────┘
```

The important research question is now not simply **“which machine is faster?”**

It is:

> **Why did the two local coding-agent stacks take such different paths to solve the same real software problem?**

That is the question the next rounds of LCAB can answer.
