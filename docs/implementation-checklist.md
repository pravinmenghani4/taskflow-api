# TaskFlow — Developer Implementation Checklist

> Generated: 2026-08-20  
> Based on: `docs/PRD.md`, `docs/system-design.md`, and full codebase audit.  
> Modules are ordered by dependency — each module only assumes the ones above it
> are complete. Work top-to-bottom.

---

## Legend

- 🔑 **Secret / env var required** — do not hard-code; add to `.env.example` first.
- 🌐 **Third-party account required** — note the provider.
- ✅ **Already implemented** — confirmed in the current codebase.

---

## Module 0 — Platform Foundation

> Thinnest vertical slice: config, database, app boot. Everything else builds on this.

- [x] **0.1 Settings object** ✅  
  _Files:_ `app/core/config.py`, `.env.example`  
  _Done when:_ `settings.database_url`, `settings.app_name`, `settings.environment`,
  and `settings.cors_origins` load cleanly from env; `get_settings()` is cached with
  `@lru_cache`; no `os.environ` reads outside this file.  
  🔑 `DATABASE_URL`, `APP_NAME`, `ENVIRONMENT`, `CORS_ORIGINS`

- [x] **0.2 Database engine & session factory** ✅  
  _Files:_ `app/core/database.py`  
  _Done when:_ `create_engine` is called once at import time; `get_session` is a
  proper generator dependency; SQLite `check_same_thread=False` flag is guarded by
  a `startswith("sqlite")` check; `init_db()` runs `Base.metadata.create_all` on
  startup.

- [x] **0.3 FastAPI app wiring** ✅  
  _Files:_ `app/main.py`  
  _Done when:_ App boots via `uvicorn app.main:app --reload`; `CORSMiddleware` is
  wired with `cors_origin_list`; `init_db()` fires in the `lifespan` context;
  `/docs` and `/openapi.json` are accessible.

- [x] **0.4 Health-check endpoint** ✅  
  _Files:_ `app/api/routes/health.py`  
  _Done when:_ `GET /health` returns `{"status": "ok", "app": "...", "env": "..."}`
  with HTTP 200.

- [x] **0.5 Test harness** ✅  
  _Files:_ `tests/conftest.py`  
  _Done when:_ `pytest -q` runs; the `client` fixture spins up an isolated
  in-memory SQLite database and overrides `get_session`; no test touches
  `taskflow.db`.

---

## Module 1 — Database Layer (Alembic Migrations)

> The current scaffold uses `create_all` which is fine for demos but unsafe for
> production. This module introduces proper schema migration.

- [ ] **1.1 Install and initialise Alembic**  
  _Files:_ `requirements.txt`, `alembic.ini`, `alembic/env.py`  
  _Done when:_ `alembic upgrade head` runs cleanly against a fresh database;
  `alembic history` shows at least one revision.  
  _Steps:_
  1. `pip install alembic==1.13.*` — pin the version.
  2. `alembic init alembic` at the repo root.
  3. Edit `alembic/env.py`: set `target_metadata = Base.metadata` and load
     `DATABASE_URL` from `settings`.
  4. Generate the initial migration: `alembic revision --autogenerate -m "initial"`.

- [ ] **1.2 Replace `create_all` with Alembic in startup**  
  _Files:_ `app/core/database.py`, `app/main.py`  
  _Done when:_ `init_db()` is either removed or calls `alembic upgrade head`
  programmatically; `Base.metadata.create_all` is no longer invoked at runtime.  
  ⚠️ Update `tests/conftest.py` — tests must still use `create_all` against the
  in-memory engine (Alembic targets only real DBs).

- [ ] **1.3 Postgres readiness**  
  _Files:_ `app/core/config.py`, `requirements.txt`, `.env.example`  
  _Done when:_ Swapping `DATABASE_URL` to a `postgresql+psycopg2://...` string boots
  the app without code changes; `psycopg2-binary` (or `asyncpg`) is in
  `requirements.txt`.  
  🔑 `DATABASE_URL` (Postgres DSN for staging/prod)

---

## Module 2 — Authentication & Users

> Auth is listed as out-of-scope in PRD v0.1 but is the prerequisite for multi-tenant
> Boards, Razorpay, and any production deployment. Implement before those modules.

- [ ] **2.1 User ORM model**  
  _Files:_ `app/models/user.py`, `alembic/versions/<rev>_add_users.py`  
  _Done when:_ `users` table exists with columns `id`, `email` (unique, indexed),
  `hashed_password`, `is_active` (bool, default True), `created_at`, `updated_at`;
  `alembic upgrade head` applies the migration cleanly.

- [ ] **2.2 User Pydantic schemas**  
  _Files:_ `app/schemas/user.py`  
  _Done when:_ `UserCreate` (email + password, password ≥ 8 chars), `UserRead` (no
  password field), `UserInDB` (with `hashed_password`) are defined and have
  `model_config = ConfigDict(from_attributes=True)` on the Read schema.

- [ ] **2.3 Password hashing utility**  
  _Files:_ `app/core/security.py`, `requirements.txt`  
  _Done when:_ `hash_password(plain: str) -> str` and `verify_password(plain, hashed) -> bool`
  use `passlib` with the `bcrypt` scheme; the plain password is never stored or logged.  
  🔑 No new env var — but `SECRET_KEY` is needed in 2.5.

- [ ] **2.4 User service**  
  _Files:_ `app/services/user_service.py`  
  _Done when:_ `create_user`, `get_user_by_email`, `get_user` functions exist;
  `create_user` hashes the password before persisting; duplicate-email raises a
  descriptive `HTTPException(409)`.

- [ ] **2.5 JWT token helpers**  
  _Files:_ `app/core/security.py`, `app/core/config.py`, `.env.example`  
  _Done when:_ `create_access_token(subject: str, expires_delta: timedelta) -> str`
  and `decode_access_token(token: str) -> dict` use `python-jose[cryptography]`;
  expiry and key are read from settings, never hard-coded.  
  🔑 `SECRET_KEY` (random 32-byte hex), `ACCESS_TOKEN_EXPIRE_MINUTES`

- [ ] **2.6 Auth routes — register & login**  
  _Files:_ `app/api/routes/auth.py`, `app/main.py`  
  _Done when:_ `POST /auth/register` creates a user and returns `UserRead`;
  `POST /auth/token` accepts `OAuth2PasswordRequestForm`, validates credentials,
  returns `{"access_token": "...", "token_type": "bearer"}`; both endpoints appear
  in `/docs`.

- [ ] **2.7 `get_current_user` dependency**  
  _Files:_ `app/api/deps.py`  
  _Done when:_ `get_current_user` extracts and validates the Bearer token;
  unauthenticated requests receive HTTP 401; downstream dependencies like
  `get_db` remain unaffected for public routes.

- [ ] **2.8 Auth tests**  
  _Files:_ `tests/test_auth.py`  
  _Done when:_ Tests cover: register → login → access protected endpoint with
  valid token; login with wrong password returns 401; protected endpoint without
  token returns 401; duplicate registration returns 409.

---

## Module 3 — Boards & Tasks (Multi-tenant Core)

> The existing `tasks` and `projects` endpoints are single-tenant (no owner).
> This module scopes them to authenticated users and adds the Board/Column concepts.

- [ ] **3.1 Link `Project` to `User` (owner FK)**  
  _Files:_ `app/models/project.py`, `alembic/versions/<rev>_project_owner.py`  
  _Done when:_ `projects.owner_id` FK → `users.id` exists in the migration;
  `project_service.create_project` accepts the current user's id;
  `list_projects` filters by `owner_id`.

- [ ] **3.2 Link `Task` to `Project`**  
  _Files:_ `app/models/task.py`, `alembic/versions/<rev>_task_project_fk.py`  
  _Done when:_ `tasks.project_id` FK → `projects.id` exists; all task service
  queries join through the project ownership chain so users can only read/mutate
  their own tasks.

- [ ] **3.3 `Board` ORM model**  
  _Files:_ `app/models/board.py`, `alembic/versions/<rev>_add_boards.py`  
  _Done when:_ `boards` table has `id`, `title` (≤200), `project_id` FK,
  `created_at`, `updated_at`; migration applies cleanly.

- [ ] **3.4 `Column` ORM model**  
  _Files:_ `app/models/column.py`, `alembic/versions/<rev>_add_columns.py`  
  _Done when:_ `columns` table has `id`, `title` (≤100), `position` (int, for
  ordering), `board_id` FK, `created_at`, `updated_at`.

- [ ] **3.5 Boards & Columns schemas + service + routes**  
  _Files:_ `app/schemas/board.py`, `app/schemas/column.py`,
  `app/services/board_service.py`, `app/api/routes/boards.py`  
  _Done when:_ Full CRUD for boards (`/projects/{project_id}/boards`) and columns
  (`/boards/{board_id}/columns`) is reachable; all routes require authentication;
  wrong-owner access returns 403.

- [ ] **3.6 Move `Task` onto a Column**  
  _Files:_ `app/models/task.py`, `app/schemas/task.py`, `app/services/task_service.py`  
  _Done when:_ `tasks.column_id` FK → `columns.id` is nullable (tasks may be
  unassigned); `TaskUpdate` includes `column_id`; `PATCH /tasks/{id}` can move
  a task between columns.

- [ ] **3.7 Task ordering within a column**  
  _Files:_ `app/models/task.py`, `app/services/task_service.py`  
  _Done when:_ `tasks.position` (int) exists; `list_tasks` for a column returns
  tasks ordered by `position`; `PATCH /tasks/{id}/reorder` accepts a `position`
  and shifts siblings atomically.

- [ ] **3.8 Boards & Tasks tests**  
  _Files:_ `tests/test_boards.py`, `tests/test_tasks.py` (extend)  
  _Done when:_ Tests cover: create board inside a project; CRUD on columns; move
  task to column; reorder tasks; cross-user access returns 403.

---

## Module 4 — Razorpay Integration

> Payments are a separate vertical. Auth (Module 2) must be complete before this.

> 🌐 **Requires a Razorpay account** — sign up at https://razorpay.com and create
> Test Mode API keys before starting any task in this module.

- [ ] **4.1 Install Razorpay SDK**  
  _Files:_ `requirements.txt`  
  _Done when:_ `razorpay==1.4.*` (or latest stable) is pinned in `requirements.txt`
  and `import razorpay` succeeds in the venv.  
  🔑 No secrets yet — keys come in 4.2.

- [ ] **4.2 Razorpay config**  
  _Files:_ `app/core/config.py`, `.env.example`  
  _Done when:_ `Settings` exposes `razorpay_key_id: str` and
  `razorpay_key_secret: str`; both default to empty string so the app doesn't
  crash when Razorpay is disabled; neither value appears in any committed file.  
  🔑 `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`  
  🌐 Razorpay Test Mode dashboard → Settings → API Keys

- [ ] **4.3 `Plan` and `Subscription` ORM models**  
  _Files:_ `app/models/plan.py`, `app/models/subscription.py`,
  `alembic/versions/<rev>_add_billing.py`  
  _Done when:_ `plans` table (`id`, `name`, `razorpay_plan_id`, `amount_paise`,
  `interval`); `subscriptions` table (`id`, `user_id` FK, `razorpay_subscription_id`,
  `status`, `current_period_end`); migration is clean.

- [ ] **4.4 Razorpay client singleton**  
  _Files:_ `app/core/razorpay_client.py`  
  _Done when:_ A lazily-instantiated `razorpay.Client` is returned by
  `get_razorpay_client()`; it reads key/secret from `settings`; calling the
  function when keys are empty raises a clear `RuntimeError` (not a cryptic SDK
  error).

- [ ] **4.5 Subscription service**  
  _Files:_ `app/services/subscription_service.py`  
  _Done when:_ `create_order(user, plan_id)` creates a Razorpay order and
  persists a pending local subscription; `verify_payment(payment_id, order_id,
  signature)` validates the HMAC signature using `razorpay_key_secret` before
  activating the subscription.  
  ⚠️ Never skip signature verification — it is the only server-side proof of payment.

- [ ] **4.6 Billing routes**  
  _Files:_ `app/api/routes/billing.py`, `app/main.py`  
  _Done when:_ `POST /billing/orders` (create Razorpay order, requires auth);
  `POST /billing/verify` (verify payment signature, activates subscription);
  `GET /billing/subscription` (current subscription status); all require auth.

- [ ] **4.7 Razorpay webhook handler**  
  _Files:_ `app/api/routes/billing.py`  
  _Done when:_ `POST /billing/webhook` validates the `X-Razorpay-Signature` header
  using HMAC-SHA256 before processing any event; handles `subscription.activated`,
  `subscription.cancelled`, `payment.failed`; returns HTTP 200 immediately
  (process asynchronously if needed).  
  🔑 `RAZORPAY_WEBHOOK_SECRET` (set in Razorpay dashboard → Webhooks)  
  🌐 Razorpay dashboard → Webhooks → Add new webhook (point to `/billing/webhook`)

- [ ] **4.8 Billing tests (Test Mode)**  
  _Files:_ `tests/test_billing.py`  
  _Done when:_ Tests mock the Razorpay SDK (`unittest.mock.patch`); cover: order
  creation, valid signature verification, invalid signature returns 400, webhook
  with bad secret returns 400; no real Razorpay calls are made during `pytest`.

---

## Module 5 — Analytics & Monitoring

> Observability layer. Depends only on Module 0 (platform). Can be developed in
> parallel with Modules 2–4.

- [ ] **5.1 Structured JSON logging**  
  _Files:_ `app/core/logging.py`, `app/main.py`  
  _Done when:_ Every request logs `method`, `path`, `status_code`, `duration_ms`
  as JSON; the logger reads `LOG_LEVEL` from settings; no secrets or request bodies
  are logged.  
  🔑 `LOG_LEVEL` (default `"INFO"`)

- [ ] **5.2 Prometheus metrics endpoint**  
  _Files:_ `app/main.py`, `requirements.txt`  
  _Done when:_ `GET /metrics` returns Prometheus text format; at minimum exposes
  `http_requests_total` (labelled by method, path, status) and
  `http_request_duration_seconds` histogram; `prometheus-client` is pinned in
  `requirements.txt`.

- [ ] **5.3 Sentry error tracking**  
  _Files:_ `app/main.py`, `app/core/config.py`, `requirements.txt`, `.env.example`  
  _Done when:_ `sentry-sdk[fastapi]` is initialised in `lifespan` using `SENTRY_DSN`
  from settings; unhandled exceptions are captured automatically; the DSN is never
  committed.  
  🔑 `SENTRY_DSN`  
  🌐 Sentry account (https://sentry.io) → New Project → Python / FastAPI

- [ ] **5.4 Health-check enrichment**  
  _Files:_ `app/api/routes/health.py`  
  _Done when:_ `GET /health` additionally returns `{"db": "ok"|"error"}` by
  running a cheap `SELECT 1` against the database; a DB outage causes `"db":
  "error"` (not a 500); HTTP status remains 200 so load balancers don't flip the
  instance.

- [ ] **5.5 Analytics event table (optional lightweight alternative)**  
  _Files:_ `app/models/event.py`, `app/services/analytics_service.py`,
  `alembic/versions/<rev>_add_events.py`  
  _Done when:_ `events` table (`id`, `user_id` FK nullable, `event_type`,
  `payload` JSON, `created_at`) is migrated; `record_event(db, type, payload)`
  is called from task/board service on create/update/delete; no PII is stored in
  `payload`.

- [ ] **5.6 Monitoring tests**  
  _Files:_ `tests/test_health.py`, `tests/test_metrics.py`  
  _Done when:_ `GET /health` returns 200 with `{"status": "ok", "db": "ok"}`;
  `GET /metrics` returns 200 and contains `http_requests_total`; Sentry init is
  patched so tests don't call the Sentry API.

---

## Cross-cutting / Non-functional

- [ ] **X.1 Pin all dependencies**  
  _Files:_ `requirements.txt`  
  _Done when:_ Every package has an exact version pinned (`==`); a `pip-audit`
  run reports no known CVEs.

- [ ] **X.2 `.env.example` kept in sync**  
  _Files:_ `.env.example`  
  _Done when:_ Every env var flagged 🔑 in this checklist has a placeholder entry
  in `.env.example` (e.g., `SECRET_KEY=changeme`); `.env` is in `.gitignore` and
  never committed.

- [ ] **X.3 CORS locked to known origins**  
  _Files:_ `app/core/config.py`, `.env.example`  
  _Done when:_ `CORS_ORIGINS` in production is set to the actual frontend domain(s)
  and never `*`; the `cors_origin_list` property strips whitespace around commas.  
  🔑 `CORS_ORIGINS`

- [ ] **X.4 Global exception handler**  
  _Files:_ `app/main.py`  
  _Done when:_ An `@app.exception_handler(Exception)` returns a JSON body
  `{"detail": "Internal server error"}` with HTTP 500 for all unhandled exceptions;
  the full traceback is written to the server log, not to the HTTP response.

- [ ] **X.5 `pip-audit` in CI**  
  _Files:_ `.github/workflows/ci.yml` (create if absent)  
  _Done when:_ A GitHub Actions workflow runs `pytest -q` and `pip-audit` on every
  push to `main`; the workflow fails if either check fails.

---

## Environment Variables — Master Reference

| Variable | Module | Required in Prod | Notes |
|---|---|---|---|
| `DATABASE_URL` | 0, 1 | ✅ | Postgres DSN in prod; SQLite path in dev |
| `APP_NAME` | 0 | optional | Display name; defaults to `"TaskFlow API"` |
| `ENVIRONMENT` | 0 | ✅ | `development` / `staging` / `production` |
| `CORS_ORIGINS` | 0 | ✅ | Comma-separated list of allowed origins |
| `LOG_LEVEL` | 5 | optional | `INFO` default; `DEBUG` for dev |
| `SECRET_KEY` | 2 | ✅ | JWT signing key — generate with `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 2 | optional | Defaults to `30` |
| `RAZORPAY_KEY_ID` | 4 | ✅ (billing) | From Razorpay dashboard → API Keys |
| `RAZORPAY_KEY_SECRET` | 4 | ✅ (billing) | From Razorpay dashboard → API Keys |
| `RAZORPAY_WEBHOOK_SECRET` | 4 | ✅ (billing) | From Razorpay dashboard → Webhooks |
| `SENTRY_DSN` | 5 | optional | From Sentry project settings |

---

## Third-party Accounts Required

| Provider | Module | Purpose | Sign-up URL |
|---|---|---|---|
| 🌐 Razorpay | 4 | Payment processing (orders, subscriptions, webhooks) | https://razorpay.com |
| 🌐 Sentry | 5 | Error and performance monitoring | https://sentry.io |
