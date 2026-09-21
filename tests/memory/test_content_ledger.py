import copy
import ast
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import unittest
from backend.services.content_ledger import ContentLedger
from backend.services.memory_contracts import ContractError
from backend.services.memory_storage import StorageContext
from storage_fakes import FakeStorage
from test_memory_revisions import revision_environment
from test_source_storage import uid


class FakeInvalidation:
    """Test transaction participant, not actual dependency traversal or stop propagation."""
    def apply(self, tx, context, revision):
        tx.insert('test_invalidation', (context.vault_id,revision['revision_id']), {'barrier':'synthetic'})
        return ()


class ContentLedgerTest(unittest.TestCase):
    def setUp(self):
        self.store,self.access,self.deps,self.context,self.revisions,self.value = revision_environment()
        ids = iter(uid(i) for i in range(200,300))
        self.ledger = ContentLedger(self.revisions.contracts,self.store,self.revisions,
            access=self.access,invalidation=FakeInvalidation(),new_id=lambda:next(ids),
            now=lambda:'2026-09-08T02:00:00+00:00')
        self.snapshot = {'content_head':uid(20),'derivation_generation':7,'policy_version':uid(2),
                         'erasure_epoch':3,'learner_version':None,'feature_epoch':11}
        self.ledger.initialize(self.context,self.snapshot)

    def commit(self,value=None,head=None,current=None,key='synthetic-commit-key'):
        return self.ledger.commit(self.context,key,value or self.value,
            expected_head=head or uid(20),expected_current=current)

    def test_atomic_commit_revision_current_receipt_and_snapshot_roundtrip(self):
        before_sources = copy.deepcopy(self.store.data['sources'])
        receipt = self.commit()
        self.revisions.contracts.validate('CommitReceipt',receipt)
        expected = {**self.snapshot,'content_head':receipt['commit_id']}
        self.assertEqual(self.ledger.get_snapshot(self.context),expected)
        commit = self.ledger.get_commit(self.context,receipt['commit_id'])
        self.assertEqual(commit['parent_head'],uid(20))
        self.assertEqual(commit['snapshot'],expected)
        self.assertEqual(self.ledger.get_item(self.context,uid(30))['basis_head'],receipt['commit_id'])
        self.assertEqual(before_sources,self.store.data['sources'])

    def test_auto_015_identical_replay_and_different_plan_conflict(self):
        first = self.commit()
        before = copy.deepcopy(self.store.data)
        self.assertEqual(self.commit(),first)
        self.assertEqual(self.store.data,before)
        changed = copy.deepcopy(self.value)
        changed['content']['text'] = '変更'
        with self.assertRaisesRegex(ContractError,'IDEMPOTENCY_CONFLICT'): self.commit(changed)

    def test_same_head_two_concurrent_commits_only_one_succeeds(self):
        barrier = Barrier(2)
        def contender(n):
            value = copy.deepcopy(self.value)
            value.update(item_id=uid(30+n),revision_id=uid(40+n))
            barrier.wait(timeout=5)
            try:
                return ('ok',self.commit(value,key='concurrent-key-'+str(n)))
            except ContractError as error:
                return ('error',str(error))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(contender,[0,1]))
        self.assertEqual(sum(r[0]=='ok' for r in results),1)
        self.assertEqual([r[1] for r in results if r[0]=='error'],['HEAD_CONFLICT'])
        self.assertEqual(len(self.store.data['content_commits']),2)  # genesis + one
        self.assertEqual(len(self.store.data['memory_revisions']),1)

    def test_rollback_at_every_write_boundary_and_commit_failure(self):
        original = copy.deepcopy(self.store.data)
        points = ('insert:memory_items','insert:memory_revisions','cas:memory_current',
                  'insert:test_invalidation','insert:content_commits',
                  'cas:content_snapshots','insert:content_receipts','commit')
        for point in points:
            with self.subTest(point=point):
                self.store.fail_at = point
                with self.assertRaisesRegex(ContractError,'INJECTED_STORAGE_FAILURE'): self.commit()
                self.assertEqual(self.store.data,original)

    def test_invalid_parent_missing_head_and_self_parent_fail(self):
        with self.assertRaisesRegex(ContractError,'HEAD_CONFLICT'): self.commit(head=uid(99))
        self.ledger.new_id = lambda:uid(20)
        with self.assertRaisesRegex(ContractError,'INVALID_COMMIT_PARENT'): self.commit()
        del self.store.data['content_commits'][(uid(1),uid(20))]
        with self.assertRaisesRegex(ContractError,'INVALID_COMMIT_PARENT'): self.commit()

    def test_auto_032_unrelated_derivation_and_operation_leave_head_unchanged(self):
        with self.store.transaction() as tx:
            tx.insert('test_derivation_log',(uid(1),uid(80)),{'candidate':'synthetic'})
            tx.insert('test_operation_log',(uid(1),uid(81)),{'operation':'synthetic'})
        self.assertEqual(self.ledger.get_snapshot(self.context),self.snapshot)
        self.assertEqual(self.commit()['parent_head'],self.snapshot['content_head'])

    def test_feature_epoch_is_preserved_and_is_not_content_head(self):
        # Simulate an independent epoch update; no FeatureControl implementation.
        with self.store.transaction() as tx:
            tx.compare_exchange('content_snapshots',(uid(1),),self.snapshot,
                                {**self.snapshot,'feature_epoch':12})
        first = self.commit()  # expected HEAD unchanged despite unrelated coordinate.
        self.assertEqual(self.ledger.get_snapshot(self.context)['feature_epoch'],12)
        self.assertEqual(first['parent_head'],uid(20))
        root = self.ledger.get_commit(self.context,uid(20))
        self.assertEqual(root['snapshot']['feature_epoch'],11)  # historic snapshot is immutable

    def test_partial_snapshot_and_double_initialization_are_rejected(self):
        partial = {**self.snapshot}
        del partial['feature_epoch']
        with self.assertRaises(ContractError): self.ledger.initialize(self.context,partial)
        with self.assertRaises(ContractError): self.ledger.initialize(self.context,self.snapshot)
        self.store.data['content_snapshots'][(uid(1),)] = partial
        with self.assertRaises(ContractError): self.commit()

    def test_auto_019_erasure_rejects_commit_history_and_receipt_replay(self):
        first = self.commit()
        self.access.erased_items.add((uid(1),uid(30)))
        for call in (self.commit,lambda:self.ledger.get_commit(self.context,first['commit_id']),
                     lambda:self.ledger.get_item(self.context,uid(30))):
            with self.assertRaisesRegex(ContractError,'NOT_FOUND'): call()

    def test_unconnected_authorization_and_invalidation_abort(self):
        ledger = ContentLedger(self.revisions.contracts,self.store,self.revisions)
        before = copy.deepcopy(self.store.data)
        with self.assertRaisesRegex(ContractError,'AUTHORIZATION_NOT_CONNECTED'):
            ledger.commit(self.context,'k',self.value,expected_head=uid(20),expected_current=None)
        ledger = ContentLedger(self.revisions.contracts,self.store,self.revisions,access=self.access)
        with self.assertRaisesRegex(ContractError,'INVALIDATION_NOT_CONNECTED'):
            ledger.commit(self.context,'k',self.value,expected_head=uid(20),expected_current=None)
        self.assertEqual(self.store.data,before)

    def test_current_item_uses_latest_vault_head_but_keeps_its_revision(self):
        first = self.commit()
        second_item = {**copy.deepcopy(self.value),'item_id':uid(31),'revision_id':uid(33)}
        second = self.commit(second_item,head=first['commit_id'],key='second-item-key')
        view = self.ledger.get_item(self.context,uid(30))
        self.assertEqual(view['basis_head'],second['commit_id'])
        self.assertEqual(view['current_revision']['revision_id'],first['revision_id'])
        self.store.data['memory_current'][(uid(1),uid(30))]['basis_head'] = uid(20)
        with self.assertRaisesRegex(ContractError,'CURRENT_COMMIT_MISMATCH'):
            self.ledger.get_item(self.context,uid(30))

    def test_other_vault_and_mismatched_transaction_port_rejected(self):
        other = StorageContext(uid(9),'synthetic-owner',uid(2))
        with self.assertRaises(ContractError): self.ledger.get_snapshot(other)
        with self.assertRaisesRegex(ContractError,'TRANSACTION_PORT_MISMATCH'):
            ContentLedger(self.revisions.contracts,FakeStorage(),self.revisions)

    def test_revision_parent_chain_is_atomic_with_ledger_parent_chain(self):
        first = self.commit()
        changed = copy.deepcopy(self.value)
        changed.update(revision_id=uid(33),parent_revision_id=first['revision_id'])
        changed['content']['text'] = '訂正版'
        before = copy.deepcopy(self.store.data)
        self.store.fail_at = 'cas:content_snapshots'
        with self.assertRaises(ContractError):
            self.commit(changed,head=first['commit_id'],current=first['revision_id'],key='correction-key')
        self.assertEqual(before,self.store.data)
        self.store.fail_at = None
        second = self.commit(changed,head=first['commit_id'],current=first['revision_id'],key='correction-key')
        self.assertEqual(second['parent_head'],first['commit_id'])
        self.assertEqual(self.ledger.get_item(self.context,uid(30))['current_revision']['parent_revision_id'],first['revision_id'])
        self.assertEqual(self.revisions.get_revision(self.context,uid(30),uid(32)),self.value)

    def test_new_storage_modules_never_import_fake_db_or_prediction(self):
        root = Path(__file__).resolve().parents[2]/'backend/services'
        for name in ('memory_storage','source_storage','memory_revisions','content_ledger'):
            for node in ast.walk(ast.parse((root/f'{name}.py').read_text(encoding='utf-8'))):
                modules = [alias.name for alias in node.names] if isinstance(node,ast.Import) else (
                    [node.module or ''] if isinstance(node,ast.ImportFrom) else [])
                for module in modules:
                    self.assertFalse(any(part in module for part in ('prediction','storage_fakes','tests.',
                        'backend.db','backend.models','backend.app','memory_service')))
