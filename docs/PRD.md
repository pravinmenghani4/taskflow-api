# TaskFlow — Product Requirements Document (mini)

## 1. Problem
Small teams need a lightweight way to track work items without a heavy tool.

## 2. Goal
A REST API to create, read, update, and delete tasks, each with a status
(`todo` → `in_progress` → `done`).

## 3. In scope (v0.1)
- CRUD for tasks (title, description, status).
- Input validation and consistent error responses.
- Health-check endpoint for monitoring.
- Auto-generated OpenAPI docs at `/docs`.

## 4. Out of scope (v0.1)
- Authentication / user accounts (single-tenant demo).
- Projects, comments, attachments, due dates.
- A frontend UI.

## 5. Non-functional
- Runs locally with one command; SQLite by default, Postgres-ready via env.
- Automated tests cover every endpoint.
- Secrets only via environment variables.

## 6. Data model
`Task`: id, title (required, ≤200), description (optional, ≤2000),
status (enum), created_at, updated_at.

## 7. Traceability — PRD → code
| Requirement           | Where it lives                          |
|-----------------------|-----------------------------------------|
| Task data model       | `app/models/task.py`                    |
| Request/response shape | `app/schemas/task.py`                   |
| CRUD behaviour        | `app/services/task_service.py`          |
| HTTP endpoints        | `app/api/routes/tasks.py`               |
| Health check          | `app/api/routes/health.py`              |
| Config via env        | `app/core/config.py` + `.env.example`   |
| Tests                 | `tests/test_tasks.py`                   |
