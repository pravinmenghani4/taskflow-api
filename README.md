# TaskFlow API

A small, AI-scaffolded **FastAPI** task-management API — the sample project for the
module **"AI-Assisted Project Scaffolding and Environment Setup."** It demonstrates a
clean layered architecture (routes → services → models/schemas), config via
environment variables, tests, and AI **skill files** that steer GitHub Copilot / Codex.

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your local env file
cp .env.example .env

# 4. Run the API (auto-reload for development)
uvicorn app.main:app --reload

# 5. Open the interactive docs
#    http://127.0.0.1:8000/docs
```

## Verify it works

```bash
pytest -q                          # all tests should pass
curl http://127.0.0.1:8000/health  # {"status":"ok",...}
```

## Project structure

```
taskflow-api/
├── app/
│   ├── main.py              # FastAPI app: middleware, routers, startup
│   ├── core/                # config.py (settings) + database.py (engine/session)
│   ├── models/              # SQLAlchemy ORM models  (how data is stored)
│   ├── schemas/             # Pydantic schemas       (API request/response)
│   ├── services/            # business logic          (reusable, testable)
│   └── api/
│       ├── deps.py          # shared dependencies (get_db, get_task_or_404)
│       └── routes/          # thin HTTP routers (health, tasks)
├── tests/                   # pytest suite (in-memory DB)
├── skills/                  # AI skill files: Dev / debug / Security
├── .github/
│   └── copilot-instructions.md   # wires the skill files into Copilot
├── docs/                    # PRD.md + system-design.md
├── .env.example             # copy to .env
├── requirements.txt
└── .gitignore
```

## API endpoints

| Method | Path           | Description        |
|--------|----------------|--------------------|
| GET    | `/health`      | Health check       |
| GET    | `/tasks`       | List tasks         |
| POST   | `/tasks`       | Create a task      |
| GET    | `/tasks/{id}`  | Get one task       |
| PATCH  | `/tasks/{id}`  | Update a task      |
| DELETE | `/tasks/{id}`  | Delete a task      |

## Working with AI (Copilot / Codex)
The `skills/` files are durable instructions for the AI assistant. `.github/
copilot-instructions.md` points Copilot at them so its suggestions respect this
project's architecture, debugging approach, and security rules. See
`docs/` for the PRD and system design the scaffold is aligned to.

## Optional: map the codebase with Graphify
```bash
pip install graphifyy      # note the double 'y'
graphify .                 # writes graph.json, GRAPH_REPORT.md, graph.html to graphify-out/
```
Graphify turns the repo into a knowledge graph so Copilot/Codex can reason about
structure with far fewer tokens. Check the Graphify project README for the current
command, as it evolves.
