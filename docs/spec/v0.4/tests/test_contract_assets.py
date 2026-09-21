"""Contract asset checks, NOT application or LLM quality tests."""
from __future__ import annotations
import copy
import csv
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]

def unique_keys(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError(f"Duplicate key: {k}")
        result[k] = v
    return result

def read(p):
    return json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)

def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)

class ContractAssetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = read(ROOT / "contracts/memory.schema.json")
        cls.valid = read(ROOT / "fixtures/valid.json")
        cls.openapi = read(ROOT / "contracts/openapi.json")
        cls.registry = read(ROOT / "contracts/operation-registry.json")

    def validator(self, name):
        return Draft202012Validator({"$schema": self.schema["$schema"], "$defs": self.schema["$defs"], "$ref": "#/$defs/" + name}, format_checker=FormatChecker())

    def test_json_files_have_no_duplicate_keys(self):
        for p in sorted(ROOT.rglob("*.json")):
            with self.subTest(path=str(p.relative_to(ROOT))):
                read(p)

    def test_schema_is_well_formed(self):
        Draft202012Validator.check_schema(self.schema)

    def test_every_named_definition_has_a_valid_example(self):
        self.assertEqual(set(self.valid), set(self.schema["$defs"]))
        for name, example in self.valid.items():
            with self.subTest(name=name):
                self.validator(name).validate(example)

    def test_invalid_examples_are_rejected(self):
        for c in read(ROOT / "fixtures/invalid.json"):
            with self.subTest(reason=c["reason"]):
                self.assertTrue(list(self.validator(c["schema"]).iter_errors(c["value"])))

    def test_all_active_refs_are_local_and_resolvable(self):
        for p in sorted((ROOT / "contracts").glob("*.schema.json")) + [ROOT / "contracts/openapi.json"]:
            for node in walk(read(p)):
                if "$ref" not in node:
                    continue
                uri, _, pointer = node["$ref"].partition("#")
                self.assertNotIn("://", uri)
                q = (p.parent / uri).resolve() if uri else p
                self.assertTrue(q.is_relative_to(ROOT))
                value = read(q)
                for token in pointer.strip("/").split("/") if pointer else []:
                    value = value[unquote(token).replace("~1", "/").replace("~0", "~")]

    def test_api_inventory_matches_paths_methods_and_schemas(self):
        inventory = read(ROOT / "contracts/api-inventory.json")
        pairs = {}
        self.assertEqual(self.openapi["openapi"], "3.1.1")
        for path, methods in self.openapi["paths"].items():
            for method, op in methods.items():
                pairs[(method.upper(), path)] = op
                self.assertEqual(set(re.findall(r"\{(.*?)\}", path)), {x["name"] for x in op["parameters"] if x["in"] == "path"})
                if method == "post":
                    self.assertTrue(any(x["name"] == "Idempotency-Key" and x["required"] for x in op["parameters"]))
        self.assertEqual(len(pairs), 38)
        self.assertEqual(len({x["operation"] for x in inventory}), 38)
        for x in inventory:
            op = pairs[(x["method"], x["path"])]
            self.assertEqual(op["operationId"], x["operation"])
            self.assertTrue(op["responses"][str(x["success"])]["content"]["application/json"]["schema"]["$ref"].endswith("/" + x["response"]))
            if x["request"]:
                self.assertTrue(op["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/" + x["request"]))

    def test_authority_csv_matches_registry(self):
        rows = list(csv.reader((ROOT / "docs/authority-matrix.csv").read_text().splitlines()))
        self.assertEqual(len(rows) - 1, len(self.registry))
        self.assertEqual({r[0] for r in rows[1:]}, set(self.registry))
        for row in rows[1:]:
            r = self.registry[row[0]]
            self.assertEqual(row[2].split(","), r["authorities"])
            self.assertEqual(row[3], r["gate"])

    def test_requirements_acceptance_and_api_ids_are_consistent(self):
        ids = re.findall(r"@((?:AUTO|V04)-\d+)", "\n".join(p.read_text() for p in (ROOT / "acceptance").glob("*.feature")))
        req = read(ROOT / "requirements.json")
        ops = {x["operation"] for x in read(ROOT / "contracts/api-inventory.json")}
        self.assertEqual(len(ids), 76)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(req), len({x["id"] for x in req}))
        for r in req:
            self.assertTrue(set(r["acceptance_ids"]) <= set(ids))
            self.assertTrue(set(r["api_operations"]) <= ops)

    def test_mermaid_document_blocks_match_sources(self):
        index = read(ROOT / "docs/diagrams-index.json")
        for doc, names in index.items():
            blocks = re.findall(r"```mermaid\n(.*?)\n```", (ROOT / doc).read_text(), re.S)
            self.assertEqual(len(blocks), len(names))
            for block, name in zip(blocks, names):
                self.assertEqual(block.strip(), (ROOT / "diagrams" / name).read_text().strip())
                self.assertTrue(block.startswith(("graph TD", "sequenceDiagram")))
        # This is a source consistency check, NOT a graphical Mermaid renderer.

    def test_cognitive_fixture_kinds_evidence_and_state(self):
        c = read(ROOT / "fixtures/cognitive-case.json")
        self.assertTrue(c["synthetic"])
        kinds = set()
        raw = c["source"]["text"]
        for a in c["derived_artifacts"]:
            self.validator("ArtifactView").validate(a)
            kinds.add(a["content"]["kind"])
            self.assertEqual(a["review_status"], "provisional")
            self.assertEqual(a["content"]["epistemic_kind"], "ai_hypothesis")
            for e in a["content"]["evidence"]:
                self.assertEqual(raw.count(e["quote"]), 1)
        self.assertEqual(len(kinds), 8)
        boundary = c["derived_artifacts"][0]["content"]["payload"]["locators"][0]["span"]
        self.assertEqual(raw.encode("utf-8")[boundary["start_byte"]:boundary["end_byte"]].decode("utf-8"), boundary["quote"])
        gist = next(a for a in c["derived_artifacts"] if a["content"]["kind"] == "gist")["content"]["payload"]
        self.assertTrue(gist["conditions"])
        self.assertTrue(gist["negations"])
        self.assertTrue(gist["uncertainties"])

    def test_owner_adoption_preserves_hypothesis_kind(self):
        v = copy.deepcopy(self.valid["ArtifactView"])
        v.update(review_status="user_adopted", review_event_id=self.valid["VersionRef"]["version_id"])
        self.validator("ArtifactView").validate(v)
        self.assertEqual(v["content"]["epistemic_kind"], "ai_hypothesis")
        self.assertNotIn("objective_truth", self.schema["$defs"]["ArtifactView"]["properties"])
        # Static state example only; actual adoption transaction is not run here.

    def test_feedback_silence_and_producer_authority_not_accepted(self):
        signals = self.schema["$defs"]["FeedbackV3Request"]["properties"]["signal"]["enum"]
        self.assertNotIn("no_response", signals)
        self.assertNotIn("review_status", self.schema["$defs"]["DerivationRequest"]["properties"])
        for prop in ("risk", "approved", "confidence", "actor"):
            self.assertNotIn(prop, self.schema["$defs"]["GateRequest"]["properties"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
