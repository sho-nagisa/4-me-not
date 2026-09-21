"""Immutable confirmed revisions/current projection; no approveChange endpoint."""
import copy
from typing import Protocol
from backend.services.memory_contracts import ContractError
from backend.services.memory_storage import UnconnectedAccess, key_id
from backend.services.source_evidence import SourceEvidence


class DependencyPort(Protocol):
    def resolve(self, tx, context, content) -> tuple[str, ...] | None:
        """Trusted W42-03 port: all refs + producer provenance, same vault, current use.

        None means unresolved. An empty result requires proof of no extension origin.
        """
        ...


class UnconnectedDependencies:
    def resolve(self, tx, context, content):
        return None


class MemoryRevisions:
    def __init__(self, contracts, storage, sources, registry, *, access=None, dependencies=None):
        self.contracts, self.storage, self.sources, self.registry = contracts, storage, sources, registry
        self.access = access if access is not None else UnconnectedAccess()
        self.dependencies = dependencies if dependencies is not None else UnconnectedDependencies()

    def _validate_evidence(self, tx, context, revision):
        evidence, spans = revision['content']['evidence'], revision['evidence_spans']
        if len(evidence) != len(spans):
            raise ContractError('EVIDENCE_SPAN_MISMATCH')
        for candidate, span in zip(evidence, spans):
            if (key_id(candidate['source_id']), key_id(candidate['message_id']), candidate['quote']) != (
                    key_id(span['source_id']), key_id(span['message_id']), span['quote']):
                raise ContractError('EVIDENCE_SPAN_MISMATCH')
            source = self.sources.read_in(tx, context, span['source_id'])
            SourceEvidence(self.contracts, source, expected_vault=context.vault_id,
                           source_contract=3).verify_text_locator({'type':'text','span':span})

    def _check_dependencies(self, tx, context, revision):
        content = revision['content']
        for revision_id in content['derived_from_revision_ids']:
            parent = tx.get('memory_revisions', (key_id(context.vault_id),key_id(revision_id)))
            if parent is None:
                raise ContractError('DEPENDENCY_NOT_FOUND')
            self.access.require(tx, context, 'readRevision', copy.deepcopy(parent))
        features = self.dependencies.resolve(tx, context, copy.deepcopy(content))
        if features is None:
            raise ContractError('DEPENDENCIES_UNRESOLVED')
        if not isinstance(features, tuple) or any(not isinstance(f,str) for f in features):
            raise ContractError('INVALID_DEPENDENCY_RESULT')
        resolved = sorted(set(features))
        for feature in resolved:
            self.registry.get(feature)
        if set(revision['required_features']) != set(resolved):
            raise ContractError('DEPENDENCY_FEATURE_MISMATCH')
        return resolved

    def project_in(self, tx, context, revision, *, expected_current, basis_head):
        """Internal transaction participant. Caller must not publish without a Commit.

        W31-04 coordinates the enclosing transaction. No permission from DTO fields.
        """
        value = self.contracts.validate('MemoryRevision', revision)
        vault, item, rid = key_id(context.vault_id), key_id(value['item_id']), key_id(value['revision_id'])
        if key_id(value['vault_id']) != vault:
            raise ContractError('VAULT_MISMATCH')
        self.access.require(tx, context, 'storeConfirmedRevision', copy.deepcopy(value))
        key_id(basis_head)
        current = tx.get('memory_current', (vault,item))
        item_record = tx.get('memory_items', (vault,item))
        if current is None and item_record is not None:
            raise ContractError('CURRENT_MISSING')
        if current is not None and item_record is None:
            raise ContractError('ITEM_INTEGRITY_ERROR')
        actual = None if current is None else key_id(current['revision_id'])
        expected = None if expected_current is None else key_id(expected_current)
        if actual != expected:
            raise ContractError('CURRENT_CONFLICT')
        parent_id = value['parent_revision_id']
        if (None if parent_id is None else key_id(parent_id)) != expected or rid == expected:
            raise ContractError('INVALID_REVISION_PARENT')
        if expected is not None:
            parent = tx.get('memory_revisions', (vault,expected))
            if parent is None or key_id(parent['item_id']) != item:
                raise ContractError('INVALID_REVISION_PARENT')
        self._validate_evidence(tx, context, value)
        value['required_features'] = self._check_dependencies(tx, context, value)
        if item_record is None:
            tx.insert('memory_items', (vault,item), {'item_id':value['item_id'],
                'vault_id':value['vault_id'],'root_revision_id':value['revision_id']})
        tx.insert('memory_revisions', (vault,rid), value)
        tx.compare_exchange('memory_current', (vault,item), current,
                            {'revision_id':value['revision_id'],'basis_head':basis_head})
        return copy.deepcopy(value)

    def read_in(self, tx, context, item_id, revision_id):
        vault, item, rid = key_id(context.vault_id), key_id(item_id), key_id(revision_id)
        self.access.require(tx, context, 'readRevision', {'item_id':item,'revision_id':rid})
        value = tx.get('memory_revisions', (vault,rid))
        if value is None or key_id(value['item_id']) != item or key_id(value['vault_id']) != vault:
            raise ContractError('NOT_FOUND')
        value = self.contracts.validate('MemoryRevision',value)
        self.access.require(tx, context, 'readRevision', copy.deepcopy(value))
        self._validate_evidence(tx, context, value)
        self._check_dependencies(tx, context, value)
        return value

    def get_revision(self, context, item_id, revision_id):
        with self.storage.transaction() as tx:
            value = self.read_in(tx, context, item_id, revision_id)
        return value

    def get_item(self, context, item_id):
        with self.storage.transaction() as tx:
            key = (key_id(context.vault_id),key_id(item_id))
            self.access.require(tx, context, 'getItem', {'item_id':key[1]})
            current = tx.get('memory_current', key)
            if current is None:
                raise ContractError('NOT_FOUND')
            revision = self.read_in(tx, context, item_id, current['revision_id'])
            view = self.contracts.validate('ItemView', {'basis_head':current['basis_head'],
                'item_id':revision['item_id'],'current_revision':revision})
        return view
