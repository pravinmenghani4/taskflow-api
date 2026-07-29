"""Database engine, session factory, and schema initialisation."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# SQLite needs a special flag when used with FastAPI's threadpool.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base class every ORM model inherits from."""


def init_db() -> None:
    """Create all tables. Called on app startup.

    For real projects use Alembic migrations instead of create_all().
    """
    # Import models so they are registered on Base.metadata before create_all.
    from app.models import project  # noqa: F401
    from app.models import task  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
