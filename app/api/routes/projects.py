"""Project CRUD routes.

Routes are intentionally thin: they validate input via schemas, delegate to the
service layer, and shape the HTTP response.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_project_or_404
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return project_service.list_projects(db, skip=skip, limit=limit)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return project_service.create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project: Project = Depends(get_project_or_404)):
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    payload: ProjectUpdate,
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
):
    return project_service.update_project(db, project, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project: Project = Depends(get_project_or_404),
    db: Session = Depends(get_db),
):
    project_service.delete_project(db, project)
