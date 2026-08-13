# 🖥️ Windows + RTX 5060 Ti

**Local AI Coding Agent Benchmark System**

| Component           | Specification      |
| ------------------- | ------------------ |
| 🖥️ System          | Windows PC 11 Pro        |
| 🧠 CPU              | Intel i5 8600 @3.10 GHz |
| 🎮 GPU              | NVIDIA RTX 5060 Ti |
| 💾 GPU Memory       | 16 GB VRAM         |
| 🧮 System Memory    | 50 GB RAM          |
| 💿 Storage          | 400 GB SSD         |
| 🪟 Operating System | Windows            |
| ⚡ Inference Runtime | llama.cpp          |
| 🤖 Current Agent    | Pi  (running in separate Ubuntu VM)|
| 🧠 Current Model    | Qwen3.6-27B (https://huggingface.co/huytd189/Qwen3.6-27B-pure-GGUF)|

## 🎯 Role in Benchmark

This system represents the **NVIDIA GPU-based local coding-agent configuration**.

```text
🖥️ Windows
     │
     ▼
🎮 RTX 5060 Ti 16 GB
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

## 📊 Measurements

The following measurements are collected during benchmark experiments:

* 🚀 Generation tokens/sec
* 📥 Prompt processing tokens/sec
* 🧠 Context usage
* 🎮 Peak VRAM usage
* 💾 Peak system RAM usage
* ⏱️ Wall-clock repair time
* 🔧 Tool calls
* 🔄 Repair iterations
* 🧪 Test attempts
* ✅ Repair success/failure

## 📝 Notes

This configuration is evaluated as a **complete local coding-agent stack**.

Benchmark results should not be interpreted as a hardware-only comparison against Apple Silicon.
