"""Application entry point.

Creates the FastAPI app, wires middleware, includes routers, and initialises the
database on startup. Run locally with:  uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, projects, tasks
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist before serving requests.
    init_db()
    yield
    # (Shutdown hooks would go here.)


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} is running. See /docs for the API."}
