# TaskFlow — System Design (one page)

## Component diagram
```
Client (curl / Swagger UI / frontend)
        │  HTTP + JSON
        ▼
┌─────────────────────────────────────────────┐
│ FastAPI app  (app/main.py)                   │
│                                              │
│  api/routes  ──▶  services  ──▶  models      │
│    (HTTP)         (logic)        (ORM)       │
│      ▲                              │        │
│   schemas (validation)          database     │
│                                  (SQLite)    │
│  core/config  ◀── .env                       │
└─────────────────────────────────────────────┘
```

## Layer responsibilities
| Layer        | Directory          | Responsibility                          |
|--------------|--------------------|-----------------------------------------|
| Routing      | `app/api/routes`   | HTTP verbs, status codes, dependencies  |
| Validation   | `app/schemas`      | Request/response contract (Pydantic)    |
| Logic        | `app/services`     | Business rules, DB reads/writes         |
| Persistence  | `app/models`       | ORM tables (SQLAlchemy)                 |
| Platform     | `app/core`         | Config + DB engine/session             |

## Request lifecycle (create a task)
1. `POST /tasks` hits `routes/tasks.py`.
2. Body is validated into a `TaskCreate` schema.
3. Route calls `task_service.create_task(db, payload)`.
4. Service builds a `Task` ORM row, commits, refreshes.
5. Route returns it as a `TaskRead` (schema shapes the JSON).

## Scaffold ↔ design mapping
Every box above maps to exactly one folder. When AI generates code, each new
file must land in the folder that owns that responsibility — this is what
"aligning the scaffold with the design" means in practice.
