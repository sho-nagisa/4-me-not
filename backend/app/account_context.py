import os
from contextvars import ContextVar, Token
from uuid import UUID


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


def get_current_account_id() -> UUID:
    return _current_account_id.get() or DEFAULT_ACCOUNT_ID


def get_authenticated_account_id() -> UUID | None:
    return _current_account_id.get()


def set_current_account_id(account_id: UUID) -> Token[UUID | None]:
    return _current_account_id.set(account_id)


def reset_current_account_id(token: Token[UUID | None]) -> None:
    _current_account_id.reset(token)
