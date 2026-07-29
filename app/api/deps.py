"""Shared API dependencies.

Re-exports the DB session dependency so routes import it from one place, and
provides a reusable `get_task_or_404` dependency that loads a task by id and
raises 404 if it does not exist.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.models.project import Project
from app.models.task import Task
from app.services import project_service
from app.services import task_service


def get_db(session: Session = Depends(get_session)) -> Session:
    return session


def get_task_or_404(task_id: int, db: Session = Depends(get_db)) -> Task:
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


def get_project_or_404(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project
