from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from backend.services.task_service import TaskService


router = APIRouter(prefix="/tasks", tags=["task"])


class TaskCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    description: str | None = None
    due_at: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    due_at: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None


@router.get("")
def list_tasks(
    include_candidates: bool = True,
    candidate_status: str | None = None,
    status: str | None = None,
    open_only: bool = False,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    service = TaskService()
    return service.list_tasks(
        include_candidates=include_candidates,
        candidate_status=candidate_status,
        status=status,
        open_only=open_only,
        search=search,
        limit=limit,
    )


@router.post("")
def create_task(payload: TaskCreateRequest):
    service = TaskService()
    return service.create_task(
        title=payload.title,
        description=payload.description,
        due_at=payload.due_at,
        priority=payload.priority,
    )


@router.patch("/{task_id}")
def update_task(task_id: str, payload: TaskUpdateRequest):
    service = TaskService()
    changes: dict[str, Any] = payload.model_dump(exclude_unset=True)
    return service.update_task(task_id, changes)


@router.post("/{task_id}/complete")
def complete_task(task_id: str):
    service = TaskService()
    return service.complete_task(task_id)


@router.post("/{task_id}/reopen")
def reopen_task(task_id: str):
    service = TaskService()
    return service.reopen_task(task_id)


@router.post("/{task_id}/accept")
def accept_task_candidate(task_id: str):
    service = TaskService()
    return service.accept_candidate(task_id)


@router.post("/{task_id}/dismiss")
def dismiss_task_candidate(task_id: str):
    service = TaskService()
    return service.dismiss_candidate(task_id)
