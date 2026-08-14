# 🖥️ Windows + RTX 5060 Ti

> **NVIDIA GPU benchmark system for the Local Coding Agent Benchmark**

This machine represents the **NVIDIA GPU side of the LCAB hardware/runtime comparison**.

The benchmark evaluates this as a **complete local coding-agent stack**, not as an isolated GPU benchmark.

```text
🪟 Windows 11 Pro
        │
        ▼
🧠 Intel Core i5-8600
        │
        ▼
🎮 NVIDIA RTX 5060 Ti
        │
        ├── 16 GB VRAM
        │
        ▼
⚡ llama.cpp
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

---

# 🧾 System Summary

| Component | Specification |
|---|---|
| 🖥️ System | Windows PC |
| 🪟 Operating System | Windows 11 Pro |
| 🧠 CPU | Intel Core i5-8600 @ 3.10 GHz |
| 🎮 GPU | NVIDIA RTX 5060 Ti |
| 💾 GPU Memory | 16 GB VRAM |
| 🧮 System Memory | 50 GB RAM |
| 💿 Storage | 400 GB SSD |
| ⚡ Inference Runtime | llama.cpp |
| 🤖 Coding Agent | Pi |
| 🖥️ Pi Environment | Separate Ubuntu VM |
| 🧠 Model | Qwen3.6-27B |
| 📦 Model configuration | Qwen3.6-27B pure GGUF |

The current hardware profile identifies the model as the `Qwen3.6-27B-pure-GGUF` configuration.

---

# 🏗️ Benchmark Stack

The system should be understood as several layers:

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
│              Pure GGUF configuration          │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│                  ⚡ llama.cpp                  │
│             Local inference runtime           │
└───────────────────────┬──────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────┐
│              🎮 RTX 5060 Ti                  │
│                  16 GB VRAM                  │
└──────────────────────────────────────────────┘
```

> ℹ️ **Important:** Pi is documented as running in a separate Ubuntu VM. The VM arrangement should therefore be treated as part of the benchmark configuration.

---

# 🎮 GPU and Memory Architecture

The RTX configuration uses a discrete NVIDIA GPU with:

```text
RTX 5060 Ti
     │
     └── 16 GB dedicated VRAM
```

Conceptually:

```text
                 🖥️ Windows PC
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
       🧠 CPU                  🎮 RTX 5060 Ti
   Intel i5-8600                 16 GB VRAM
          │                         │
          │                         ▼
          │                    🧠 Model
          │                         │
          └────────────┬────────────┘
                       ▼
                    50 GB RAM
```

Unlike the M4 Pro system, this configuration has separate CPU system memory and GPU VRAM.

For LCAB, this distinction matters when interpreting memory pressure:

```text
🧮 System RAM
      ≠
🎮 GPU VRAM
```

Both should be reported separately whenever measurements are available.

---

# ⚡ Inference Runtime

The NVIDIA configuration uses:

> **llama.cpp**

The runtime is part of the experimental configuration.

```text
RTX 5060 Ti
     +
llama.cpp
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
| Runtime | llama.cpp |
| Runtime version / commit | Record at run time |
| Model | Exact identifier |
| Quantization | Exact format |
| Context | Exact window |
| MTP | Enabled / disabled |
| Sampling | Exact parameters |
| GPU offload settings | Record when relevant |
| Other runtime options | Record when relevant |

> ⚠️ A result represents the tested llama.cpp configuration, not every possible llama.cpp setup.

---

# 🧠 Model

Current model family:

```text
Qwen3.6-27B
```

Current RTX benchmark configuration:

```text
Qwen3.6-27B-MTP-4.5bpw-pure.gguf
```

The model configuration should be recorded together with:

```text
Model identity
      │
      ├── Family: Qwen3.6
      ├── Size: 27B
      ├── Format: GGUF
      ├── Quantization: 4.5 bpw
      └── MTP: enabled
```

> ⚠️ Do not generalize the benchmark result to every Qwen3.6-27B GGUF or every quantization.

---

# 🤖 Coding Agent

The coding agent is:

> **Pi**

The current hardware profile specifies that Pi runs in a separate Ubuntu VM.

```text
🤖 Pi
   │
   ▼
Ubuntu VM
   │
   ▼
Benchmark workload
```

The current primary benchmark uses:

```text
Pi 0.84.1
```

The exact agent version must be recorded for every run.

---

# 📐 Primary Benchmark Configuration

| Layer | Configuration |
|---|---|
| 🖥️ Hardware | Windows PC |
| 🧠 CPU | Intel Core i5-8600 |
| 🎮 GPU | RTX 5060 Ti |
| 💾 GPU memory | 16 GB VRAM |
| 🧮 System memory | 50 GB RAM |
| 🪟 Host OS | Windows 11 Pro |
| 🖥️ Agent environment | Ubuntu VM |
| 🤖 Agent | Pi 0.84.1 |
| 🧠 Model | Qwen3.6-27B |
| 📦 Quantization | 4.5 bpw pure GGUF |
| 🚀 MTP | Enabled |
| ⚡ Runtime | llama.cpp |
| 📐 Context | 55K for primary comparison |
| 🔧 Workload | Task 01 real software repair |

The 55K configuration is the **primary RTX run used for comparison with the M4 Pro**.

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
        🟢 RTX 5060 Ti      🍎 M4 Pro 64 GB
                │                 │
             llama.cpp           oMLX
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

The primary experiment keeps the workload, agent, model family, context size, and starting repository revision aligned as closely as practical while allowing the hardware/runtime stack to differ.

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

## 🎮 System resources

- peak GPU VRAM
- peak system RAM
- GPU utilization where captured
- CPU utilization where captured
- power/energy measurements where available

---

# ⏱️ Why Wall-Clock Time Matters

LCAB measures the entire repair trajectory:

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

Generation throughput is useful as an explanatory metric, but it is not the benchmark's sole objective.

---

# 💾 VRAM vs System RAM

The RTX configuration has two distinct memory pools:

```text
              RTX Configuration
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     🎮 16 GB VRAM          🧮 50 GB RAM
          │                     │
          │                     ├── Windows
          │                     ├── Ubuntu VM
          │                     └── Agent / tools
          │
          └── Model / GPU workload
```

This differs fundamentally from the M4 Pro's unified-memory architecture.

Consequently, LCAB should report:

- peak VRAM separately;
- peak system RAM separately;
- measurement method and sampling interval where available.

A 16 GB VRAM specification should not be interpreted as equivalent to 16 GB of total system memory.

---

# 🧪 55K Context Experiment

The primary RTX benchmark uses:

```text
Context window: 55,000
MTP:            Enabled
Agent:          Pi 0.84.1
Model:          Qwen3.6-27B
Runtime:        llama.cpp
```

This is intended to be compared with the M4 Pro primary run using:

```text
Context window: 55,000
MTP:            Enabled
Agent:          Pi 0.84.1
Model:          Qwen3.6-27B
Runtime:        oMLX / MLX
```

The experimental question is:

> **How does the complete local coding-agent stack behave when the same real software-repair workload is executed with Qwen3.6-27B on an RTX 5060 Ti/llama.cpp system versus an M4 Pro/oMLX system?**

---

# 🗃️ Baseline and Branch Provenance

The primary benchmark runs use the same starting repository revision:

```text
9ab2b50bc2ceca42b4a225aef7b9669d3c88c4f7
```

The RTX benchmark branch is:

```text
benchmark/task9-rtx5060ti-mtp
```

The primary Mac comparison branch is:

```text
benchmark/task9-m4pro-omlx-mtp-55k
```

Conceptually:

```text
                         Baseline
                     9ab2b50bc2ce...
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
       benchmark/task9-rtx...   benchmark/task9-m4...
                 │                   │
                 ▼                   ▼
           RTX / llama.cpp       M4 / oMLX
                55K                 55K
```

This shared baseline is important because it reduces one major source of experimental variation: different starting repository states.

---

# ⚖️ Comparison Caveat

The RTX and M4 systems differ in:

```text
Hardware architecture
        +
Operating system
        +
Inference runtime
        +
Model representation / quantization
```

The comparison is therefore a comparison of **complete tested configurations**.

Use:

> **RTX 5060 Ti + llama.cpp + Qwen3.6-27B + Pi**

rather than simply:

> **RTX 5060 Ti**

Likewise, avoid describing the result as a universal hardware benchmark.

---

# 📋 Reproducibility Checklist

Before an RTX benchmark:

```text
☐ RTX 5060 Ti confirmed
☐ 16 GB VRAM confirmed
☐ Intel i5-8600 confirmed
☐ 50 GB system RAM confirmed
☐ Windows version recorded
☐ Ubuntu VM configuration recorded
☐ llama.cpp version/commit recorded
☐ Qwen3.6-27B identifier recorded
☐ GGUF / quantization recorded
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
☐ VRAM/RAM measurements captured where available
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

- NVIDIA RTX 5060 Ti system used by LCAB
- 16 GB dedicated VRAM
- 50 GB system RAM
- Intel i5-8600 host
- Windows 11 Pro host
- separate Ubuntu VM for Pi
- llama.cpp runtime
- Qwen3.6-27B GGUF configuration
- role in the initial 55K comparison

### Does not establish

- that all RTX 5060 Ti systems perform identically;
- that llama.cpp is universally faster than oMLX;
- that the tested GGUF quantization is universally optimal;
- that RTX 5060 Ti is universally faster or slower than M4 Pro;
- that one hardware architecture is better for every coding workload.

Those conclusions require additional controlled experiments.

---

# 🌟 Why This System Is Interesting

The RTX configuration combines:

```text
🎮 16 GB dedicated VRAM
        +
🧮 50 GB system RAM
        +
⚡ llama.cpp
        +
🧠 27B local model
        +
🤖 Coding agent
        +
📐 55K context
        +
🔧 Real software repair
```

This makes it a useful example of a relatively constrained local NVIDIA GPU running a large coding model through a highly optimized inference runtime.

The benchmark can therefore investigate an important practical question:

> **How competitive is a 16 GB consumer GPU when the workload is a real coding-agent task rather than a synthetic token-generation benchmark?**

---

# 🧭 Future Experiments

| Experiment | Question |
|---|---|
| 🚀 MTP | How much does MTP change end-to-end repair time? |
| 📐 Context scaling | How do 16K / 32K / 55K contexts affect repair? |
| 🧠 Quantization | How do different Qwen3.6-27B GGUF formats compare? |
| ⚙️ llama.cpp tuning | How do offload/batching/runtime parameters affect results? |
| 🤖 Agent | Pi vs OpenHands on identical tasks |
| 🧪 Repeated runs | How stable are repair outcomes? |
| 🎮 VRAM pressure | How does memory pressure affect long-context work? |
| ⚡ Throughput | How strongly does generation speed correlate with repair time? |
| 🔄 Recovery | Do faster inference configurations reduce recovery cost? |

---

# 🎯 Summary

```text
🖥️ Windows 11 Pro
      │
      ├── Intel i5-8600
      ├── RTX 5060 Ti
      ├── 16 GB VRAM
      ├── 50 GB RAM
      ├── Ubuntu VM for Pi
      ├── llama.cpp
      ├── Qwen3.6-27B-MTP 4.5bpw GGUF
      └── Pi 0.84.1
              │
              ▼
       🔧 Real Software Repair
              │
              ▼
       📊 LCAB Measurements
```

> **Benchmark identity:** `RTX 5060 Ti + llama.cpp + Qwen3.6-27B + Pi`

The RTX 5060 Ti system is therefore best understood as a **complete local coding-agent platform**, whose practical performance is evaluated through real software-repair work rather than isolated inference throughput.
