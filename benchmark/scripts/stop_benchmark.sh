
export RUN_DIR="/home/amit/projects/local-coding-agent-benchmark/results/raw/20260813-122237-task01-windows-rtx5060-llama"
export RUN_ID="20260813-122237-task01-windows-rtx5060-llama"

echo "Run directory: ${RUN_DIR}"
echo "Run ID: ${RUN_ID}"



END_TIME=$(date +%s)
END_ISO=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

DURATION=$((END_TIME - START_TIME))

echo "END_TIME=$END_TIME" | tee -a "${RUN_DIR}/timing.txt"
echo "END_ISO=$END_ISO" | tee -a "${RUN_DIR}/timing.txt"
echo "WALL_TIME_SECONDS=$DURATION" | tee -a "${RUN_DIR}/timing.txt"
echo "WALL_TIME_MINUTES=$(awk "BEGIN {printf \"%.2f\", $DURATION/60}")" | tee -a "${RUN_DIR}/timing.txt"

export SESSION_FILE=`find "${RUN_DIR}/pi-session" -type f -name "*.jsonl"`

cp "${SESSION_FILE}" "${RUN_DIR}/pi-session.jsonl"

pi --export  "${SESSION_FILE}"   "${RUN_DIR}/pi-session.html"

git status --short > "${RUN_DIR}/git-after.txt"

git rev-parse HEAD >> "${RUN_DIR}/git-after.txt"

git diff --stat >> "${RUN_DIR}/git-after.txt"

#Save the complete patch:

git diff > "${RUN_DIR}/diff.patch"

#pytest 2>&1 | tee "${RUN_DIR}/tests.txt"