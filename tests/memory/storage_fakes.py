"""Test-only storage/access fakes. Never imported by application code."""
import copy
from contextlib import contextmanager
from threading import RLock
from backend.services.memory_contracts import ContractError
from backend.services.memory_storage import key_id


class FakeTransaction:
    def __init__(self, store, data):
        self.store, self.data = store, data

    def get(self, collection, key):
        return copy.deepcopy(self.data.get(collection, {}).get(key))

    def insert(self, collection, key, value):
        rows = self.data.setdefault(collection, {})
        if key in rows:
            raise ContractError('DUPLICATE_RECORD')
        rows[key] = copy.deepcopy(value)
        self.store.checkpoint('insert:' + collection)

    def compare_exchange(self, collection, key, expected, value):
        rows = self.data.setdefault(collection, {})
        if rows.get(key) != expected:
            raise ContractError('CAS_CONFLICT')
        rows[key] = copy.deepcopy(value)
        self.store.checkpoint('cas:' + collection)


class FakeStorage:
    """Copy-on-write rollback and serializable threads, NOT durable DB storage."""
    def __init__(self):
        self.data = {}
        self.fail_at = None
        self.lock = RLock()

    def checkpoint(self, name):
        if self.fail_at == name:
            raise ContractError('INJECTED_STORAGE_FAILURE')

    @contextmanager
    def transaction(self):
        with self.lock:
            working = copy.deepcopy(self.data)
            yield FakeTransaction(self, working)
            self.checkpoint('commit')
            self.data = working


class FakeAccess:
    """Test oracle for a current-state port, NOT real authentication or a Gate."""
    def __init__(self):
        self.denied = set()
        self.erased_sources = set()
        self.erased_items = set()
        self.calls = []

    def require(self, tx, context, operation, target):
        self.calls.append(operation)
        if operation in self.denied:
            raise ContractError('NOT_FOUND')
        vault = key_id(context.vault_id)
        if isinstance(target, dict):
            if target.get('source_id') and (vault,key_id(target['source_id'])) in self.erased_sources:
                raise ContractError('NOT_FOUND')
            if target.get('item_id') and (vault,key_id(target['item_id'])) in self.erased_items:
                raise ContractError('NOT_FOUND')
