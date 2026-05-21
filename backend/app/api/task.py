from fastapi import APIRouter, Query

from backend.services.task_service import TaskService


router = APIRouter(prefix="/tasks", tags=["task"])


@router.get("")
def list_tasks(
    include_candidates: bool = True,
    candidate_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    service = TaskService()
    return service.list_tasks(
        include_candidates=include_candidates,
        candidate_status=candidate_status,
        limit=limit,
    )


@router.post("/{task_id}/accept")
def accept_task_candidate(task_id: str):
    service = TaskService()
    return service.accept_candidate(task_id)


@router.post("/{task_id}/dismiss")
def dismiss_task_candidate(task_id: str):
    service = TaskService()
    return service.dismiss_candidate(task_id)
