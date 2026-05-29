from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)


class AuthAccountResponse(BaseModel):
    id: str
    email: str
    is_active: bool
