import copy
import json
import os
from pathlib import Path
import unittest
from backend.services.memory_contracts import ContractError, MemoryContracts
from backend.services.memory_features import FeatureRegistry
from backend.services.memory_revisions import MemoryRevisions
from backend.services.memory_storage import StorageContext
from backend.services.source_evidence import SourceEvidence
from backend.services.source_storage import SourceStorage
from storage_fakes import FakeAccess, FakeStorage
from test_source_storage import uid


class FakeDependencies:
    """Exact test oracle; no real closure computation or authorization."""
    def __init__(self):
        self.features = ()
        self.refs = set()

    def resolve(self, tx, context, content):
        for ref in content['additional_dependency_refs']:
            if (context.vault_id, ref['resource_type'],ref['object_id'],ref['version_id']) not in self.refs:
                return None
        return self.features


def revision_environment():
    root = Path(os.environ['MEMORY_SPEC_ROOT'])
    contracts = MemoryContracts(json.loads((root/'contracts/memory.schema.json').read_text(encoding='utf-8-sig')))
    fixtures = json.loads((root/'fixtures/valid.json').read_text(encoding='utf-8'))
    registry = FeatureRegistry(json.loads((root/'contracts/feature-registry.json').read_text(encoding='utf-8')))
    store, access, deps = FakeStorage(), FakeAccess(), FakeDependencies()
    context = StorageContext(uid(1),'synthetic-owner',uid(2))
    sources = SourceStorage(contracts,store,access=access,new_id=lambda:uid(10),
                            now=lambda:'2026-09-08T01:00:00+00:00')
    request = copy.deepcopy(fixtures['ImportRequest'])
    request['messages'] = [copy.deepcopy(fixtures['Source']['messages'][0])]
    receipt = sources.import_source(context,'synthetic-source-key',request,source_contract=3)
    source = sources.get_source(context,receipt['source_id'])
    quote = source['messages'][0]['text']
    evidence = {'source_id':source['source_id'],'message_id':source['messages'][0]['message_id'],'quote':quote}
    span = SourceEvidence(contracts,source,expected_vault=context.vault_id,source_contract=3).locate(evidence)['span']
    revision = copy.deepcopy(fixtures['MemoryRevision'])
    revision.update(revision_id=uid(32),item_id=uid(30),vault_id=context.vault_id,parent_revision_id=None)
    revision['content']['evidence'] = [evidence]
    revision['content']['epistemic_kind'] = 'ai_hypothesis'
    revision['evidence_spans'] = [span]
    revisions = MemoryRevisions(contracts,store,sources,registry,access=access,dependencies=deps)
    return store,access,deps,context,revisions,revision


class MemoryRevisionsTest(unittest.TestCase):
    def setUp(self):
        self.store,self.access,self.deps,self.context,self.revisions,self.value = revision_environment()

    def project(self,value=None,expected=None):
        # Local transaction participant only; actual Content Ledger coordinator is W31-04.
        with self.store.transaction() as tx:
            return self.revisions.project_in(tx,self.context,value or self.value,
                expected_current=expected,basis_head=uid(20))

    def test_auto_008_history_and_current_are_separate_and_origin_is_preserved(self):
        first = self.project()
        next_revision = copy.deepcopy(first)
        next_revision.update(revision_id=uid(33),parent_revision_id=first['revision_id'])
        next_revision['content']['text'] = '訂正後の仮説'
        self.project(next_revision,first['revision_id'])
        current = self.revisions.get_item(self.context,uid(30))
        self.assertEqual(current['current_revision']['revision_id'],uid(33))
        self.assertEqual(self.revisions.get_revision(self.context,uid(30),uid(32)),first)
        self.assertEqual(current['current_revision']['content']['epistemic_kind'],'ai_hypothesis')
        current['current_revision']['content']['text'] = '書換'
        self.assertNotEqual(self.revisions.get_item(self.context,uid(30)),current)

    def test_missing_current_cannot_reset_an_existing_chain(self):
        self.project()
        del self.store.data['memory_current'][(uid(1),uid(30))]
        with self.assertRaisesRegex(ContractError,'CURRENT_MISSING'):
            self.project({**self.value,'revision_id':uid(33)})

    def test_parent_current_and_item_reference_integrity(self):
        first = self.project()
        for changes,expected in [({'revision_id':uid(33),'parent_revision_id':uid(90)},uid(32)),
                                  ({'revision_id':uid(33),'parent_revision_id':uid(32),'item_id':uid(31)},uid(32))]:
            with self.assertRaises(ContractError): self.project({**first,**changes},expected)
        with self.assertRaises(ContractError): self.project(first)

    def test_missing_other_vault_missing_current_and_old_reference(self):
        first = self.project()
        for item,rev in [(uid(99),uid(32)),(uid(30),uid(99))]:
            with self.assertRaises(ContractError): self.revisions.get_revision(self.context,item,rev)
        other = StorageContext(uid(5),'synthetic-owner',uid(2))
        with self.assertRaises(ContractError): self.revisions.get_item(other,uid(30))
        del self.store.data['memory_current'][(uid(1),uid(30))]
        with self.assertRaises(ContractError): self.revisions.get_item(self.context,uid(30))
        self.assertEqual(self.revisions.get_revision(self.context,uid(30),uid(32)),first)

    def test_provisional_and_unconnected_approval_are_rejected(self):
        with self.assertRaises(ContractError): self.project({**self.value,'review_state':'provisional'})
        self.revisions.access = self.revisions.__class__(self.revisions.contracts,self.store,
            self.revisions.sources,self.revisions.registry).access
        with self.assertRaisesRegex(ContractError,'AUTHORIZATION_NOT_CONNECTED'): self.project()

    def test_auto_019_erasure_blocks_past_and_current(self):
        self.project()
        self.access.erased_items.add((uid(1),uid(30)))
        for call in (lambda:self.revisions.get_item(self.context,uid(30)),
                     lambda:self.revisions.get_revision(self.context,uid(30),uid(32))):
            with self.assertRaisesRegex(ContractError,'NOT_FOUND'): call()

    def test_evidence_mismatch_and_other_source_are_rejected(self):
        changed = copy.deepcopy(self.value)
        changed['evidence_spans'][0]['quote'] = '捏造'
        with self.assertRaises(ContractError): self.project(changed)
        changed = copy.deepcopy(self.value)
        changed['content']['evidence'][0]['source_id'] = uid(99)
        changed['evidence_spans'][0]['source_id'] = uid(99)
        with self.assertRaises(ContractError): self.project(changed)

    def test_additional_dependencies_missing_bad_or_unresolved(self):
        changed = copy.deepcopy(self.value)
        del changed['content']['additional_dependency_refs']
        with self.assertRaises(ContractError): self.project(changed)
        for ref in ({'resource_type':'invalid'}, {'resource_type':'evaluation','object_id':uid(70),'version_id':uid(71)}):
            changed = copy.deepcopy(self.value)
            changed['content']['additional_dependency_refs'] = [ref]
            with self.assertRaises(ContractError): self.project(changed)

    def test_dependency_marks_roundtrip_and_empty_self_claim_is_not_trusted(self):
        self.deps.features = ('prediction_loop',)
        with self.assertRaisesRegex(ContractError,'DEPENDENCY_FEATURE_MISMATCH'): self.project()
        self.value['required_features'] = ['prediction_loop']
        ref = {'resource_type':'evaluation','object_id':uid(70),'version_id':uid(71)}
        self.value['content']['additional_dependency_refs'] = [ref]
        self.deps.refs.add((uid(1),'evaluation',uid(70),uid(71)))
        self.project()
        read = self.revisions.get_item(self.context,uid(30))['current_revision']
        self.assertEqual(read['required_features'],['prediction_loop'])
        self.assertEqual(read['content']['additional_dependency_refs'],[ref])
        self.deps.refs.clear()
        with self.assertRaisesRegex(ContractError,'DEPENDENCIES_UNRESOLVED'):
            self.revisions.get_revision(self.context,uid(30),uid(32))

    def test_unconnected_dependency_port_holds_even_empty_claim(self):
        self.revisions.dependencies = self.revisions.__class__(self.revisions.contracts,self.store,
            self.revisions.sources,self.revisions.registry).dependencies
        with self.assertRaisesRegex(ContractError,'DEPENDENCIES_UNRESOLVED'): self.project()

    def test_current_update_failure_rolls_back_immutable_revision(self):
        before = copy.deepcopy(self.store.data)
        self.store.fail_at = 'cas:memory_current'
        with self.assertRaises(ContractError): self.project()
        self.assertEqual(before,self.store.data)
