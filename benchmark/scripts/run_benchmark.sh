export RUN_DIR="/home/amit/projects/local-coding-agent-benchmark/results/raw/20260813-122237-task01-windows-rtx5060-llama"
export RUN_ID="20260813-122237-task01-windows-rtx5060-llama"

echo "Run directory: ${RUN_DIR}"
echo "Run ID: ${RUN_ID}"


START_TIME=$(date +%s)
START_ISO=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

echo "START_TIME=$START_TIME" | tee "${RUN_DIR}/timing.txt"
echo "START_ISO=$START_ISO" | tee -a "${RUN_DIR}/timing.txt"

mkdir -p "${RUN_DIR}/pi-session"

pi \
  --session-dir "${RUN_DIR}/pi-session" \
  --name "${RUN_ID}" \
  --model llamacpp/Qwen3.6-27B-MTP-4.5bpw-pure.gguf