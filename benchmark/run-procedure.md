# 🧪 Pi Benchmark Run Procedure

This document defines the standard procedure for running **one benchmark iteration** with the Pi coding agent.

The goal is to capture enough information to reproduce and analyze every run.

Each iteration gets its own directory containing:

```text
benchmark/results/raw/
└── <run-id>/
    ├── metadata.txt
    ├── timing.txt
    ├── git-before.txt
    ├── git-after.txt
    ├── diff.patch
    ├── tests.txt
    ├── pi-session.jsonl
    ├── pi-session.html
    └── system-info.txt
```

---

# 1. What We Capture

For every Pi run, capture:

| Category  | Metric                     |
| --------- | -------------------------- |
| ⏱️ Timing | Start time                 |
| ⏱️ Timing | End time                   |
| ⏱️ Timing | Wall-clock duration        |
| 🤖 Pi     | Session ID                 |
| 🤖 Pi     | Session JSONL              |
| 💬 Pi     | Full conversation          |
| 🧠 Model  | Model/provider             |
| 🧠 Model  | Token usage                |
| 🧠 Model  | Thinking level             |
| 🔧 Agent  | Tool calls                 |
| 🔧 Agent  | Iterations                 |
| 🧪 Tests  | Test commands              |
| 🧪 Tests  | Test output                |
| 📦 Git    | Starting commit            |
| 📦 Git    | Final commit               |
| 📝 Git    | Final diff                 |
| 💾 System | RAM usage                  |
| 🎮 GPU    | VRAM usage where available |
| 💻 System | OS / hardware information  |

The raw Pi session is especially important because Pi stores sessions as JSONL and the session contains the conversation, tool results, model information, timestamps, and other session events.

---

# 2. Run ID

Every benchmark iteration must have a unique run ID.

Recommended format:

```text
YYYYMMDD-HHMMSS-taskNN-runNN
```

Example:

```text
20260813-061530-task01-run01
```

If the same task is repeated three times:

```text
20260813-061530-task01-run01
20260813-073210-task01-run02
20260813-084455-task01-run03
```

Never overwrite an existing run directory.

---

# 3. Create the Run Directory

## macOS / Linux

From the repository root:

```bash
export TASK_ID="task01"
export RUN_ID="$(date '+%Y%m%d-%H%M%S')-${TASK_ID}"

mkdir -p "benchmark/results/raw/${RUN_ID}"

export RUN_DIR="benchmark/results/raw/${RUN_ID}"

echo "Run directory: ${RUN_DIR}"
```

Example:

```text
benchmark/results/raw/20260813-061530-task01/
```

---

## Windows PowerShell

```powershell
$TASK_ID = "task01"
$RUN_ID = "$(Get-Date -Format 'yyyyMMdd-HHmmss')-$TASK_ID"

$RUN_DIR = "benchmark/results/raw/$RUN_ID"

New-Item -ItemType Directory -Force -Path $RUN_DIR | Out-Null

Write-Host "Run directory: $RUN_DIR"
```

---

# 4. Record Benchmark Metadata

Create the metadata file before starting Pi.

## macOS / Linux

```bash
cat > "${RUN_DIR}/metadata.txt" <<EOF
Run ID: ${RUN_ID}
Task ID: ${TASK_ID}
Date: $(date '+%Y-%m-%d %H:%M:%S %Z')
Hostname: $(hostname)
OS: $(uname -a)
Working Directory: $(pwd)

Agent: Pi
Model: Qwen3.6-27B
EOF
```

## Windows PowerShell

```powershell
@"
Run ID: $RUN_ID
Task ID: $TASK_ID
Date: $(Get-Date)
Hostname: $env:COMPUTERNAME
OS: $([System.Environment]::OSVersion.VersionString)
Working Directory: $(Get-Location)

Agent: Pi
Model: Qwen3.6-27B
"@ | Out-File "$RUN_DIR/metadata.txt"
```

Add the exact runtime configuration to this file before publishing the benchmark.

---

# 5. Record Git State Before the Run

This is critical.

The benchmark must know exactly what repository state Pi started with.

## macOS / Linux

```bash
git rev-parse HEAD | tee "${RUN_DIR}/git-before.txt"

git status --short | tee -a "${RUN_DIR}/git-before.txt"

git diff --stat | tee -a "${RUN_DIR}/git-before.txt"
```

Also capture the full starting diff:

```bash
git diff > "${RUN_DIR}/diff-before.patch"
```

For a clean benchmark run, ideally:

```text
git status --short
```

returns nothing.

---

## Windows PowerShell

```powershell
git rev-parse HEAD | Tee-Object "$RUN_DIR/git-before.txt"

git status --short | Tee-Object "$RUN_DIR/git-before.txt" -Append

git diff --stat | Tee-Object "$RUN_DIR/git-before.txt" -Append

git diff | Out-File "$RUN_DIR/diff-before.patch"
```

---

# 6. Record Pi Version

Before each benchmark session:

```bash
pi --version
```

or:

```bash
pi -v
```

Save it:

```bash
pi --version > "${RUN_DIR}/pi-version.txt"
```

Windows:

```powershell
pi --version | Out-File "$RUN_DIR/pi-version.txt"
```

This is important because Pi itself evolves over time.

---

# 7. Record Hardware / Runtime Information

## Windows + RTX 5060 Ti

Capture:

```powershell
nvidia-smi | Out-File "$RUN_DIR/gpu-info.txt"
```

Also:

```powershell
systeminfo | Out-File "$RUN_DIR/system-info.txt"
```

If you want the GPU details in a more compact format:

```powershell
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv |
    Out-File "$RUN_DIR/gpu-info.txt"
```

---

## macOS + M4 Pro

Capture:

```bash
system_profiler SPHardwareDataType > "${RUN_DIR}/system-info.txt"
```

Also:

```bash
sw_vers > "${RUN_DIR}/os-info.txt"
```

And:

```bash
sysctl -n hw.memsize > "${RUN_DIR}/memory-info.txt"
```

---

# 8. Start the Wall-Clock Timer

The timer should start **immediately before launching Pi**.

## macOS / Linux

```bash
START_TIME=$(date +%s)
START_ISO=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

echo "START_TIME=$START_TIME" | tee "${RUN_DIR}/timing.txt"
echo "START_ISO=$START_ISO" | tee -a "${RUN_DIR}/timing.txt"
```

## Windows PowerShell

```powershell
$START = Get-Date
$START_UNIX = [DateTimeOffset]$START

"START_TIME=$START" | Out-File "$RUN_DIR/timing.txt"
"START_UNIX=$($START_UNIX.ToUnixTimeSeconds())" | Out-File "$RUN_DIR/timing.txt" -Append
```

---

# 9. Start Pi With a Dedicated Session Directory

This is the recommended approach.

Instead of allowing the benchmark session to disappear into the normal Pi session directory, give each benchmark run its own session directory.

Pi supports `--session-dir` specifically for controlling where session files are stored.

## macOS / Linux

```bash
mkdir -p "${RUN_DIR}/pi-session"

pi \
  --session-dir "${RUN_DIR}/pi-session" \
  --name "${RUN_ID}"
```

## Windows PowerShell

```powershell
New-Item -ItemType Directory -Force -Path "$RUN_DIR/pi-session" | Out-Null

pi `
  --session-dir "$RUN_DIR/pi-session" `
  --name "$RUN_ID"
```

Pi will automatically save the session as JSONL.

---

# 10. Give Pi the Benchmark Task

Use exactly the same task prompt for every system being compared.

For example:

```text
Fix the following issue:

[benchmark task description]

You have access to the repository and may inspect files,
modify code, and run tests.

Complete the repair and verify the implementation with the
appropriate tests.

Do not ask me for implementation guidance. Investigate and
solve the problem independently.
```

The exact task prompt should be stored in:

```text
benchmark/tasks/task01.md
```

Do **not** manually modify the prompt between benchmark systems unless the experiment explicitly tests prompt differences.

---

# 11. During the Pi Run

Do not manually intervene unless the benchmark methodology explicitly permits intervention.

Allow Pi to:

* inspect files
* search the repository
* modify files
* run commands
* run tests
* analyze failures
* iterate
* recover from mistakes

Do not provide hints that would not be available to another benchmark system.

---

# 12. Check Pi Session Information

At any point inside Pi:

```text
/session
```

Pi displays session information including:

* session file
* session ID
* message count
* tokens
* cost

This is useful for recording the final session information.

At the end of the benchmark run, use:

```text
/session
```

and record the information in:

```text
session-summary.txt
```

---

# 13. Export the Pi Conversation

Pi supports exporting a session to HTML.

After the benchmark run, identify the session JSONL file:

## macOS / Linux

```bash
find "${RUN_DIR}/pi-session" -type f -name "*.jsonl"
```

## Windows PowerShell

```powershell
Get-ChildItem "$RUN_DIR/pi-session" -Filter *.jsonl -Recurse
```

Suppose the session is:

```text
benchmark/results/raw/20260813-061530-task01/pi-session/20260813-061530_xxxxx.jsonl
```

Export it:

```bash
pi --export \
  "benchmark/results/raw/20260813-061530-task01/pi-session/20260813-061530_xxxxx.jsonl" \
  "benchmark/results/raw/20260813-061530-task01/pi-session.html"
```

Pi's export functionality can produce an HTML representation of the session, which is useful as the human-readable conversation record.

---

# 14. Preserve the Raw Pi JSONL

The JSONL session is the **primary raw conversation artifact**.

Copy it to the run directory:

```bash
cp "${SESSION_FILE}" "${RUN_DIR}/pi-session.jsonl"
```

Windows:

```powershell
Copy-Item $SESSION_FILE "$RUN_DIR/pi-session.jsonl"
```

Do not modify this file.

The JSONL should remain the authoritative record of the Pi run.

---

# 15. End the Wall-Clock Timer

Immediately after Pi finishes:

## macOS / Linux

```bash
END_TIME=$(date +%s)
END_ISO=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

DURATION=$((END_TIME - START_TIME))

echo "END_TIME=$END_TIME" | tee -a "${RUN_DIR}/timing.txt"
echo "END_ISO=$END_ISO" | tee -a "${RUN_DIR}/timing.txt"
echo "WALL_TIME_SECONDS=$DURATION" | tee -a "${RUN_DIR}/timing.txt"
echo "WALL_TIME_MINUTES=$(awk "BEGIN {printf \"%.2f\", $DURATION/60}")" | tee -a "${RUN_DIR}/timing.txt"
```

Example:

```text
START_TIME=1755064530
START_ISO=2026-08-13T13:55:30Z
END_TIME=1755065214
END_ISO=2026-08-13T14:06:54Z
WALL_TIME_SECONDS=684
WALL_TIME_MINUTES=11.40
```

---

## Windows PowerShell

```powershell
$END = Get-Date
$DURATION = $END - $START

"END_TIME=$END" | Out-File "$RUN_DIR/timing.txt" -Append
"WALL_TIME_SECONDS=$([math]::Round($DURATION.TotalSeconds, 3))" |
    Out-File "$RUN_DIR/timing.txt" -Append
"WALL_TIME_MINUTES=$([math]::Round($DURATION.TotalMinutes, 3))" |
    Out-File "$RUN_DIR/timing.txt" -Append
```

---

# 16. Record Final Git State

After Pi exits:

## macOS / Linux

```bash
git status --short > "${RUN_DIR}/git-after.txt"

git rev-parse HEAD >> "${RUN_DIR}/git-after.txt"

git diff --stat >> "${RUN_DIR}/git-after.txt"
```

Save the complete patch:

```bash
git diff > "${RUN_DIR}/diff.patch"
```

## Windows PowerShell

```powershell
git status --short | Out-File "$RUN_DIR/git-after.txt"

git rev-parse HEAD | Out-File "$RUN_DIR/git-after.txt" -Append

git diff --stat | Out-File "$RUN_DIR/git-after.txt" -Append

git diff | Out-File "$RUN_DIR/diff.patch"
```

This gives you the exact code Pi produced.

---

# 17. Record Test Results

The benchmark should explicitly record the validation command used.

For example:

```bash
pytest
```

Capture the output:

```bash
pytest 2>&1 | tee "${RUN_DIR}/tests.txt"
```

Or if the repository uses npm:

```bash
npm test 2>&1 | tee "${RUN_DIR}/tests.txt"
```

Or another repository-specific test command.

Record:

```text
Test command:
Test result:
Exit code:
```

The important point is that the **same validation procedure must be used for every benchmark system**.

---

# 18. Determine Benchmark Success

Create:

```text
result.txt
```

Example:

```text
RESULT=SUCCESS
TESTS=PASS
```

or:

```text
RESULT=FAILURE
TESTS=FAIL
FAILURE_REASON=Agent could not resolve failing integration test
```

Do not manually classify a run as successful merely because Pi says:

> "The fix is complete."

The benchmark validation determines success.

---

# 19. Capture Final System State

## NVIDIA

After the run:

```powershell
nvidia-smi |
    Out-File "$RUN_DIR/gpu-after.txt"
```

For a specific GPU snapshot:

```powershell
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu `
    --format=csv |
    Out-File "$RUN_DIR/gpu-after.txt"
```

---

## Apple Silicon

Capture:

```bash
top -l 1 -n 0 > "${RUN_DIR}/system-after.txt"
```

and:

```bash
memory_pressure > "${RUN_DIR}/memory-after.txt"
```

These are useful supporting measurements.

---

# 20. Recommended Run Directory

A completed benchmark run should look approximately like:

```text
benchmark/
└── results/
    └── raw/
        └── 20260813-061530-task01-run01/
            │
            ├── metadata.txt
            ├── timing.txt
            │
            ├── pi-version.txt
            ├── session-summary.txt
            │
            ├── pi-session.jsonl
            ├── pi-session.html
            │
            ├── system-info.txt
            ├── gpu-info.txt
            │
            ├── git-before.txt
            ├── diff-before.patch
            │
            ├── git-after.txt
            ├── diff.patch
            │
            ├── tests.txt
            ├── result.txt
            │
            └── pi-session/
                └── <original-session>.jsonl
```

---

# 21. One Benchmark Iteration — Complete Procedure

For every benchmark iteration, follow this sequence:

```text
┌─────────────────────────────┐
│ 1. Create unique RUN_ID     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 2. Create run directory     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 3. Record hardware/runtime  │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 4. Record Git state         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 5. Start wall-clock timer   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 6. Start Pi                 │
│    dedicated session dir    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 7. Run benchmark task       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 8. Pi completes / fails     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 9. Stop wall-clock timer    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 10. Preserve Pi JSONL       │
│     + export HTML           │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 11. Capture Git diff        │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 12. Run validation tests    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ 13. Record SUCCESS/FAILURE  │
└─────────────────────────────┘
```

---

# 22. Important: Reset Before the Next Iteration

Never start the next benchmark iteration on top of the previous agent's modifications.

After saving the results:

```bash
git reset --hard HEAD
git clean -fd
```

**Only use `git clean -fd` if the benchmark repository is disposable and you are certain there are no files you need to preserve.**

A safer approach is to restore the repository from a fresh checkout or benchmark-specific worktree.

For example:

```bash
git reset --hard <BENCHMARK_COMMIT>
```

Then verify:

```bash
git status --short
```

It should be clean.

---

# 23. Recommended: Use Git Worktrees

For serious benchmarking, use a separate Git worktree for every benchmark iteration.

For example:

```text
benchmark/workspaces/
├── task01-run01/
├── task01-run02/
├── task01-run03/
└── task02-run01/
```

Create one:

```bash
git worktree add \
    "benchmark/workspaces/${RUN_ID}" \
    <BENCHMARK_COMMIT>
```

Then run Pi inside that directory.

This is safer than repeatedly resetting the main development checkout.

---

# 24. Recommended Benchmark Separation

Keep these three things separate:

```text
┌──────────────────────────┐
│ Benchmark Definition     │
│                          │
│ tasks/                   │
│ methodology.md          │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│ Benchmark Execution      │
│                          │
│ workspaces/              │
│ Pi                       │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│ Benchmark Evidence       │
│                          │
│ results/raw/             │
│ JSONL                    │
│ HTML                     │
│ patches                  │
│ tests                    │
│ timing                   │
└──────────────────────────┘
```

This makes the benchmark easier to audit later.

---

# 25. Optional: Pi JSON Event Capture

Pi also supports:

```bash
pi --mode json
```

which outputs session events as JSON lines. The stream includes events such as:

* `agent_start`
* `turn_start`
* `message_start`
* `message_update`
* `message_end`
* `tool_execution_start`
* `tool_execution_update`
* `tool_execution_end`
* `turn_end`
* `agent_end`

This can be useful for automated metric extraction.

For example:

```bash
pi --mode json "benchmark task prompt" \
    > "${RUN_DIR}/pi-events.jsonl"
```

This is particularly useful for future automated analysis of:

```text
🤖 Model calls
🔧 Tool calls
⏱️ Turn durations
🧠 Token usage
❌ Tool failures
🔄 Compactions
```

For the initial **interactive Pi benchmark**, however, preserve the normal Pi session JSONL as the primary conversation artifact.

---

# 26. Future Automated Metrics

Once enough runs have been collected, the JSONL files can be parsed automatically to generate:

| Metric           | Source                     |
| ---------------- | -------------------------- |
| ⏱️ Wall time     | Benchmark timer            |
| 🤖 Session ID    | Pi JSONL                   |
| 💬 Conversation  | Pi JSONL                   |
| 🧠 Input tokens  | Pi usage data              |
| 🧠 Output tokens | Pi usage data              |
| 🔧 Tool calls    | Pi JSONL                   |
| ❌ Tool failures  | Pi JSONL                   |
| 🔄 Compactions   | Pi JSONL                   |
| 🧪 Test attempts | Tool execution / test logs |
| 📝 Files changed | Git diff                   |
| 📊 Lines changed | Git diff                   |
| ✅ Success        | Validation tests           |
| 🎮 VRAM          | `nvidia-smi`               |
| 💾 RAM           | OS metrics                 |

This will eventually allow the benchmark repository to generate its summary tables automatically.

---

# 27. Minimum Required Artifacts

If time is limited, **never skip these five artifacts**:

```text
1. ⏱️ timing.txt
2. 🤖 pi-session.jsonl
3. 💬 pi-session.html
4. 📝 diff.patch
5. 🧪 tests.txt
```

These provide the core evidence for:

> **How long did Pi take?**

> **What did Pi actually do?**

> **What code did Pi change?**

> **Did the repair actually work?**

---

# 28. Golden Rule

For every benchmark iteration:

> **Start clean → start timer → run Pi → preserve session → stop timer → validate → preserve patch → record result.**

Never rely on memory or screenshots for benchmark measurements.

The raw Pi session, timing data, Git diff, and test results should be the authoritative evidence for every published benchmark result.
