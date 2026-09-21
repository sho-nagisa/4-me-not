"""Local storage interfaces. No default database or authenticated caller factory."""
from dataclasses import dataclass
from typing import ContextManager, Protocol
from backend.services.memory_contracts import ContractError
from backend.services.source_evidence import _uuid


@dataclass(frozen=True)
class StorageContext:
    """Coordinates, NOT an authentication/approval capability (including when frozen)."""
    vault_id: str
    caller_key: str
    policy_revision: str

    def __post_init__(self):
        _uuid(self.vault_id)
        _uuid(self.policy_revision)
        if not isinstance(self.caller_key, str) or not self.caller_key:
            raise ContractError('INVALID_CALLER_KEY')


def key_id(value):
    return str(_uuid(value))


class Transaction(Protocol):
    """Serializable view; copy reads/writes; unique insert; atomic CAS; rollback on error."""
    def get(self, collection: str, key: tuple): ...
    def insert(self, collection: str, key: tuple, value): ...
    def compare_exchange(self, collection: str, key: tuple, expected, value): ...


class StoragePort(Protocol):
    def transaction(self) -> ContextManager[Transaction]: ...


class AccessPort(Protocol):
    def require(self, tx: Transaction, context: StorageContext, operation: str, target):
        """Recheck authenticated identity, current policy, erasure and use availability.

        target is the exact resource/plan, not caller-asserted authority. Raising aborts.
        Adapter must share the transaction's consistency boundary with current state.
        """
        ...


class UnconnectedAccess:
    def require(self, tx, context, operation, target):
        raise ContractError('AUTHORIZATION_NOT_CONNECTED')
