"""Pydantic schemas — the API's request/response contract for a Task.

`TaskCreate`  -> what a client must send to create a task.
`TaskUpdate`  -> the (all-optional) fields a client may patch.
`TaskRead`    -> what the API returns. `from_attributes` lets it read ORM objects.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class TaskCreate(TaskBase):
    status: TaskStatus = TaskStatus.todo


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
