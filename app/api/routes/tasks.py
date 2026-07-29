"""Task CRUD routes.

Routes are intentionally thin: they validate input via schemas, delegate to the
service layer, and shape the HTTP response. No business logic lives here.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_task_or_404
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status: TaskStatus | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    return task_service.list_tasks(db, skip=skip, limit=limit, status=status, q=q)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return task_service.create_task(db, payload)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task: Task = Depends(get_task_or_404)):
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    payload: TaskUpdate,
    task: Task = Depends(get_task_or_404),
    db: Session = Depends(get_db),
):
    return task_service.update_task(db, task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task: Task = Depends(get_task_or_404), db: Session = Depends(get_db)
):
    task_service.delete_task(db, task)
