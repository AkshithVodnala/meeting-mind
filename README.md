# 🧠 Meeting Mind

AI-powered meeting action extractor. Paste a meeting transcript and the agent autonomously extracts action items, assigns owners, detects deadlines, flags risks, and generates a productivity score.

## Problem It Solves

After every meeting someone manually writes up who does what and by when. This wastes 20-30 minutes of senior engineer time per meeting. Meeting Mind automates this entirely in 15 seconds.

## Tech Stack

- **FastAPI** — REST API backend
- **SQLModel + SQLite** — Database
- **HuggingFace Inference API** — LLM (Qwen2.5-7B)
- **Jinja2** — HTML templates
- **Pytest** — Unit and integration tests
- **Playwright** — End-to-end browser tests
- **Docker Compose** — Containerization
- **GitHub Actions** — CI/CD pipeline

## Agentic AI Workflow

The agent runs 5 steps in sequence:
1. Extract action items
2. Assign owners
3. Detect deadlines
4. Detect risks and blockers
5. Generate summary and productivity score

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/AkshithVodnala/meeting-mind.git
cd meeting-mind
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your HuggingFace token
```

### 4. Run the app
```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000

### 5. Run with Docker
```bash
docker compose up
```

## Running Tests

```bash
# Unit tests
pytest tests/ -v

# E2E tests (server must be running)
pytest e2e/ -v
```

## CI/CD

GitHub Actions runs on every push:
- Lint with Ruff
- Pytest suite
- Playwright E2E tests
- Docker build

## Project Structure