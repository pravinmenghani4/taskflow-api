"""Business logic for projects.

The service layer sits between the API routes and the database. Routes stay thin
(HTTP concerns only); services own the actual work.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def list_projects(db: Session, skip: int = 0, limit: int = 100) -> list[Project]:
    stmt = select(Project).offset(skip).limit(limit).order_by(Project.id)
    return list(db.scalars(stmt).all())


def get_project(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(
    db: Session, project: Project, payload: ProjectUpdate
) -> Project:
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(project, field, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
