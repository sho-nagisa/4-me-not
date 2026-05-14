import os
from uuid import UUID


DEFAULT_ACCOUNT_ID = UUID(
    os.environ.get("DEFAULT_ACCOUNT_ID", "00000000-0000-0000-0000-000000000001")
)
DEFAULT_ACCOUNT_EMAIL = os.environ.get(
    "DEFAULT_ACCOUNT_EMAIL",
    "debug@example.local",
)


def get_current_account_id() -> UUID:
    return DEFAULT_ACCOUNT_ID
