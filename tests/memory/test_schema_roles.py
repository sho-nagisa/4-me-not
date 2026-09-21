import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
import zipfile
from backend.services.memory_contracts import ContractError, MemoryContracts
from backend.services.schema_roles import SchemaRoles


class SchemaRolesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['MEMORY_SPEC_ROOT'])
        cls.contracts = MemoryContracts(json.loads((root/'contracts/memory.schema.json').read_text(encoding='utf-8-sig')))
        cls.roles = SchemaRoles(cls.contracts)
        cls.payload = json.loads((root/'fixtures/valid.json').read_text(encoding='utf-8'))['CognitiveSchemaPayload']
        with zipfile.ZipFile(root/'archive/v0.3-original.zip') as z:
            cls.legacy = json.loads(z.read('4-me-not-collab-v0.3/fixtures/valid.json'))['CognitiveSchemaPayload']
            cls.legacy_contracts = MemoryContracts(json.loads(z.read('4-me-not-collab-v0.3/contracts/memory.schema.json')))

    def test_all_roles_positive_and_negative(self):
        for role in ('pattern','principle','model','unclassified'):
            with self.subTest(role=role):
                p = {**self.payload, 'schema_role':role, 'model_scope':'environment' if role=='model' else None}
                self.assertEqual(self.roles.validate(p), p)
                with self.assertRaises(ContractError):
                    self.roles.validate({**p, 'model_scope':None if role=='model' else 'self'})
        with self.assertRaises(ContractError):
            self.roles.validate({**self.payload, 'schema_role':'personality'})

    def test_direct_principle_and_missing_model_scope(self):
        p = {**self.payload, 'schema_role':'principle', 'model_scope':None}
        self.roles.validate(p)  # No prior pattern/model or prediction is required.
        p['schema_role'] = 'model'
        del p['model_scope']
        with self.assertRaises(ContractError):
            self.roles.validate(p)

    def test_unknown_time_and_invalid_time_shape(self):
        unknown = {'precision':'unknown','start':None,'end':None,'timezone':None,'original_expression':None}
        self.roles.validate({**self.payload, 'valid_time':unknown})
        with self.assertRaises(ContractError):
            self.roles.validate({**self.payload,'valid_time':{**unknown,'start':'2026-01-01'}})

    def test_explicit_legacy_map_preserves_id_text_and_fields(self):
        original = copy.deepcopy(self.legacy)
        identifier = '00000000-0000-4000-8000-000000000001'
        a = self.roles.migrate_legacy(identifier, original, legacy_contracts=self.legacy_contracts)
        b = self.roles.migrate_legacy(identifier, original, legacy_contracts=self.legacy_contracts)
        self.assertEqual(a, b)
        self.assertEqual(a.stable_id, identifier)
        self.assertEqual(a.original_hypothesis_digest, hashlib.sha256(original['hypothesis'].encode('utf-8')).hexdigest())
        for key, value in original.items():
            self.assertEqual(a.payload[key], value)
        self.assertEqual(a.payload['schema_role'], 'unclassified')
        self.assertEqual(a.payload['valid_time']['precision'], 'unknown')
        self.assertEqual(self.legacy, original)

    def test_new_fields_or_reverse_migration_are_not_silently_accepted(self):
        with self.assertRaises(ContractError):
            self.roles.migrate_legacy('00000000-0000-4000-8000-000000000001', self.payload,
                                     legacy_contracts=self.legacy_contracts)
        with self.assertRaises(ContractError):
            self.roles.migrate_legacy('00000000-0000-4000-8000-000000000001', self.legacy,
                legacy_contracts=self.legacy_contracts, source_contract=3, target_contract=2)
