"""Local schema/boundary tests; reference Gate remains unmodified."""
import copy
import itertools
import unittest

from jsonschema import Draft202012Validator, ValidationError
from contracts.authority_boundary import (
    ACTOR_KIND, BOUNDARY, CallerFields, OPERATIONS, check_actor_binding,
    check_required_set, required_authorities, validator,
)
from reference.policy_model import TrustedFacts, decide
from test_w30_02_state_axes import read


class AuthorityBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = read("fixtures/w30-04-authority-cases.json")
        cls.valid = read("fixtures/valid.json")
        cls.caller = CallerFields(**cls.cases["caller"])

    def test_schema_and_independent_types(self):
        Draft202012Validator.check_schema(BOUNDARY)
        self.assertTrue(self.cases["synthetic"])
        for name, valid, invalid in (
            ("Authority", "action", "enabled"),
            ("DecisionOutcome", "allow_provisional", "continue"),
            ("PermissionBasis", "interactive", "allow"),
        ):
            validator(name).validate(valid)
            self.assertFalse(validator(name).is_valid(invalid))
        for bad in ([], ["unknown"], ["structure", "structure"]):
            self.assertFalse(validator("AuthoritySet").is_valid(bad))

    def test_candidate_rejects_authority_self_reports(self):
        for field, value in self.cases["forged_fields"].items():
            with self.subTest(field=field):
                candidate = {**self.valid["GateRequest"], field: value}
                with self.assertRaises(ValidationError):
                    required_authorities(caller=self.caller, candidate=candidate,
                                         vault_id=self.caller.vault_id)
        for name, extra in (("CallerFields", {"approved": True}),
                            ("AuditActor", {"authenticated": True})):
            baseline = self.cases["caller"] if name == "CallerFields" else self.valid["Actor"]
            self.assertFalse(validator(name).is_valid({**baseline, **extra}))

    def test_caller_cannot_be_taken_from_json(self):
        with self.assertRaises(TypeError):
            required_authorities(caller=self.cases["caller"],
                                 candidate=self.valid["GateRequest"],
                                 vault_id=self.caller.vault_id)
        with self.assertRaises(ValueError):
            required_authorities(caller=self.caller, candidate=self.valid["GateRequest"],
                                 vault_id="00000000-0000-4000-8000-000000000099")
        with self.assertRaises(ValidationError):
            CallerFields("user", self.caller.id, self.caller.vault_id)

    def test_actor_mapping_is_forward_and_identity_bound(self):
        for role, kind in itertools.product(ACTOR_KIND, ACTOR_KIND.values()):
            with self.subTest(role=role, kind=kind):
                caller = CallerFields(role, self.caller.id, self.caller.vault_id)
                actor = {"kind": kind, "id": caller.id}
                if kind == ACTOR_KIND[role]:
                    check_actor_binding(caller, actor)
                else:
                    with self.assertRaises(ValueError):
                        check_actor_binding(caller, actor)
        with self.assertRaises(ValueError):
            check_actor_binding(self.caller, {"kind":"model",
                "id":"00000000-0000-4000-8000-000000000099"})
        with self.assertRaises(TypeError):
            check_actor_binding({"role":"owner"}, {"kind":"user","id":self.caller.id})

    def test_all_compound_requirements_must_be_present(self):
        for case in self.cases["compound"]:
            with self.subTest(operation=case["operation"]):
                candidate = {**self.valid["GateRequest"], "operation":case["operation"]}
                before = copy.deepcopy(candidate)
                self.assertEqual(required_authorities(caller=self.caller, candidate=candidate,
                    vault_id=self.caller.vault_id), frozenset(case["required"]))
                check_required_set(case["operation"], list(reversed(case["required"])))
                for missing in case["required"]:
                    with self.assertRaises(ValueError):
                        check_required_set(case["operation"],
                            [a for a in case["required"] if a != missing])
                self.assertEqual(candidate, before)
        for name, entry in OPERATIONS.items():
            check_required_set(name, entry["authorities"])

    def test_reference_model_cannot_adopt_even_with_claimed_confidence(self):
        result = decide("profile_adopt", TrustedFacts(actor="model",
            reported_confidence=0.99, valid_confirmation=True), OPERATIONS)
        self.assertEqual((result.outcome, result.reason), ("deny", "FORBIDDEN"))
        owner = decide("profile_adopt", TrustedFacts(actor="owner",
            reported_confidence=0.99, valid_confirmation=False), OPERATIONS)
        self.assertEqual(owner.outcome, "require_confirmation")


if __name__ == "__main__":
    unittest.main(verbosity=2)
