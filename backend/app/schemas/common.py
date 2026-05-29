from pydantic import BaseModel


class IdResponse(BaseModel):
    id: str


class StatusResponse(BaseModel):
    status: str
