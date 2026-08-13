# 🍎 Mac + M4 Pro

**Local AI Coding Agent Benchmark System**

| Component           | Specification        |
| ------------------- | -------------------- |
| 💻 System           | Mac                  |
| 🧠 SoC              | Apple M4 Pro         |
| 🎮 GPU              | Integrated Apple GPU |
| 💾 Unified Memory   | 64 GB                |
| 💿 Storage          | 100 GB Free          |
| 🍎 Operating System | macOS                |
| ⚡ Inference Runtime | oMLX / MLX           |
| 🤖 Current Agent    | Pi (running in separate Ubuntu VM)|
| 🧠 Current Model    | Qwen3.6-27B (https://huggingface.co/Jundot/Qwen3.6-27B-oQ4e-mtp)|

## 🎯 Role in Benchmark

This system represents the **Apple Silicon-based local coding-agent configuration**.

```text
🍎 macOS
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

## 📊 Measurements

The following measurements are collected during benchmark experiments:

* 🚀 Generation tokens/sec
* 📥 Prompt processing tokens/sec
* 🧠 Context usage
* 💾 Peak unified memory usage
* ⏱️ Wall-clock repair time
* 🔧 Tool calls
* 🔄 Repair iterations
* 🧪 Test attempts
* ✅ Repair success/failure

## 📝 Notes

This configuration is evaluated as a **complete local coding-agent stack**.

Benchmark results should not be interpreted as a hardware-only comparison against the NVIDIA system.
