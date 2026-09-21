"""Mapping audit, not production routing or authorization."""
import ast
import csv
import os
from pathlib import Path
import unittest
from reference.policy_model import TrustedFacts, decide
from test_w30_02_state_axes import read, ROOT


class MappingTest(unittest.TestCase):
    def test_csv_json_markdown_all_columns(self):
        registry = read('contracts/operation-registry.json')
        rows = list(csv.reader((ROOT/'docs/authority-matrix.csv').read_text(encoding='utf-8').splitlines()))[1:]
        md = {}
        for line in (ROOT/'docs/authority-matrix.md').read_text(encoding='utf-8').split('## v0.4')[0].splitlines():
            cells = [v.strip().strip('`') for v in line.split('|')[1:-1]]
            if cells and cells[0] in registry:
                self.assertNotIn(cells[0], md)
                md[cells[0]] = cells
        self.assertEqual(set(md), set(registry))
        self.assertEqual(len(rows), len(registry))
        for row in rows:
            r = registry[row[0]]
            self.assertEqual(row[1:8], [r['label'], ','.join(r['authorities']), r['gate'],
                r['result_state'], ','.join(r['actors']), r['conditions'], r['feature_id']])
            self.assertEqual(row[8].lower(), str(r['required_feature_runtime']).lower())
            self.assertEqual(md[row[0]][1:], [r['label'], ', '.join(r['authorities']),
                r['gate'], r['result_state'], r['conditions']])

    def test_complete_audit_and_explicit_mapping_gaps(self):
        registry = read('contracts/operation-registry.json')
        mapping = read('contracts/api-authority-map.json')
        inventory = read('contracts/api-inventory.json')
        features = read('contracts/feature-registry.json')
        text = (ROOT/'docs/w30-05-mapping-audit.md').read_text(encoding='utf-8')
        self.assertEqual(len(mapping), 38)
        self.assertEqual({m['operation_id'] for m in mapping}, {a['operation'] for a in inventory})
        for m in mapping:
            self.assertEqual(len(m['use_classes']), len(set(m['use_classes'])))
            self.assertTrue(m['mandatory_checks'])
            self.assertTrue(m['note'])
        for keys, section in (
            (registry, text.split('## 操作')[1].split('## 全API')[0]),
            ([a['operation'] for a in inventory], text.split('## 全API')[1].split('## 全機能')[0]),
            ([f['feature_id'] for f in features], text.split('## 全機能')[1].split('## 未対応')[0]),
        ):
            for key in keys:
                self.assertEqual(sum(l.startswith('| '+key+' |') for l in section.splitlines()), 1, key)
        for a in inventory:
            m = next(m for m in mapping if m['operation_id'] == a['operation'])
            self.assertIn('| '+a['operation']+' | '+a['method']+' | '+a['path']+' | '+','.join(m['use_classes'])+' |', text)
        used = {c for m in mapping for c in m['use_classes']}
        self.assertEqual(set(registry)-used, {'counterevidence_search'})
        evaluation = next(m for m in mapping if m['operation_id']=='evaluateUse')
        self.assertEqual(len(set(registry)-set(evaluation['use_classes'])), 9)
        for missing in set(registry)-set(evaluation['use_classes']):
            self.assertIn(missing, text.split('## 未対応')[1])

    def test_non_delegable_and_unknown_operations(self):
        registry = read('contracts/operation-registry.json')
        for op in ('message_send','profile_adopt','entity_merge','memory_erase','policy_grant'):
            result = decide(op, TrustedFacts(stage='enabled', live_use=True,
                delegation_matches=True, valid_confirmation=False), registry)
            self.assertEqual(result.outcome, 'require_confirmation', op)
        self.assertEqual(decide('unregistered', TrustedFacts(), registry).reason, 'UNSUPPORTED_OPERATION')

    def test_legacy_bypass_candidates_are_detected_without_app_import(self):
        repo = Path(os.environ['W30_REPO'])
        for file, fragment in (
            ('backend/app/api/task.py', '/{task_id}/accept'),
            ('backend/app/api/memory.py', '/proposals/{proposal_id}/accept'),
            ('backend/app/api/interaction.py', 'share_level'),
            ('backend/services/search/embedding.py', 'httpx.post'),
        ):
            source = (repo/file).read_text(encoding='utf-8-sig')
            ast.parse(source)
            self.assertIn(fragment, source, file)
        # Detection only: absence of a v3 Gate is not proved by a string search.
