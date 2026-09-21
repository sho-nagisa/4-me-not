"""Specification examples only: no application routing, authorization or DB.

The route comparator checks one synthetic artifact-to-hit example. It is not
a retrieval implementation, general provenance closure or a deployed Gate.
"""
import copy
import itertools
import unittest

from reference.policy_model import TrustedFacts, decide
import test_w30_02_state_axes as state_axes
from test_w30_02_state_axes import read, with_changes


def route_example_preserves_hypothesis(artifact, hit):
    content = artifact["content"]
    route = {"resource_type": "derived", "object_id": artifact["artifact_id"],
             "version_id": artifact["version_id"]}
    return (
        hit["review_status"] == artifact["review_status"]
        and hit["epistemic_kind"] == content["epistemic_kind"]
        and route in hit["route_refs"]
        and all(ref in hit["evidence_refs"] for ref in content["input_refs"])
        and all(c in hit["conditions"] for c in content["payload"]["conditions"])
        and all(u in hit["uncertainties"] for u in content["payload"]["uncertainties"])
    )


class UseConditionsTest(unittest.TestCase):
    validator = state_axes.StateAxesTest.validator

    @classmethod
    def setUpClass(cls):
        cls.schema = read("contracts/memory.schema.json")
        cls.valid = read("fixtures/valid.json")
        cls.registry = read("contracts/operation-registry.json")
        cls.cases = read("fixtures/w30-03-use-cases.json")

    def test_reference_use_boundaries(self):
        self.assertTrue(self.cases["synthetic"])
        for case in self.cases["cases"]:
            with self.subTest(case=case["id"]):
                facts = TrustedFacts(**case["facts"])
                result = decide(case["operation"], facts, self.registry)
                self.assertEqual((result.outcome, result.reason),
                                 (case["outcome"], case["reason"]))

    def test_stage_and_adoption_matrix_for_live_internal_recall(self):
        for stage, provisional in itertools.product(
            ("shadow", "internal", "presentation", "enabled"), (True, False)
        ):
            with self.subTest(stage=stage, provisional=provisional):
                result = decide("recall_internal", TrustedFacts(
                    stage=stage, provisional=provisional, live_use=True), self.registry)
                expected = "defer" if stage == "shadow" else (
                    "allow_provisional" if provisional else "allow")
                self.assertEqual(result.outcome, expected)

    def test_internal_route_example_and_schema_valid_laundering(self):
        artifact = copy.deepcopy(self.valid["ArtifactView"])
        before = copy.deepcopy(artifact)
        content = artifact["content"]
        hit = with_changes(self.valid["RecallV3Hit"], {
            "ref": {"resource_type": "derived", "object_id": artifact["artifact_id"],
                    "version_id": artifact["version_id"]},
            "summary": content["payload"]["text"],
            "review_status": "provisional", "epistemic_kind": "ai_hypothesis",
            "evidence_refs": content["input_refs"],
            "route_refs": [{"resource_type": "derived", "object_id": artifact["artifact_id"],
                            "version_id": artifact["version_id"]}],
            "conditions": content["payload"]["conditions"],
            "uncertainties": content["payload"]["uncertainties"],
        })
        self.validator("RecallV3Hit").validate(hit)
        self.assertTrue(route_example_preserves_hypothesis(artifact, hit))
        for mutation in self.cases["route_mutations"]:
            with self.subTest(field=mutation["field"]):
                changed = with_changes(hit, {mutation["field"]: mutation["value"]})
                # Shape validity alone does not prevent semantic laundering.
                self.validator("RecallV3Hit").validate(changed)
                self.assertFalse(route_example_preserves_hypothesis(artifact, changed))
        self.assertEqual(artifact, before)

    def test_get_item_rejects_unadopted_response_shapes(self):
        item = self.valid["ItemView"]
        self.validator("ItemView").validate(item)
        for revision in (self.valid["ArtifactView"],
                         with_changes(item["current_revision"], {"review_state": "provisional"})):
            with self.subTest(revision=revision.get("review_state", "artifact")):
                self.assertFalse(self.validator("ItemView").is_valid(
                    with_changes(item, {"current_revision": revision})))

    def test_recall_request_does_not_carry_authority(self):
        for mode, include in itertools.product(
            ("exact", "explore", "intention", "internal"), (True, False)
        ):
            request = with_changes(self.valid["RecallV3Request"], {
                "mode": mode, "include_provisional": include})
            self.validator("RecallV3Request").validate(request)
            for forged in ("stage", "live_use", "actor", "valid_confirmation"):
                self.assertFalse(self.validator("RecallV3Request").is_valid(
                    with_changes(request, {forged: "enabled"})))

    def test_grade_and_deployment_require_complete_scope(self):
        for name in ("Grade", "DeploymentView"):
            for field in ("feature", "producer_version", "purpose"):
                with self.subTest(schema=name, missing=field):
                    value = copy.deepcopy(self.valid[name])
                    del value[field]
                    self.assertFalse(self.validator(name).is_valid(value))
        # Actual tuple lookup and current policy validation require a trusted
        # deployment adapter; this test claims only structural completeness.


if __name__ == "__main__":
    unittest.main(verbosity=2)

