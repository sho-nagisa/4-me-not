from pydantic import BaseModel, Field


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
