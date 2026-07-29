# Security Skill — Guardrails for TaskFlow

> Security context for the AI assistant. Apply these rules to every suggestion;
> flag any generated code that violates them.

## Secrets & config
- Never hard-code secrets. All config comes from environment via `app/core/config.py`.
- `.env` is git-ignored; only `.env.example` (no real values) is committed.
- Never log secrets, tokens, or full request bodies that may contain them.

## Input handling
- Validate all input with Pydantic schemas; never trust client data.
- Use SQLAlchemy's query API / bound parameters (as in `task_service.py`).
  Never build SQL with f-strings or string concatenation.
- Set sensible bounds (`max_length`, pagination `limit`) to avoid abuse.

## API surface
- Lock down CORS to known origins via `CORS_ORIGINS` — never `*` in production.
- Return generic error messages to clients; keep stack traces server-side.
- Add authentication (e.g. OAuth2 / API keys) before any non-demo deployment;
  the demo intentionally ships without auth — note this in the PRD.

## Dependencies
- Pin versions in `requirements.txt`; review before upgrading.
- Periodically run `pip-audit` (or `uv pip audit`) to catch known CVEs.

## Good Copilot prompt
> "Review this new endpoint against Security_skill.md. List any hard-coded secrets,
>  injection risks, missing validation, or over-broad CORS, and show fixes."
