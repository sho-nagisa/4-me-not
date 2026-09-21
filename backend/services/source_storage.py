"""Contract-3 importSource/getSource over an injected atomic storage port."""
import copy
import json
from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4
from backend.services.memory_contracts import ContractError
from backend.services.memory_storage import UnconnectedAccess, key_id
from backend.services.source_evidence import SourceEvidence


def canonical_bytes(value):
    # Key ordering only: never normalize text, newline, IDs, or array ordering.
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeEncodeError):
        raise ContractError('INVALID_CANONICAL_INPUT') from None


class SourceStorage:
    def __init__(self, contracts, storage, *, access=None, new_id=uuid4,
                 now=lambda: datetime.now(timezone.utc).isoformat()):
        self.contracts, self.storage = contracts, storage
        self.access = access if access is not None else UnconnectedAccess()
        self.new_id, self.now = new_id, now

    def import_source(self, context, idempotency_key, request, *, source_contract):
        value = self.contracts.validate('ImportRequest', request)
        if type(source_contract) is not int or source_contract != 3:
            raise ContractError('EXPLICIT_SOURCE_MIGRATION_REQUIRED')
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise ContractError('INVALID_IDEMPOTENCY_KEY')
        canonical = canonical_bytes(value)
        key = (key_id(context.vault_id), context.caller_key, 'importSource', idempotency_key)
        with self.storage.transaction() as tx:
            self.access.require(tx, context, 'importSource', copy.deepcopy(value))
            prior = tx.get('import_receipts', key)
            if prior is not None:
                if prior['canonical_request'] != canonical:
                    raise ContractError('IDEMPOTENCY_CONFLICT')
                self.read_in(tx, context, prior['receipt']['source_id'])
                receipt = prior['receipt']
            else:
                source = {**value, 'source_id':str(self.new_id()), 'vault_id':context.vault_id,
                          'imported_at':self.now(), 'policy_revision':context.policy_revision}
                source = SourceEvidence(self.contracts, source, expected_vault=context.vault_id,
                                        source_contract=source_contract).snapshot()
                receipt = self.contracts.validate('ImportReceipt', {
                    'source_id':source['source_id'], 'vault_id':source['vault_id'],
                    'imported_at':source['imported_at'], 'status':'saved'})
                tx.insert('sources', (key_id(context.vault_id), key_id(source['source_id'])), {
                    'source':source, 'sha256':sha256(canonical_bytes(source)).hexdigest()})
                tx.insert('import_receipts', key, {'canonical_request':canonical, 'receipt':receipt})
                self.read_in(tx, context, source['source_id'])
        # Context exit must successfully commit before any success is returned.
        return copy.deepcopy(receipt)

    def read_in(self, tx, context, source_id):
        target = {'source_id':key_id(source_id)}
        self.access.require(tx, context, 'getSource', target)
        row = tx.get('sources', (key_id(context.vault_id), key_id(source_id)))
        if row is None:
            raise ContractError('NOT_FOUND')
        if sha256(canonical_bytes(row['source'])).hexdigest() != row['sha256']:
            raise ContractError('SOURCE_INTEGRITY_ERROR')
        return SourceEvidence(self.contracts, row['source'], expected_vault=context.vault_id,
                              source_contract=3).snapshot()

    def get_source(self, context, source_id):
        with self.storage.transaction() as tx:
            source = self.read_in(tx, context, source_id)
        return source
