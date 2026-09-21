"""Synthetic conversion and reference checks, not DB migration acceptance."""
import copy
import unittest
from jsonschema import ValidationError
from contracts.migration_examples import (
    old_asset, convert_source_example, digest, check_dependency_evidence_example,
)
from reference.policy_model import TrustedFacts, decide
import test_w30_02_state_axes as state_axes


class MigrationTest(unittest.TestCase):
    validator = state_axes.StateAxesTest.validator

    @classmethod
    def setUpClass(cls):
        cls.schema = state_axes.read('contracts/memory.schema.json')
        cls.old = old_asset('fixtures/valid.json')['Source']
        cls.registry = state_axes.read('contracts/operation-registry.json')

    def test_v2_and_forged_v3_require_explicit_provenance(self):
        self.assertFalse(self.validator('Source').is_valid(self.old))
        forged = {**self.old, 'schema_version':3}
        # A shape alone cannot prove whether identical fields came from v2.
        self.validator('Source').validate(forged)
        with self.assertRaises(ValueError):
            convert_source_example(forged, source_contract=2)
        for version in (1, 3):
            with self.assertRaises(ValueError):
                convert_source_example(self.old, source_contract=version)

    def test_explicit_conversion_is_repeatable_and_preserves_all_content(self):
        before = copy.deepcopy(self.old)
        first, evidence = convert_source_example(self.old, source_contract=2)
        self.assertEqual((first, evidence), convert_source_example(self.old, source_contract=2))
        self.assertEqual(self.old, before)
        for key in before:
            if key != 'schema_version':
                self.assertEqual(before[key], first[key], key)
        self.assertEqual(evidence['input_digest'], digest(before))
        self.assertEqual(evidence['output_digest'], digest(first))
        # Perturb ID/identity/messages: the immutable-content evidence changes.
        for key in ('source_id','vault_id','messages'):
            changed = copy.deepcopy(first)
            changed[key] = 'tampered'
            self.assertNotEqual(digest(changed), evidence['output_digest'])

    def test_legacy_approval_and_share_level_are_not_new_grants(self):
        for key in ('approved','approve','share_level'):
            with self.assertRaises(ValidationError):
                convert_source_example({**self.old, key:True}, source_contract=2)
        result = decide('external_ai_send', TrustedFacts(stage='enabled', live_use=True,
            provisional=False, valid_confirmation=False, delegation_matches=False), self.registry)
        self.assertEqual(result.outcome, 'require_confirmation')

    def test_unknown_dependency_is_not_empty_non_dependency(self):
        for recorded in ([], ['prediction_loop']):
            with self.assertRaises(ValueError):
                check_dependency_evidence_example(recorded, None)
        with self.assertRaises(ValueError):
            check_dependency_evidence_example([], ['prediction_loop'])
        check_dependency_evidence_example(['prediction_loop'], ['prediction_loop'])

    def test_reverse_conversion_and_restored_erased_use_are_rejected(self):
        migrated, _ = convert_source_example(self.old, source_contract=2)
        for source in (migrated, {**migrated, 'schema_version':2}):
            with self.assertRaises(ValueError):
                convert_source_example(source, source_contract=3, target_contract=2)
        for facts in (TrustedFacts(erased=True), TrustedFacts(consent_revoked=True)):
            self.assertEqual(decide('recall_internal', facts, self.registry).outcome, 'deny')
