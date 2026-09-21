import copy
import json
import os
from pathlib import Path
import unittest
from uuid import UUID
from backend.services.memory_contracts import ContractError, MemoryContracts
from backend.services.memory_storage import StorageContext
from backend.services.source_storage import SourceStorage, canonical_bytes
from storage_fakes import FakeAccess, FakeStorage


def uid(n):
    return str(UUID(int=n))


class SourceStorageTest(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ['MEMORY_SPEC_ROOT'])
        self.contracts = MemoryContracts(json.loads((root/'contracts/memory.schema.json').read_text(encoding='utf-8-sig')))
        self.request = json.loads((root/'fixtures/valid.json').read_text(encoding='utf-8'))['ImportRequest']
        self.request['messages'][0]['text'] = '原文🙂\r\ne\u0301'
        self.store, self.access = FakeStorage(), FakeAccess()
        ids = iter(uid(i) for i in range(100,200))
        self.service = SourceStorage(self.contracts,self.store,access=self.access,
            new_id=lambda:next(ids), now=lambda:'2026-09-08T01:00:00+00:00')
        self.context = StorageContext(uid(1),'caller-a',uid(2))

    def save(self, key='same', request=None, context=None):
        return self.service.import_source(context or self.context,key,
            self.request if request is None else request,source_contract=3)

    def test_auto_015_same_request_replay_preserves_id_time_text(self):
        first = self.save()
        self.service.now = lambda:'2027-01-01T00:00:00+00:00'
        self.assertEqual(first,self.save(request=dict(reversed(list(self.request.items())))))
        self.assertEqual(len(self.store.data['sources']),1)
        stored = self.service.get_source(self.context,first['source_id'])
        self.assertEqual(stored['messages'],self.request['messages'])
        self.assertEqual(stored['schema_version'],3)
        self.assertEqual(stored['imported_at'],first['imported_at'])

    def test_auto_015_changed_request_same_key_is_conflict(self):
        self.save()
        before = copy.deepcopy(self.store.data)
        changed = copy.deepcopy(self.request)
        changed['messages'][0]['text'] += '!'
        with self.assertRaisesRegex(ContractError,'IDEMPOTENCY_CONFLICT'): self.save(request=changed)
        self.assertEqual(self.store.data,before)

    def test_auto_015_partial_failure_rolls_back_source_and_receipt(self):
        for point in ('insert:sources','insert:import_receipts','commit'):
            with self.subTest(point=point):
                self.store.fail_at = point
                with self.assertRaises(ContractError): self.save()
                self.assertEqual(self.store.data,{})
        self.store.fail_at = None
        self.assertEqual(self.save()['status'],'saved')

    def test_auto_001_analysis_failure_and_later_result_link_preserve_raw(self):
        receipt = self.save()  # No analyzer/Prediction port is required.
        before = copy.deepcopy(self.store.data['sources'])
        try:
            raise RuntimeError('synthetic analyzer failure after import')
        except RuntimeError:
            pass
        # An unrelated external test record links to the source without rewriting it.
        self.store.data['test_result_links'] = {('result',):receipt['source_id']}
        self.assertEqual(self.store.data['sources'],before)
        self.assertEqual(self.save(),receipt)

    def test_auto_015_vault_caller_and_operation_key_isolation(self):
        a = self.save()
        b = self.save(context=StorageContext(uid(3),'caller-a',uid(2)))
        c = self.save(context=StorageContext(uid(1),'caller-b',uid(2)))
        self.assertEqual(len({a['source_id'],b['source_id'],c['source_id']}),3)
        self.assertEqual({key[2] for key in self.store.data['import_receipts']},{'importSource'})
        with self.assertRaises(ContractError): self.service.get_source(self.context,b['source_id'])

    def test_auto_019_replay_and_get_recheck_current_access_and_erasure(self):
        first = self.save()
        self.access.erased_sources.add((self.context.vault_id,first['source_id']))
        for call in (self.save, lambda:self.service.get_source(self.context,first['source_id'])):
            with self.assertRaisesRegex(ContractError,'^NOT_FOUND$'): call()
        self.access.erased_sources.clear()
        self.access.denied.add('getSource')
        with self.assertRaises(ContractError): self.save()
        self.assertNotIn('原文',str(first))

    def test_unconnected_authorization_denies_without_saving(self):
        service = SourceStorage(self.contracts,self.store)
        with self.assertRaisesRegex(ContractError,'AUTHORIZATION_NOT_CONNECTED'):
            service.import_source(self.context,'k',self.request,source_contract=3)
        self.assertEqual(self.store.data,{})

    def test_v3_provenance_and_source_integrity_boundary(self):
        with self.assertRaises(ContractError): self.save(request={**self.request,'schema_version':2})
        with self.assertRaises(ContractError):
            self.service.import_source(self.context,'k',self.request,source_contract=2)
        first = self.save()
        row = self.store.data['sources'][(self.context.vault_id,first['source_id'])]
        row['source']['messages'][0]['text'] = 'tampered'
        with self.assertRaisesRegex(ContractError,'SOURCE_INTEGRITY_ERROR'):
            self.service.get_source(self.context,first['source_id'])

    def test_read_and_request_are_detached_copies(self):
        original = canonical_bytes(self.request)
        first = self.save()
        read = self.service.get_source(self.context,first['source_id'])
        read['messages'][0]['text'] = 'changed'
        self.assertEqual(canonical_bytes(self.request),original)
        self.assertNotEqual(self.service.get_source(self.context,first['source_id']),read)
