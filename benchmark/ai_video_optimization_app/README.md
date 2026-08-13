# ai_video_optimization_app

ai_video_optimization_app is an AI video optimization application that iteratively generates, analyzes, ranks, optimizes, and evaluates video generation prompts and parameters. It automates the process of improving AI-generated video quality through a closed-loop feedback system.

## How It Works

```
Generate → Analyze → Rank → Optimize → Repeat
```

Each iteration:

1. **Generate** N candidate videos using ComfyUI with unique seeds.
2. **Analyze** each candidate via LM Studio vision model for quality scores across 10 dimensions.
3. **Rank** candidates by overall score, identity score, and motion score.
4. **Select** the best candidate as the winner for this iteration.
5. **Optimize** prompt and parameters based on QA feedback using an adaptive strategy (TARGETED, REFINE, EXPLORE, or RECOVER).
6. **Evaluate** stopping conditions (target score, max iterations, confidence, plateau, cancellation).

## Architecture

```
Browser
   |
   v
FastAPI / Web UI  (Jinja2 + HTMX + Bootstrap)
   |
   v
ai_video_optimization_app Engine
   |
   +----> ComfyUI              (external service)
   |        |
   |        +--> Generate video via workflow JSON
   |        +--> Monitor execution via WebSocket
   |        +--> Download output artifacts
   |
   +----> LM Studio            (external service)
   |        |
   |        +--> Video QA analysis (vision model)
   |        +--> Prompt/parameter optimization
   |
   +----> SQLite               (local database)
            |
            +--> Experiments, Iterations, Candidates
```

**ComfyUI** and **LM Studio** are external services. ai_video_optimization_app communicates with them over HTTP/WebSocket on the local network. They must be running before starting experiments.

## Core Workflow

```
Create Experiment
    ↓
Generate N Candidates (each with unique seed)
    ↓
Analyze All Candidates (QA scoring across 10 dimensions)
    ↓
Rank Candidates (overall_score → identity_score → motion_score)
    ↓
Select Best Candidate
    ↓
Determine Optimization Strategy
    ↓
Optimize Prompt / Parameters via LM Studio
    ↓
Evaluate Stopping Conditions
    ↓
Continue or Complete
```

### Optimization Strategies

ai_video_optimization_app adapts its optimization approach based on QA results and score history:

| Mode | When Used | Behavior |
|------|-----------|----------|
| **TARGETED** | One or more QA dimensions below threshold (default 70/100) | Focuses changes on parameters that influence weak areas |
| **REFINE** | Score is improving steadily | Makes minimal changes; preserves working configuration |
| **EXPLORE** | Progress has plateaued for N iterations | Allows larger changes to escape local optima |
| **RECOVER** | Current score regressed significantly from best | Returns toward best-known configuration with minor exploration |

### Candidate Ranking

Candidates within each iteration are ranked by:

1. `overall_score` (highest first)
2. `identity_score` (tiebreaker)
3. `motion_score` (secondary tiebreaker)

The highest-ranked candidate is selected as the winner and used for optimization.

## Features

- Experiment creation via web dashboard
- ComfyUI workflow execution with WebSocket monitoring
- Workflow parameter injection (prompt, negative prompt, seed, CFG, noise, steps)
- Video quality analysis across 10 dimensions via LM Studio vision model
- Multiple candidates per iteration with unique seeds
- Candidate ranking and winner selection
- Adaptive optimization strategy (TARGETED / REFINE / EXPLORE / RECOVER)
- Autonomous optimization loop with configurable stopping conditions
- Experiment persistence in SQLite database
- Resume support for interrupted experiments
- Cancellation of running experiments
- Best-result tracking across iterations
- Score history and progression analytics
- Per-dimension QA metric progression

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application (reads host/port from configs/default.yaml)
python -m web.app
```

Open http://localhost:7000 in your browser.

### Alternative start methods

```bash
# Via uvicorn CLI
uvicorn web.app:create_app --factory --host 0.0.0.0 --port 7000
```


## Tech Stack

- Python 3.11+
- FastAPI + Jinja2 + HTMX + Bootstrap 5
- Pydantic v2 + SQLAlchemy + SQLite
- Loguru for structured logging