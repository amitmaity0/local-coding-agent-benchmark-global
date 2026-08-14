# 🍎 Mac + M4 Pro

> **Apple Silicon benchmark system for the Local Coding Agent Benchmark**

This machine represents the **Apple Silicon side of the LCAB hardware/runtime comparison**.

```text
🍎 Mac
   │
   ▼
🧠 Apple M4 Pro
   │
   ▼
⚡ oMLX / MLX
   │
   ▼
🧠 Qwen3.6-27B
   │
   ▼
🤖 Pi
   │
   ▼
🔧 Real Software Repair
```

The benchmark evaluates this as a **complete local coding-agent stack**, not as an isolated hardware benchmark.

---

# 🧾 System Summary

| Component | Specification |
|---|---|
| 💻 System | Mac |
| 🧠 SoC | Apple M4 Pro |
| 🎮 GPU | Integrated Apple GPU |
| 💾 Unified Memory | 64 GB |
| 💿 Storage | 100 GB free |
| 🍎 Operating System | macOS |
| ⚡ Inference Runtime | oMLX / MLX |
| 🤖 Coding Agent | Pi |
| 🖥️ Pi Environment | Separate Ubuntu VM |
| 🧠 Model | Qwen3.6-27B |
| 📦 Model configuration | Qwen3.6-27B-oQ4e-mtp |

The current hardware profile identifies the model as `Qwen3.6-27B-oQ4e-mtp`.

---

# 🏗️ Benchmark Stack

```text
┌──────────────────────────────────────────────┐
│              🔧 Software Repair              │
│             Real benchmark workload          │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│                  🤖 Pi Agent                  │
│             Ubuntu VM environment             │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│                🧠 Qwen3.6-27B                │
│              oQ4e MTP configuration           │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│                  ⚡ oMLX / MLX                │
│             Local inference runtime           │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│                 🍎 Apple M4 Pro               │
│              Integrated Apple GPU             │
│               64 GB unified memory            │
└──────────────────────────────────────────────┘
```

> ℹ️ **Important:** Pi is documented as running in a separate Ubuntu VM. Preserve the VM/network/runtime arrangement as part of the benchmark configuration.

---

# 🧠 Apple Silicon Memory Model

The system uses **64 GB of unified memory**.

Conceptually:

```text
                 🍎 M4 Pro SoC
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
      CPU cores                Apple GPU
          │                         │
          └────────────┬────────────┘
                       │
                       ▼
                💾 Unified Memory
                    64 GB
```

For LCAB, this matters because model inference, operating-system activity, the VM, the coding agent, and other processes can participate in the same memory pool.

Therefore, memory measurements should be described as **unified-memory usage**, not as equivalent to dedicated GPU VRAM.

---

# ⚡ Inference Runtime

The Apple Silicon benchmark uses:

> **oMLX / MLX**

The runtime is part of the experimental configuration.

```text
M4 Pro
   +
oMLX / MLX
   +
Qwen3.6-27B
   +
Pi
   +
Task
```

For reproducibility, record:

| Runtime field | Value |
|---|---|
| Runtime | oMLX / MLX |
| Runtime version | Record at run time |
| Runtime commit | Record when applicable |
| Model | Exact identifier |
| Quantization | Exact format |
| Context | Exact window |
| MTP | Enabled / disabled |
| Sampling | Exact parameters |
| Other acceleration options | Record when relevant |

> ⚠️ A result represents the tested runtime configuration, not every possible Apple Silicon inference runtime.

---

# 🧠 Model

Current model:

```text
Qwen3.6-27B
```

Current benchmark configuration:

```text
Qwen3.6-27B-oQ4e-mtp
```

Record the exact model identifier, revision, quantization and MTP configuration for every run.

```text
Model
 │
 ├── Family: Qwen3.6
 ├── Size: 27B
 ├── Quantization: oQ4e
 └── MTP: enabled
```

> ⚠️ Do not generalize the result to every Qwen3.6-27B quantization or runtime.

---

# 🤖 Coding Agent

The current coding agent is:

> **Pi**

The hardware profile specifies that Pi runs in a separate Ubuntu VM.

```text
🤖 Pi
   │
   ▼
Ubuntu VM
   │
   ▼
Benchmark workload
```

The current primary experiments use:

```text
Pi 0.84.1
```

The exact version must be captured for every run.

---

# 📐 Primary Benchmark Configuration

| Layer | Configuration |
|---|---|
| 💻 Hardware | Apple M4 Pro |
| 💾 Memory | 64 GB unified |
| 🍎 Host OS | macOS |
| 🖥️ Agent environment | Ubuntu VM |
| 🤖 Agent | Pi 0.84.1 |
| 🧠 Model | Qwen3.6-27B |
| 📦 Quantization | oQ4e |
| 🚀 MTP | Enabled |
| ⚡ Runtime | oMLX / MLX |
| 📐 Context | 55K for primary comparison |
| 🔧 Workload | Task 01 real software repair |

The **55K configuration is the primary Mac run used for the RTX-vs-M4 comparison**.

A separate unlimited-context Mac run exists and should be analyzed independently.

---

# 🔬 Role in the Initial Experiment

```text
                     🧪 Task 01
                         │
                         ▼
                 Same baseline
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
        🍎 M4 Pro 64 GB     🟢 RTX 5060 Ti
                │                 │
             oMLX              llama.cpp
                │                 │
                ▼                 ▼
          Qwen3.6-27B        Qwen3.6-27B
                │                 │
                ▼                 ▼
               Pi                Pi
                │                 │
                └────────┬────────┘
                         ▼
                  Compare outcomes
```

The primary comparison attempts to keep workload, agent, model family, context size, and starting repository revision aligned while allowing hardware/runtime stacks to differ.

---

# 📊 Measurements

## 🚀 Inference

Where available:

- generation tokens/sec
- prompt-processing tokens/sec
- context usage
- model calls
- token consumption

## 🤖 Agent behavior

- tool calls
- repair iterations
- test attempts
- recovery behavior
- context behavior
- session trajectory

## 🧪 Software-engineering outcome

- wall-clock repair time
- repair success/failure
- tests passed
- tests failed
- final patch
- files modified

## 💾 System resources

- peak unified-memory usage
- CPU utilization where captured
- GPU utilization where available
- power/energy measurements where available

---

# ⏱️ Why Wall-Clock Time Matters

LCAB measures more than token generation:

```text
Task received
     │
     ▼
🤖 Pi reasoning
     │
     ▼
🔎 Repository exploration
     │
     ▼
✏️ Code modification
     │
     ▼
🔧 Tool execution
     │
     ▼
🧪 Tests
     │
     ▼
🔄 Recovery / iteration
     │
     ▼
✅ Validated repair
```

Therefore:

> **Wall-clock repair time is a primary software-engineering measurement.**

Generation throughput remains useful for explaining the end-to-end result.

---

# 🧮 Memory Considerations

The 64 GB unified-memory configuration is relevant to large local models and long-context workloads.

```text
64 GB Unified Memory
        │
        ├── 🧠 Model / inference
        ├── 🤖 Coding agent
        ├── 🖥️ Ubuntu VM
        ├── 🍎 macOS
        └── Other processes
```

Consequently, memory observations should be captured at the system level with the measurement method documented.

---

# 🧪 55K Context Experiment

The primary M4 Pro benchmark uses:

```text
Context window: 55,000
MTP:            Enabled
Agent:          Pi 0.84.1
Model:          Qwen3.6-27B
Runtime:        oMLX / MLX
```

This is intended to be compared with the RTX 5060 Ti configuration using the same 55K context target.

The experimental question is:

> **How does the complete local coding-agent stack behave when the same real software-repair workload is executed with Qwen3.6-27B on an M4 Pro/oMLX system versus an RTX 5060 Ti/llama.cpp system?**

---

# 🧪 Unlimited-Context Experiment

A separate M4 Pro run was performed with an unlimited-context configuration.

Keep it separate:

```text
Primary:
M4 Pro + oMLX + 55K
        │
        └── compare with RTX 55K

Exploratory:
M4 Pro + oMLX + unlimited
        │
        └── study context / agent trajectory
```

The unlimited run should not be used to make hardware-level claims.

---

# ⚖️ Comparison Caveat

The M4 Pro and RTX configurations use different inference runtimes:

```text
🍎 M4 Pro
   └── oMLX / MLX

🟢 RTX 5060 Ti
   └── llama.cpp
```

They also use platform-specific model formats/quantizations.

Therefore, describe results as complete configurations:

> **M4 Pro + oMLX + Qwen3.6-27B + Pi**

rather than simply:

> **M4 Pro**

This distinction is essential for defensible conclusions.

---

# 📋 Reproducibility Checklist

Before an M4 Pro benchmark:

```text
☐ Apple M4 Pro confirmed
☐ 64 GB unified memory confirmed
☐ macOS version recorded
☐ Ubuntu VM configuration recorded
☐ oMLX / MLX version recorded
☐ Qwen3.6-27B identifier recorded
☐ Quantization recorded
☐ MTP configuration recorded
☐ Pi version recorded
☐ Context size recorded
☐ Task ID recorded
☐ Baseline Git commit recorded
☐ Working tree clean
☐ Run ID created
```

During:

```text
☐ Start timestamp captured
☐ Agent session captured
☐ Tool trajectory preserved
☐ No manual repository intervention
☐ Resource measurements captured where available
```

After:

```text
☐ End timestamp captured
☐ Tests captured
☐ Final Git state captured
☐ Final patch captured
☐ Session exported
☐ Anomalies documented
☐ Raw evidence frozen
```

---

# 🔍 What This Profile Does — and Does Not — Establish

### Establishes

- Apple M4 Pro hardware used by LCAB
- 64 GB unified-memory configuration
- macOS host
- separate Ubuntu VM for Pi
- oMLX / MLX runtime
- Qwen3.6-27B model configuration
- role in the initial LCAB comparison

### Does not establish

- that all M4 Pro systems perform identically
- that oMLX is universally faster than llama.cpp
- that Qwen3.6-27B is universally optimal on Apple Silicon
- that M4 Pro is universally faster or slower than RTX 5060 Ti
- that one runtime is superior for every workload

Those claims require additional controlled experiments.

---

# 🌟 Why This System Is Interesting

```text
🍎 Apple Silicon
        +
💾 64 GB Unified Memory
        +
⚡ MLX-based inference
        +
🧠 27B local model
        +
🤖 Coding agent
        +
📐 Long context
        +
🔧 Real software repair
```

This makes the M4 Pro a useful platform for investigating whether a high-memory consumer Apple Silicon system can provide a practical local coding-agent environment without relying on a discrete high-VRAM GPU.

---

# 🧭 Future Experiments

| Experiment | Question |
|---|---|
| 📐 Context scaling | How does 16K / 32K / 55K / larger context affect repair? |
| 🚀 MTP | Does MTP improve end-to-end repair time? |
| 🧠 Quantization | How do Qwen3.6-27B formats compare? |
| 🤖 Agent | Pi vs OpenHands on identical tasks |
| 🔧 Runtime | How do MLX/oMLX configurations differ? |
| 🧪 Repeated runs | How stable are repair outcomes? |
| 💾 Memory | How does unified-memory pressure affect long-context runs? |
| ⚡ Throughput | How does inference throughput correlate with repair time? |

---

# 🎯 Summary

```text
🍎 Apple M4 Pro
      │
      ├── 64 GB unified memory
      ├── macOS
      ├── Ubuntu VM for Pi
      ├── oMLX / MLX
      ├── Qwen3.6-27B-oQ4e-mtp
      └── Pi 0.84.1
              │
              ▼
       🔧 Real Software Repair
              │
              ▼
       📊 LCAB Measurements
```

> **Benchmark identity:** `M4 Pro + oMLX/MLX + Qwen3.6-27B + Pi`

The M4 Pro system is best understood as a **complete local coding-agent platform** whose behavior is measured through real software-repair work.
