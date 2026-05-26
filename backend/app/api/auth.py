import os

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.services.auth_service import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    AuthService,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=128)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=os.environ.get("AUTH_COOKIE_SECURE", "").lower() == "true",
        samesite="lax",
        path="/",
    )


@router.post("/register")
def register(payload: AuthRequest, response: Response):
    service = AuthService()
    account = service.register(email=payload.email, password=payload.password)
    _set_session_cookie(response, service.create_session_token(account))
    return service.serialize_account(account)


@router.post("/login")
def login(payload: AuthRequest, response: Response):
    service = AuthService()
    account = service.authenticate(email=payload.email, password=payload.password)
    _set_session_cookie(response, service.create_session_token(account))
    return service.serialize_account(account)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(request: Request):
    service = AuthService()
    account_id = service.account_id_from_token(
        request.cookies.get(SESSION_COOKIE_NAME)
    )
    if account_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    account = service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return service.serialize_account(account)
