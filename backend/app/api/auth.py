import os

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


def _trusted_proxy_count() -> int:
    try:
        return max(int(os.environ.get("AUTH_TRUSTED_PROXY_COUNT", "0")), 0)
    except ValueError:
        return 0


def _client_ip(request: Request) -> str | None:
    # X-Forwarded-For is fully client-controllable, so the leftmost entry must
    # never be trusted. Only honor the hops appended by our own reverse proxies,
    # counting AUTH_TRUSTED_PROXY_COUNT entries from the right. With the default
    # of 0 the header is ignored entirely and the direct peer address is used,
    # which is the safe choice for a directly exposed deployment.
    trusted_proxies = _trusted_proxy_count()
    if trusted_proxies > 0:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            hops = [item.strip() for item in forwarded_for.split(",") if item.strip()]
            if hops:
                index = max(len(hops) - trusted_proxies, 0)
                return hops[index]
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
def register(payload: AuthRequest, request: Request, response: Response):
    service = AuthService()
    account = service.register(email=payload.email, password=payload.password)
    _set_session_cookie(
        response,
        service.create_session_token(
            account,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        ),
    )
    return service.serialize_account(account)


@router.post("/login", response_model=AuthAccountResponse)
def login(payload: AuthRequest, request: Request, response: Response):
    service = AuthService()
    account = service.authenticate(
        email=payload.email,
        password=payload.password,
        ip_address=_client_ip(request),
    )
    _set_session_cookie(
        response,
        service.create_session_token(
            account,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        ),
    )
    return service.serialize_account(account)


@router.post("/logout", response_model=StatusResponse)
def logout(request: Request, response: Response) -> StatusResponse:
    AuthService().revoke_session_token(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    clear_csrf_cookie(response)
    return StatusResponse(status="ok")


@router.post("/logout-all", response_model=StatusResponse)
def logout_all(request: Request, response: Response) -> StatusResponse:
    service = AuthService()
    account_id = service.account_id_from_token(
        request.cookies.get(SESSION_COOKIE_NAME)
    )
    if account_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    service.revoke_account_sessions(account_id)
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
