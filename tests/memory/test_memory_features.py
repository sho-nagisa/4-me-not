import ast
import copy
import json
import os
from pathlib import Path
import unittest
from backend.services.memory_contracts import ContractError, MemoryContracts
from backend.services.memory_features import CoreComposition, FeatureRegistry


def forbidden_core_imports(source):
    """Core local modules have an explicit import boundary; dynamic loading forbidden."""
    allowed = {'dataclasses','typing','copy','hashlib','uuid','jsonschema',
               'backend.services.memory_contracts'}
    violations = []
    for node in ast.walk(ast.parse(source)):
        modules = [a.name for a in node.names] if isinstance(node,ast.Import) else (
            [node.module or ''] if isinstance(node,ast.ImportFrom) else [])
        violations.extend(m for m in modules if m not in allowed)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in ('__import__','eval','exec'):
            violations.append(node.func.id)
    return violations


class FeatureRegistryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['MEMORY_SPEC_ROOT'])
        cls.rows = json.loads((root/'contracts/feature-registry.json').read_text(encoding='utf-8'))
        cls.contracts = MemoryContracts(json.loads((root/'contracts/memory.schema.json').read_text(encoding='utf-8-sig')))
        cls.valid = json.loads((root/'fixtures/valid.json').read_text(encoding='utf-8'))

    def test_v04_001_three_tiers_and_independent_axes(self):
        registry = FeatureRegistry(self.rows)
        self.assertEqual(len(registry.features()),25)
        self.assertEqual({f.tier for f in registry.features()}, {'core','experimental','evaluation_only'})
        p = registry.get('prediction_loop')
        self.assertEqual((p.decision_status,p.implementation_status,p.default_control,p.default_stage),
            ('accepted-experimental','specified-not-implemented','disabled','shadow'))
        altered = copy.deepcopy(self.rows)
        altered[0]['implementation_status']='locally-tested-not-deployed'
        self.assertEqual(FeatureRegistry(altered).get('source').decision_status, 'agreed-direction')

    def test_v04_002_extension_defaults_and_candidate_rejection(self):
        registry = FeatureRegistry(self.rows)
        for row in self.rows:
            if row['tier']!='core':
                self.assertEqual((registry.get(row['feature_id']).default_control,
                    registry.get(row['feature_id']).default_stage),('disabled','shadow'))
                for key,value in [('default_control','enabled'),('default_stage','presentation')]:
                    altered=copy.deepcopy(self.rows)
                    next(r for r in altered if r['feature_id']==row['feature_id'])[key]=value
                    with self.assertRaises(ContractError): FeatureRegistry(altered)
            if row['decision_status']=='candidate':
                with self.assertRaisesRegex(ContractError,'CLASSIFICATION_NOT_LIVE'):
                    registry.check_live_classification(row['feature_id'])

    def test_v04_004_unknown_feature_tier_duplicate_and_cycle(self):
        with self.assertRaises(ContractError): FeatureRegistry(self.rows).get('unknown')
        for field,value in [('tier','unknown'),('depends_on',['unknown']),('depends_on',['ledger'])]:
            altered=copy.deepcopy(self.rows)
            altered[0][field]=value
            with self.assertRaises(ContractError): FeatureRegistry(altered)
        with self.assertRaises(ContractError): FeatureRegistry(self.rows+[self.rows[0]])

    def test_v04_004_core_requires_no_experimental_or_study(self):
        for identifier in ('prediction_loop','exposure_balance_study'):
            altered=copy.deepcopy(self.rows)
            altered[0]['depends_on']=[identifier]
            with self.assertRaisesRegex(ContractError,'CORE_REQUIRES_EXTENSION'):
                FeatureRegistry(altered)

    def test_v04_004_optional_composition_starts_without_prediction(self):
        registry=FeatureRegistry(self.rows)
        core=CoreComposition(registry)
        self.assertFalse(core.has_extension('prediction_loop'))
        self.assertEqual(core.registry.get('schema').default_control,'enabled')
        class ExplodingPort:
            def evaluate(self, candidate): raise AssertionError('must not invoke extension')
        injected=CoreComposition(registry,{'prediction_loop':ExplodingPort()})
        self.assertTrue(injected.has_extension('prediction_loop'))
        self.assertEqual(injected.registry.get('prediction_loop').default_control,'disabled')
        with self.assertRaises(ContractError): CoreComposition(registry,{'missing':ExplodingPort()})

    def test_v04_004_core_import_boundary_with_negative_fixture(self):
        repo=Path(__file__).resolve().parents[2]
        for name in ('memory_contracts','schema_roles','memory_features'):
            self.assertEqual(forbidden_core_imports((repo/'backend/services'/f'{name}.py').read_text(encoding='utf-8')),[])
        for text in ('import backend.experimental.prediction', 'from prediction import predict',
                     '__import__("prediction")', 'import importlib; importlib.import_module("prediction")'):
            self.assertTrue(forbidden_core_imports(text))

    def test_v04_035_study_cannot_enter_live(self):
        registry=FeatureRegistry(self.rows)
        for row in self.rows:
            if row['tier']=='evaluation_only':
                with self.assertRaises(ContractError): registry.check_live_classification(row['feature_id'])
        registry.check_live_classification('source')  # Necessary classification only, not permission.

    def test_control_and_snapshot_shapes_do_not_change_registry(self):
        registry=FeatureRegistry(self.rows)
        before=registry.features()
        view=registry.validate_control_view(self.contracts,self.valid['FeatureControlView'])
        self.assertEqual(view,self.valid['FeatureControlView'])
        with self.assertRaisesRegex(ContractError,'UNKNOWN_FEATURE'):
            registry.validate_control_view(self.contracts,{**view,'feature_id':'missing'})
        self.contracts.validate('Snapshot',self.valid['Snapshot'])
        self.assertEqual(before,registry.features())
