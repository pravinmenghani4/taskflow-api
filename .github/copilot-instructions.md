# Copilot / Codex instructions for TaskFlow

You are assisting on **TaskFlow**, a FastAPI task-management API. Follow the
project's skill files as your source of truth — read them before generating code:

- **skills/Dev_skill.md** — architecture, layer boundaries, and how to add features.
- **skills/debug_skill.md** — how to reproduce and fix bugs in this stack.
- **skills/Security_skill.md** — secrets, validation, injection, and CORS rules.

## Ground rules
- Preserve the layered structure: model → schema → service → route.
- Python 3.11+ typing (PEP 604 unions), Pydantic v2, SQLAlchemy 2.0 `Mapped[...]`.
- Every route needs a `response_model`; every function is type-annotated.
- New feature = model → schema → service → router → include in `app/main.py`,
  plus tests in `tests/`.
- Never hard-code secrets or build raw SQL strings.
- A change isn't done until `pytest` passes and the app boots.
