"""Schema role validation/migration only; no classification, adoption or storage."""
import copy
from dataclasses import dataclass
from hashlib import sha256
from uuid import UUID
from backend.services.memory_contracts import ContractError, MemoryContracts


@dataclass(frozen=True)
class SchemaMigration:
    stable_id: str
    original_hypothesis_digest: str
    payload: dict
    source_contract: int = 2
    target_contract: int = 3


class SchemaRoles:
    def __init__(self, contracts: MemoryContracts):
        self.contracts = contracts

    def validate(self, payload):
        return self.contracts.validate('CognitiveSchemaPayload', payload)

    def migrate_legacy(self, stable_id, payload, *, legacy_contracts,
                       source_contract=2, target_contract=3):
        # Explicit caller-supplied legacy schema, never inferred from prose.
        if (source_contract, target_contract) != (2, 3):
            raise ContractError('UNSUPPORTED_MIGRATION')
        UUID(stable_id)
        original = legacy_contracts.validate('CognitiveSchemaPayload', payload)
        if any(key in original for key in ('schema_role', 'model_scope', 'valid_time',
                'alternative_refs', 'unresolved_questions', 'independent_evidence_groups')):
            raise ContractError('NOT_LEGACY_SCHEMA')
        result = copy.deepcopy(original)
        result.update(schema_role='unclassified', model_scope=None,
            valid_time={'precision':'unknown', 'start':None, 'end':None,
                        'timezone':None, 'original_expression':None},
            alternative_refs=[], unresolved_questions=['legacy role/time/evidence grouping unknown'],
            independent_evidence_groups=[])
        self.validate(result)
        return SchemaMigration(stable_id,
            sha256(original['hypothesis'].encode('utf-8')).hexdigest(), result)
