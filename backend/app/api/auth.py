from fastapi import APIRouter, HTTPException, Request, Response

from backend.app.http_security import (
    CSRF_COOKIE_NAME,
    clear_csrf_cookie,
    set_csrf_cookie,
)
from backend.app.security_config import auth_cookie_secure
from backend.app.schemas.auth import AuthAccountResponse, AuthRequest
from backend.app.schemas.common import StatusResponse
from backend.services.auth_service import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    AuthService,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip
    if request.client is not None:
        return request.client.host
    return None


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=auth_cookie_secure(),
        samesite="lax",
        path="/",
    )
    set_csrf_cookie(response)


@router.post("/register", response_model=AuthAccountResponse)
def register(payload: AuthRequest, response: Response):
    service = AuthService()
    account = service.register(email=payload.email, password=payload.password)
    _set_session_cookie(response, service.create_session_token(account))
    return service.serialize_account(account)


@router.post("/login", response_model=AuthAccountResponse)
def login(payload: AuthRequest, request: Request, response: Response):
    service = AuthService()
    account = service.authenticate(
        email=payload.email,
        password=payload.password,
        ip_address=_client_ip(request),
    )
    _set_session_cookie(response, service.create_session_token(account))
    return service.serialize_account(account)


@router.post("/logout", response_model=StatusResponse)
def logout(response: Response) -> StatusResponse:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    clear_csrf_cookie(response)
    return StatusResponse(status="ok")


@router.get("/me", response_model=AuthAccountResponse)
def me(request: Request, response: Response):
    service = AuthService()
    account_id = service.account_id_from_token(
        request.cookies.get(SESSION_COOKIE_NAME)
    )
    if account_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    account = service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    set_csrf_cookie(response, request.cookies.get(CSRF_COOKIE_NAME))
    return service.serialize_account(account)
