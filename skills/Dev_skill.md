# Dev Skill — How to build features in TaskFlow

> This is a **skill file**: durable context you give an AI coding assistant
> (GitHub Copilot / Codex) so its suggestions match this project's conventions.
> Reference it from `.github/copilot-instructions.md` or paste it into Copilot Chat
> before a task.

## Stack
- Python 3.11+, FastAPI, SQLAlchemy 2.0 (typed `Mapped[...]`), Pydantic v2.
- SQLite in dev via `DATABASE_URL`; tests use an in-memory SQLite database.

## Layered architecture — respect these boundaries
1. **models/** — SQLAlchemy ORM classes. How data is *stored*. No HTTP, no Pydantic.
2. **schemas/** — Pydantic models. The API request/response contract. `TaskRead`
   uses `model_config = ConfigDict(from_attributes=True)` to read ORM objects.
3. **services/** — plain functions that take a `Session` + validated schema and do
   the work. All business logic lives here. No FastAPI imports.
4. **api/routes/** — thin routers. Validate via schemas, call a service, return.
5. **core/** — `config.py` (settings) and `database.py` (engine/session). Never read
   `os.environ` outside `config.py`.

## Conventions
- Add a new resource by creating, in order: model → schema → service → route,
  then include the router in `app/main.py`.
- Type every function. Prefer `list[X] | None` style (PEP 604) over `Optional`.
- Return `response_model=...` on every route so the schema shapes the output.
- Use the `get_task_or_404` dependency pattern for "load-or-404" lookups.

## Definition of done
- `pytest` passes, `uvicorn app.main:app` boots, and the new endpoint appears in `/docs`.

### Good Copilot prompt
> "Following Dev_skill.md, add a `Project` resource with title and description:
>  create the ORM model, Pydantic schemas (Create/Update/Read), a service module,
>  and a CRUD router, then include it in main.py."
