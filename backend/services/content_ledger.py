"""Local Content Ledger coordinator. No Git, HTTP approval, or live database."""
import copy
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4
from backend.services.memory_contracts import ContractError
from backend.services.memory_storage import UnconnectedAccess, key_id
from backend.services.source_storage import canonical_bytes


class InvalidationPort(Protocol):
    def apply(self, tx, context, revision) -> tuple[str, ...]:
        """W31-07 participant: stage current-use barrier in this same transaction.

        Return affected derived revision IDs. No independently committed work here.
        """
        ...


class UnconnectedInvalidation:
    def apply(self, tx, context, revision):
        raise ContractError('INVALIDATION_NOT_CONNECTED')


class ContentLedger:
    def __init__(self, contracts, storage, revisions, *, access=None, invalidation=None,
                 new_id=uuid4, now=lambda: datetime.now(timezone.utc).isoformat()):
        self.contracts, self.storage, self.revisions = contracts, storage, revisions
        if revisions.storage is not storage:
            raise ContractError('TRANSACTION_PORT_MISMATCH')
        self.access = access if access is not None else UnconnectedAccess()
        self.invalidation = invalidation if invalidation is not None else UnconnectedInvalidation()
        self.new_id, self.now = new_id, now

    def initialize(self, context, snapshot):
        """Internal bootstrap only. Full coordinates must be supplied by trusted storage."""
        value = self.contracts.validate('Snapshot', snapshot)
        vault, head = key_id(context.vault_id), key_id(value['content_head'])
        with self.storage.transaction() as tx:
            self.access.require(tx, context, 'initializeContentLedger', copy.deepcopy(value))
            tx.insert('content_commits', (vault,head), {'kind':'genesis','commit_id':value['content_head'],
                'parent_head':None,'vault_id':context.vault_id,'item_id':None,'revision_id':None,
                'snapshot':value,'receipt':None})
            tx.insert('content_snapshots', (vault,), value)

    def _snapshot_in(self, tx, context):
        vault = key_id(context.vault_id)
        self.access.require(tx, context, 'readContentSnapshot', {'vault_id':vault})
        value = tx.get('content_snapshots', (vault,))
        if value is None:
            raise ContractError('LEDGER_NOT_INITIALIZED')
        value = self.contracts.validate('Snapshot', value)
        head = tx.get('content_commits', (vault,key_id(value['content_head'])))
        if head is None or key_id(head['commit_id']) != key_id(value['content_head']) or key_id(head['vault_id']) != vault:
            raise ContractError('INVALID_COMMIT_PARENT')
        return value

    def commit(self, context, idempotency_key, revision, *, expected_head, expected_current):
        """Internal pre-authorized commit, NOT approveChange/confirmation implementation."""
        value = self.contracts.validate('MemoryRevision', revision)
        key_id(expected_head)
        if not isinstance(idempotency_key,str) or not idempotency_key:
            raise ContractError('INVALID_IDEMPOTENCY_KEY')
        plan = {'revision':value,'expected_head':expected_head,'expected_current':expected_current}
        canonical = canonical_bytes(plan)
        vault = key_id(context.vault_id)
        key = (vault,context.caller_key,'contentCommit',idempotency_key)
        with self.storage.transaction() as tx:
            self.access.require(tx, context, 'commitContent', copy.deepcopy(plan))
            previous = tx.get('content_receipts', key)
            if previous is not None:
                if previous['canonical_plan'] != canonical:
                    raise ContractError('IDEMPOTENCY_CONFLICT')
                receipt = previous['receipt']
                self.revisions.read_in(tx,context,receipt['item_id'],receipt['revision_id'])
                self.access.require(tx, context, 'readContentCommit', copy.deepcopy(receipt))
            else:
                snapshot = self._snapshot_in(tx,context)
                if key_id(snapshot['content_head']) != key_id(expected_head):
                    raise ContractError('HEAD_CONFLICT')
                commit_id = str(self.new_id())
                key_id(commit_id)
                if key_id(commit_id) == key_id(expected_head):
                    raise ContractError('INVALID_COMMIT_PARENT')
                # Internal revision/current writes join the enclosing ledger transaction.
                saved = self.revisions.project_in(tx,context,value,
                    expected_current=expected_current,basis_head=commit_id)
                stale = self.invalidation.apply(tx,context,copy.deepcopy(saved))
                if not isinstance(stale,tuple) or any(not isinstance(i,str) for i in stale):
                    raise ContractError('INVALID_INVALIDATION_RESULT')
                receipt = self.contracts.validate('CommitReceipt', {'commit_id':commit_id,
                    'parent_head':snapshot['content_head'],'item_id':saved['item_id'],
                    'revision_id':saved['revision_id'],'applied_at':self.now(),
                    'stale_derived_revision_ids':list(stale)})
                next_snapshot = self.contracts.validate('Snapshot',{**snapshot,'content_head':commit_id})
                tx.insert('content_commits', (vault,key_id(commit_id)), {'kind':'content',
                    'commit_id':commit_id,'parent_head':snapshot['content_head'],'vault_id':context.vault_id,
                    'item_id':saved['item_id'],'revision_id':saved['revision_id'],
                    'snapshot':next_snapshot,'receipt':receipt})
                tx.compare_exchange('content_snapshots', (vault,), snapshot, next_snapshot)
                tx.insert('content_receipts', key, {'canonical_plan':canonical,'receipt':receipt})
                self.revisions.read_in(tx,context,saved['item_id'],saved['revision_id'])
                self.access.require(tx, context, 'readContentCommit', copy.deepcopy(receipt))
        return copy.deepcopy(receipt)

    def get_snapshot(self, context):
        with self.storage.transaction() as tx:
            result = self._snapshot_in(tx,context)
        return result

    def get_commit(self, context, commit_id):
        with self.storage.transaction() as tx:
            self.access.require(tx,context,'readContentCommit',{'commit_id':key_id(commit_id)})
            value = tx.get('content_commits',(key_id(context.vault_id),key_id(commit_id)))
            if value is None:
                raise ContractError('NOT_FOUND')
            if value['kind'] == 'content':
                self.revisions.read_in(tx,context,value['item_id'],value['revision_id'])
        return value

    def get_item(self, context, item_id):
        """Current item and current vault HEAD read from the same transaction."""
        with self.storage.transaction() as tx:
            snapshot = self._snapshot_in(tx,context)
            vault, item = key_id(context.vault_id), key_id(item_id)
            self.access.require(tx,context,'getItem',{'item_id':item})
            current = tx.get('memory_current',(vault,item))
            if current is None:
                raise ContractError('NOT_FOUND')
            origin = tx.get('content_commits',(vault,key_id(current['basis_head'])))
            if origin is None or origin['item_id'] is None or key_id(origin['item_id']) != item or (
                    origin['revision_id'] is None or key_id(origin['revision_id']) != key_id(current['revision_id'])):
                raise ContractError('CURRENT_COMMIT_MISMATCH')
            revision = self.revisions.read_in(tx,context,item_id,current['revision_id'])
            view = self.contracts.validate('ItemView',{'basis_head':snapshot['content_head'],
                'item_id':revision['item_id'],'current_revision':revision})
        return view
