"""Agent triage route — thin HTTP wrapper around agent_service."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import agent_service, task_service

router = APIRouter(prefix="/agent", tags=["agent"])


class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class TriageResponse(BaseModel):
    reply: str


@router.post("/triage", response_model=TriageResponse)
def triage(payload: TriageRequest, db: Session = Depends(get_db)):
    """Send a natural-language request to the AI agent.
    The agent sees the current task list and returns planning suggestions.
    """
    tasks = [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "description": t.description,
        }
        for t in task_service.list_tasks(db)
    ]
    try:
        reply = agent_service.triage_tasks(payload.message, tasks)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Agent error: {exc}",
        )
    return TriageResponse(reply=reply)
