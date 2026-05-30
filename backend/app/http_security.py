import hmac
import os
import secrets

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from backend.app.security_config import auth_cookie_secure, is_dev_environment
from backend.services.auth_service import SESSION_COOKIE_NAME, SESSION_TTL_SECONDS


CSRF_COOKIE_NAME = "forme_not_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_CSRF_EXEMPT_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
}


def csrf_protection_enabled() -> bool:
    if not is_dev_environment():
        return True
    return os.environ.get("AUTH_CSRF_PROTECTION", "").strip().lower() == "true"


def create_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str | None = None) -> str:
    csrf_token = token or create_csrf_token()
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=False,
        secure=auth_cookie_secure(),
        samesite="lax",
        path="/",
    )
    return csrf_token


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


def validate_csrf_request(request: Request) -> JSONResponse | None:
    if not _csrf_required(request):
        return None

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if (
        not cookie_token
        or not header_token
        or not hmac.compare_digest(cookie_token, header_token)
    ):
        return JSONResponse(
            {"detail": "CSRF token is missing or invalid"},
            status_code=403,
        )
    return None


def add_security_headers(response: Response, *, include_csp: bool = True) -> None:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    if include_csp:
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self'",
        )
    if not is_dev_environment():
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains",
        )


def _csrf_required(request: Request) -> bool:
    if not csrf_protection_enabled():
        return False
    if request.method.upper() not in _UNSAFE_METHODS:
        return False
    if request.url.path in _CSRF_EXEMPT_PATHS:
        return False
    if not request.url.path.startswith("/api/"):
        return False
    return request.cookies.get(SESSION_COOKIE_NAME) is not None
