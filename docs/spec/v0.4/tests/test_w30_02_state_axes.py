"""W30-02 schema/fixture/reference checks; no app imports or DB operations.

Review examples assert the proposed before/after contract only. They do not
implement a ledger transaction, authenticate a caller or issue a capability.
"""
from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker
from reference.policy_model import TrustedFacts, decide

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def with_changes(original, changes):
    result = copy.deepcopy(original)
    for path, value in changes.items():
        parts = path.split(".")
        target = result
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = copy.deepcopy(value)
    return result


def review_example_violations(before, after, trusted_actor):
    """Fixture-only invariant comparison, not a transition command or Gate.

    Only provisional -> adopted/rejected examples are in scope here. Real owner
    authentication, confirmation binding and transaction guards belong to W31/33.
    """
    problems = []
    if trusted_actor != "owner":
        problems.append("owner_required")
    if before["review_status"] != "provisional" or after["review_status"] not in {
        "user_adopted", "user_rejected"
    }:
        problems.append("unsupported_review_example")
    mutable = {"review_status", "review_event_id"}
    if {k: v for k, v in before.items() if k not in mutable} != {
        k: v for k, v in after.items() if k not in mutable
    }:
        problems.append("immutable_fields_changed")
    return problems


class StateAxesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = read("contracts/memory.schema.json")
        cls.valid = read("fixtures/valid.json")
        cls.cases = read("fixtures/w30-02-state-cases.json")
        cls.registry = read("contracts/operation-registry.json")

    def validator(self, name):
        return Draft202012Validator(
            {"$schema": self.schema["$schema"], "$defs": self.schema["$defs"],
             "$ref": "#/$defs/" + name}, format_checker=FormatChecker()
        )

    def test_schema_cases(self):
        self.assertTrue(self.cases["synthetic"])
        for case in self.cases["schema_cases"]:
            with self.subTest(case=case["id"]):
                value = with_changes(self.valid[case["schema"]], case["set"])
                errors = list(self.validator(case["schema"]).iter_errors(value))
                self.assertEqual(not errors, case["valid"], case["id"])

    def test_review_lifecycle_and_recording_lane_are_independent_shapes(self):
        # 48 valid stored shapes. A valid stored shape is NOT a readable response.
        for review, lifecycle, lane in itertools.product(
            ("provisional", "user_adopted", "user_rejected"),
            ("current", "stale", "retracted", "erased"),
            ("shadow", "internal", "presentation", "enabled"),
        ):
            with self.subTest(review=review, lifecycle=lifecycle, lane=lane):
                value = with_changes(self.valid["ArtifactView"], {
                    "review_status": review, "lifecycle": lifecycle,
                    "recorded_lane": lane,
                    "review_event_id": None if review == "provisional" else
                    "00000000-0000-4000-8000-000000000099",
                })
                self.validator("ArtifactView").validate(value)
                self.assertEqual(value["content"]["epistemic_kind"], "ai_hypothesis")

    def test_unknown_and_cross_axis_enum_values_are_rejected(self):
        fields = [
            ("MemoryDraft", "epistemic_kind", "user_adopted"),
            ("ChangeRecord", "state", "current"),
            ("MemoryRevision", "review_state", "user_adopted"),
            ("ArtifactView", "review_status", "shadow"),
            ("ArtifactView", "lifecycle", "user_adopted"),
            ("ArtifactView", "recorded_lane", "provisional"),
            ("DeploymentView", "stage", "disabled"),
            ("FeatureControlView", "state", "shadow"),
            ("GateDecision", "outcome", "enabled"),
            ("GateDecision", "basis", "continue"),
        ]
        for name, field, other_axis in fields:
            for unknown in ("unknown-enum", other_axis):
                with self.subTest(schema=name, field=field, value=unknown):
                    value = with_changes(self.valid[name], {field: unknown})
                    self.assertTrue(list(self.validator(name).iter_errors(value)))

    def test_reference_current_state_overrides_adoption_and_confidence(self):
        for case in self.cases["use_cases"]:
            with self.subTest(case=case["id"]):
                facts = TrustedFacts(**case["facts"])
                result = decide(case["operation"], facts, self.registry)
                self.assertEqual((result.outcome, result.reason),
                                 (case["outcome"], case["reason"]))

    def test_review_examples_preserve_origin_content_and_dependencies(self):
        before = with_changes(self.valid["ArtifactView"], {
            "review_status": "provisional", "review_event_id": None,
            "recorded_lane": "internal", "producer_feature": "schema",
            "required_features": ["prediction_loop"],
        })
        self.validator("ArtifactView").validate(before)
        for case in self.cases["review_examples"]:
            with self.subTest(case=case["id"]):
                after = with_changes(before, case["after"])
                # Even the forbidden transitions here have individually valid
                # response shapes: their restriction requires a semantic guard.
                self.validator("ArtifactView").validate(after)
                self.assertEqual(review_example_violations(before, after, case["actor"]),
                                 case["violations"])

    def test_adoption_cannot_rewrite_payload_or_origin_in_same_version(self):
        before = with_changes(self.valid["ArtifactView"], {
            "review_status": "provisional", "review_event_id": None,
        })
        adopted = with_changes(before, {
            "review_status": "user_adopted",
            "review_event_id": "00000000-0000-4000-8000-000000000099",
        })
        for field, replacement in (
            ("content.epistemic_kind", "self_report"),
            ("content.producer_version", "another-producer"),
            ("content.input_refs", []),
            ("version_id", "00000000-0000-4000-8000-000000000098"),
        ):
            with self.subTest(field=field):
                after = with_changes(adopted, {field: replacement})
                self.assertIn("immutable_fields_changed",
                              review_example_violations(before, after, "owner"))

    def test_snapshot_is_version_coordinates_not_state_or_permission(self):
        snapshot = copy.deepcopy(self.valid["Snapshot"])
        for field in ("review_status", "lifecycle", "stage", "outcome", "tier"):
            with self.subTest(field=field):
                self.assertTrue(list(self.validator("Snapshot").iter_errors(
                    with_changes(snapshot, {field: "enabled"}))))
        self.assertEqual(snapshot, self.valid["Snapshot"])

    def test_published_wire_constraints_are_unchanged(self):
        # Runner extracts the original zip separately; this baseline never gets
        # overlaid. Compare all constraints, ignoring only added annotations.
        original = read("w30-02-baseline-memory.schema.json")
        def constraints(value):
            if isinstance(value, dict):
                return {k: constraints(v) for k, v in value.items() if k != "$comment"}
            if isinstance(value, list):
                return [constraints(v) for v in value]
            return value
        self.assertEqual(constraints(original), constraints(self.schema))
        self.assertEqual(len(self.schema["$defs"]), 86)


if __name__ == "__main__":
    unittest.main(verbosity=2)
