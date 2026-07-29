# Debug Skill — How to diagnose issues in TaskFlow

> Give this to Copilot/Codex when something breaks so it debugs the way this
> project expects, instead of guessing.

## First moves
1. Reproduce with a test. Add a failing case in `tests/` before changing code —
   it pins the bug and proves the fix.
2. Read the traceback bottom-up: the last frame in *our* code is usually the cause.
3. Run a focused test: `pytest tests/test_tasks.py::test_update_task -x -q`.

## Common issues in this stack
- **`table not found` / empty DB** — `init_db()` didn't run, or a model wasn't
  imported before `create_all`. Check `app/core/database.py::init_db`.
- **422 Unprocessable Entity** — the request body failed schema validation. Read
  the JSON `detail`; the schema in `app/schemas/` is the source of truth.
- **500 on serialization** — returning an ORM object without `from_attributes`
  on the response schema, or a type mismatch between model and schema.
- **SQLite threading error** — missing `check_same_thread=False` (already set in
  `database.py`; don't remove it).
- **Stale settings** — `get_settings()` is `@lru_cache`d; restart the server after
  editing `.env`.

## Good Copilot prompt
> "This endpoint returns 500. Here's the traceback and the route + service code.
>  Following debug_skill.md, add a failing test that reproduces it, find the root
>  cause, and propose the minimal fix."
