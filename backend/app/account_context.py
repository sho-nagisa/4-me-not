import os
from contextvars import ContextVar, Token
from uuid import UUID

from fastapi import HTTPException

from backend.app.security_config import is_dev_environment


DEFAULT_ACCOUNT_ID = UUID(
    os.environ.get("DEFAULT_ACCOUNT_ID", "00000000-0000-0000-0000-000000000001")
)
DEFAULT_ACCOUNT_EMAIL = os.environ.get(
    "DEFAULT_ACCOUNT_EMAIL",
    "debug@example.local",
)

_current_account_id: ContextVar[UUID | None] = ContextVar(
    "current_account_id",
    default=None,
)


def dev_fallback_enabled() -> bool:
    return is_dev_environment()


def _resolve_account_id() -> UUID | None:
    account_id = _current_account_id.get()
    if account_id is not None:
        return account_id
    if dev_fallback_enabled():
        return DEFAULT_ACCOUNT_ID
    return None


def get_authenticated_account_id() -> UUID:
    account_id = _resolve_account_id()
    if account_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return account_id


def get_current_account_id() -> UUID:
    account_id = _resolve_account_id()
    if account_id is None:
        # Reached only if a request bypassed get_authenticated_account_id, or a
        # script ran outside dev. The DEFAULT_ACCOUNT_ID fallback is dev-only.
        raise RuntimeError(
            "No account in context. Protect the route with the "
            "get_authenticated_account_id dependency, or set APP_ENV=dev for "
            "local scripts."
        )
    return account_id


def set_current_account_id(account_id: UUID) -> Token[UUID | None]:
    return _current_account_id.set(account_id)


def reset_current_account_id(token: Token[UUID | None]) -> None:
    _current_account_id.reset(token)
