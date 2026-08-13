export BENCHMARK_REPO=~/projects/local-coding-agent-benchmark
export CURRENT_DIR=`pwd`


#export TASK_ID="task01-windows-rtx5060-llama"
#export RUN_ID="$(date '+%Y%m%d-%H%M%S')-${TASK_ID}"

mkdir -p "${BENCHMARK_REPO}/results/raw/${RUN_ID}"

export RUN_DIR="${BENCHMARK_REPO}/results/raw/${RUN_ID}"

echo "Run directory: ${RUN_DIR}"
echo "Run ID: ${RUN_ID}"
pi --version > "${RUN_DIR}/pi-version.txt"


git rev-parse HEAD | tee "${RUN_DIR}/git-before.txt"

git status --short | tee -a "${RUN_DIR}/git-before.txt"

git diff --stat | tee -a "${RUN_DIR}/git-before.txt"
git diff > "${RUN_DIR}/diff-before.patch"

###############################################
# Update Specific before starting the benchmark Run
#################################################
cat > "${RUN_DIR}/metadata.txt" <<EOF
Run ID: ${RUN_ID}
Task ID: ${TASK_ID}
Date: $(date '+%Y-%m-%d %H:%M:%S %Z')
Hostname: 110.100.1.288
OS: Windows 11, RTX 5060 TI
Working Directory: $(pwd)

LLM Serving Engine: llama.cpp
Agent: Pi
Model: Qwen3.6-27B-MTP-4.5bpw-pure.gguf
Context Limit: 
        "contextWindow": 55000,
        "maxTokens": 18384,

EOF