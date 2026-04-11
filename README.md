---
title: Bug Triage Env
emoji: 🐛
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
tags:
  - openenv
---

# 🐛 Bug Triage & Fix Recommendation

> **An OpenEnv RL environment where AI agents learn to triage software bugs — just like a real engineer.**

[![Live Demo](https://img.shields.io/badge/🤗_HF_Space-Live-green)](https://karpagaganeshs-bug-triage-env.hf.space)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)]()
[![Tasks](https://img.shields.io/badge/Tasks-3_(Easy_Medium_Hard)-orange)]()

---

## What Is This?

In real-world engineering, a bug report rarely tells you everything up front. Before making a triage decision, engineers must **investigate** — read logs, check related tickets, ask the reporter for details. But investigating everything is slow. Guessing without enough data is inaccurate. The best engineers know **which questions to ask** and **when they have enough to decide**.

This environment turns that trade-off into an RL problem:

```
🐛 Brief Bug Report
   ↓
🔍 Investigate? (costs budget)  ←──── strategic choice
   ↓                                   │
📋 More Info Revealed                  │
   ↓                                   │
✅ Submit Triage ──────────────────────
   ↓
🏆 Score = Accuracy × Efficiency
```

The agent sees a brief bug description and at each step chooses: **investigate further** (costing limited budget) or **triage now** (classify and move on). Smarter investigation strategy → higher score.

---

## Baseline Scores

Tested with **Qwen/Qwen2.5-72B-Instruct** via HuggingFace Inference Router:

| Task | Score | What's Tested |
|------|:-----:|---------------|
| Easy | **0.99** | Bug type classification with full info |
| Medium | **0.68** | Type + severity with 10 investigation budget |
| Hard | **0.67** | Full triage (type + severity + fix) with only 6 budget |
| **Average** | **0.78** | |

---

## Three Difficulty Tiers

### 🟢 Easy — Full-Information Classification
- **5 bugs** sampled from a pool of 10
- All investigation info shown upfront — no budget needed
- Classify `bug_type` only (ui / backend / security)
- **Grading:** 100% accuracy (1.0 if correct, 0.0 if wrong)

### 🟡 Medium — Investigate & Classify
- **5 bugs** sampled from a pool of 10 · **Budget: 10 investigations**
- Agent starts with a brief description only
- Must investigate (logs / related / reporter) before triaging
- Classify `bug_type` + `severity`
- **Grading:** 70% accuracy + 30% efficiency

### 🔴 Hard — Strategic Triage Under Pressure
- **5 bugs** sampled from a pool of 10 · **Budget: 6 investigations**
- Ambiguous bugs with misleading signals
- Classify `bug_type` + `severity` + provide a `fix_suggestion`
- **Grading:** 60% accuracy + 40% efficiency

---

## How the Episode Works

```
reset(task="medium")  →  brief bug description

  step(investigate "logs")       →  stack trace revealed
  step(investigate "related")    →  similar past bugs revealed
  step(triage: type=backend, severity=high)   →  scored ✓, next bug

  step(investigate "reporter")   →  reporter details revealed
  step(triage: type=security, severity=critical)  →  scored ✓, next bug

  ... until all 5 bugs triaged   →  episode done, final reward returned
```

---

## Action Space

Every step sends **one** action — either investigate or triage:

| Field | Type | Values | When |
|-------|------|--------|------|
| `action_type` | string | `investigate` / `triage` | Always required |
| `investigate_target` | string | `logs` / `related` / `reporter` | When investigating |
| `bug_type` | string | `ui` / `backend` / `security` | When triaging |
| `severity` | string | `low` / `medium` / `high` / `critical` | When triaging (medium/hard) |
| `fix_suggestion` | string | free text | When triaging (hard) |

## Observation Space

Returned after every step:

| Field | Type | Description |
|-------|------|-------------|
| `bug_report` | object | Current bug (title, description, component, reporter, frequency) |
| `investigations_done` | list | Investigation results revealed so far |
| `available_investigations` | list | Remaining targets for this bug |
| `current_bug_index` | int | Which bug (1-indexed) |
| `bugs_total` | int | Total bugs in the episode |
| `investigations_used` | int | Budget spent so far |
| `investigation_budget` | int | Total budget for the episode |
| `phase` | string | `investigate` or `triage` |
| `feedback` | string | Human-readable feedback |
| `step_score` | float | Score for the last triage (0 during investigation) |
| `done` | bool | Whether the episode is complete |
| `reward` | float | 0.0 during steps, final clamped score (0.0–1.0) when `done=true` |

---

## Scoring Design

| Component | Description |
|-----------|-------------|
| **Accuracy** (0–1) | Correctness of bug classification |
| **Efficiency** (0.3–1.0) | `max(0.3, 1 - used_budget / total_budget)` — fewer investigations → higher bonus |
| **Early-guess penalty** | Triaging with 0 investigations AND wrong answer → score × 0.7 |
| **Wasted investigation penalty** | Repeating an already-investigated target → −0.05 per repeat |
| **Partial credit** | Adjacent severity guesses score 0.4 (e.g., "high" when answer is "critical") |
| **Keyword matching** | Fix suggestion quality measured by overlap with expected technical terms |
| **Reward clamping** | Final reward always clamped to [0.0, 1.0] |
| **30-bug pool** | Episodes sample randomly — agents can't memorize answers |
| **Per-step feedback** | `reward=0.0` during investigation, `step_score` after each triage, full reward at episode end |

---

## API Endpoints

All stateful interactions (multi-step episodes) go through **WebSocket** (`/ws`).  
HTTP endpoints are stateless — each request creates a fresh environment.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/state` | Current environment state (stateless — shows defaults) |
| `GET` | `/docs` | Swagger / OpenAPI docs |
| `POST` | `/reset` | Start a new episode (`{"task": "easy"}`) |
| `POST` | `/step` | Submit an action (investigate or triage) |
| `WS` | `/ws` | **WebSocket — primary interface** for stateful multi-step episodes |
| `GET` | `/` | Interactive web UI — try the environment in your browser |

---

## Quick Start

### Install & Run Locally

```bash
# Clone and install
git clone https://huggingface.co/spaces/karpagaganeshs/bug-triage-env
cd bug-triage-env
pip install -r requirements.txt

# Start the server
uvicorn bug_triage_env.server:app --host 0.0.0.0 --port 7860

# Test it
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{"task":"easy"}'
```

### Run with Docker

```bash
docker build -t bug-triage-env .
docker run -p 7860:7860 bug-triage-env
```

### Run the Baseline Agent

```bash
export HF_TOKEN="your-huggingface-token"
python inference.py
```

The inference script defaults to:
- **Model:** `Qwen/Qwen2.5-72B-Instruct`
- **API:** `https://router.huggingface.co/v1`
- **Environment:** `https://karpagaganeshs-bug-triage-env.hf.space`

---

## Project Structure

```
rl_env/
├── bug_triage_env/             # Core environment package
│   ├── __init__.py             # Package exports
│   ├── models.py               # Action, Observation, State (Pydantic models)
│   ├── env.py                  # Multi-step investigation environment logic
│   ├── tasks.py                # 30-bug pool with investigation layers
│   ├── grader.py               # Deterministic accuracy + efficiency scoring
│   ├── server.py               # FastAPI app + interactive web UI
│   └── client.py               # GenericEnvClient subclass
├── server/
│   └── app.py                  # Entry point for openenv validate
├── inference.py                # Baseline LLM agent (WebSocket)
├── openenv.yaml                # OpenEnv manifest (3 tasks)
├── Dockerfile                  # Docker build (python:3.11-slim, port 7860)
├── pyproject.toml              # Package metadata + scripts
├── requirements.txt            # Python dependencies
├── uv.lock                     # Lockfile
└── README.md
```

---

## Inference Log Format

The inference script outputs structured logs in the required format:

```
[START] task=easy env=bug_triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=triage backend reward=1.00 done=false error=null
[STEP] step=2 action=investigate logs reward=0.00 done=false error=null
[STEP] step=3 action=triage ui medium reward=0.69 done=false error=null
...
[END] success=true steps=5 rewards=1.00,1.00,1.00,1.00,1.00
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | [OpenEnv](https://github.com/openenv) (`openenv-core`) |
| Server | FastAPI + Uvicorn |
| Models | Pydantic v2 |
| Inference | OpenAI-compatible API (HF Router) |
| Container | Docker (python:3.11-slim) |
| Hosting | Hugging Face Spaces |

---

## License

MIT