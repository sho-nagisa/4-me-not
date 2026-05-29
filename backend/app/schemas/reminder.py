from pydantic import BaseModel


class ReminderCreateRequest(BaseModel):
    title: str
    remind_at: str
    message: str | None = None
