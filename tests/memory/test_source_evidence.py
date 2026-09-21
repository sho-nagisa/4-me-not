import copy
import hashlib
import json
import os
from pathlib import Path
import unittest
from backend.services.memory_contracts import ContractError, MemoryContracts
from backend.services.source_evidence import SourceEvidence
from test_memory_features import forbidden_core_imports


class SourceEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(os.environ['MEMORY_SPEC_ROOT'])
        cls.contracts=MemoryContracts(json.loads((root/'contracts/memory.schema.json').read_text(encoding='utf-8-sig')))
        cls.template=json.loads((root/'fixtures/valid.json').read_text(encoding='utf-8'))['Source']

    def source(self,text='前置き 日本語🙂\r\nnext e\u0301 終わり'):
        source=copy.deepcopy(self.template)
        source['messages'][0]['text']=text
        return source

    def reader(self,source):
        return SourceEvidence(self.contracts,source,expected_vault=source['vault_id'],source_contract=3)

    def evidence(self,source,quote):
        return {'source_id':source['source_id'],'message_id':source['messages'][0]['message_id'],'quote':quote}

    def test_auto_001_multilingual_exact_utf8_roundtrip(self):
        source=self.source()
        reader=self.reader(source)
        quote='日本語🙂\r\nnext e\u0301'
        locator=reader.locate(self.evidence(source,quote))
        self.assertEqual(locator['span']['start_byte'],len('前置き '.encode('utf-8')))
        self.assertEqual(locator['span']['end_byte'],len(('前置き '+quote).encode('utf-8')))
        self.assertEqual(reader.verify_text_locator(locator),locator)
        self.assertEqual(reader.message_digest(source['source_id'],source['messages'][0]['message_id']),
            hashlib.sha256(source['messages'][0]['text'].encode('utf-8')).hexdigest())

    def test_zero_and_multiple_matches_including_overlaps(self):
        for raw, quote, error in [('猫と猫','猫','EVIDENCE_AMBIGUOUS'),('aaa','aa','EVIDENCE_AMBIGUOUS'),
                                 ('猫','犬','EVIDENCE_NOT_FOUND')]:
            source=self.source(raw)
            with self.assertRaisesRegex(ContractError,error): self.reader(source).locate(self.evidence(source,quote))

    def test_no_normalization_or_newline_replacement(self):
        source=self.source('e\u0301\r\n🙂')
        reader=self.reader(source)
        for quote in ('é','e\u0301\n'):
            with self.assertRaisesRegex(ContractError,'EVIDENCE_NOT_FOUND'):
                reader.locate(self.evidence(source,quote))
        self.assertEqual(reader.snapshot(),source)

    def test_composite_source_message_and_vault_boundary(self):
        source=self.source('同一の文')
        other=copy.deepcopy(source)
        other['source_id']='00000000-0000-4000-8000-000000000077'
        reader=self.reader(source)
        # Identical message IDs and text in two sources are valid, never interchangeable.
        self.reader(other).locate(self.evidence(other,'同一の文'))
        with self.assertRaisesRegex(ContractError,'SOURCE_MISMATCH'):
            reader.locate(self.evidence(other,'同一の文'))
        candidate=self.evidence(source,'同一の文')
        candidate['message_id']='00000000-0000-4000-8000-000000000078'
        with self.assertRaisesRegex(ContractError,'MESSAGE_NOT_IN_SOURCE'): reader.locate(candidate)
        with self.assertRaisesRegex(ContractError,'VAULT_MISMATCH'):
            SourceEvidence(self.contracts,source,expected_vault=other['source_id'],source_contract=3)
        source['messages'].append(copy.deepcopy(source['messages'][0]))
        with self.assertRaisesRegex(ContractError,'DUPLICATE_MESSAGE_ID'): self.reader(source)

    def test_invalid_byte_boundaries_ranges_and_quote(self):
        source=self.source('🙂猫')
        reader=self.reader(source)
        locator=reader.locate(self.evidence(source,'🙂'))
        for changes,error in [({'start_byte':1},'INVALID_UTF8_BOUNDARY'),
                ({'end_byte':3},'INVALID_UTF8_BOUNDARY'),({'end_byte':99},'INVALID_BYTE_RANGE'),
                ({'start_byte':4,'end_byte':4},'INVALID_BYTE_RANGE'),({'quote':'犬'},'EVIDENCE_QUOTE_MISMATCH')]:
            changed=copy.deepcopy(locator)
            changed['span'].update(changes)
            with self.assertRaisesRegex(ContractError,error): reader.verify_text_locator(changed)

    def test_explicit_selection_resolves_duplicate_without_picking_first(self):
        source=self.source('猫と猫')
        reader=self.reader(source)
        selected={'type':'text','span':{**self.evidence(source,'猫'),'start_byte':6,'end_byte':9}}
        self.assertEqual(reader.verify_text_locator(selected),selected)
        # This verifies the selected bytes, not that a human authorized the selection.

    def test_integral_json_offsets_and_nonintegral_rejection(self):
        source=self.source('🙂猫')
        reader=self.reader(source)
        selected={'type':'text','span':{**self.evidence(source,'猫'),'start_byte':4.0,'end_byte':7.0}}
        self.assertEqual(reader.verify_text_locator(selected),selected)
        for start in (4.5,True):
            selected['span']['start_byte']=start
            with self.assertRaises(ContractError): reader.verify_text_locator(selected)

    def test_contract_two_and_relabelled_source_are_rejected(self):
        source=self.source()
        with self.assertRaises(ContractError): self.reader({**source,'schema_version':2})
        with self.assertRaisesRegex(ContractError,'EXPLICIT_SOURCE_MIGRATION_REQUIRED'):
            SourceEvidence(self.contracts,source,expected_vault=source['vault_id'],source_contract=2)
        with self.assertRaises(ContractError): self.reader({**source,'owner':True})

    def test_media_union_shape_only_and_unknown_locator(self):
        reader=self.reader(self.source())
        asset='00000000-0000-4000-8000-000000000088'
        for locator in ({'type':'audio','asset_version_id':asset,'start_ms':0,'end_ms':20},
                {'type':'image','asset_version_id':asset,'region_xywh':[0,0,1,1]}):
            self.assertEqual(reader.validate_locator_shape(locator),locator)
            with self.assertRaisesRegex(ContractError,'MEDIA_RESOLUTION_NOT_IMPLEMENTED'):
                reader.verify_text_locator(locator)
        with self.assertRaises(ContractError): reader.validate_locator_shape({'type':'unknown'})

    def test_new_version_refs_are_shapes_not_media_or_existence_proof(self):
        source=self.source('独立した結果の原文')
        reader=self.reader(source)
        for kind in ('source','prediction','outcome','evaluation','assessment','feature_control','learning_manifest'):
            ref={'resource_type':kind,'object_id':source['source_id'],
                 'version_id':'00000000-0000-4000-8000-000000000088'}
            self.assertEqual(reader.validate_version_ref_shape(ref),ref)
        with self.assertRaises(ContractError): reader.validate_version_ref_shape({**ref,'resource_type':'video'})
        # Independent raw text requires no prediction port or derived record.
        self.assertEqual(reader.locate(self.evidence(source,'独立した結果の原文'))['span']['start_byte'],0)

    def test_auto_001_input_and_snapshot_mutations_do_not_change_raw(self):
        source=self.source()
        original=copy.deepcopy(source)
        reader=self.reader(source)
        source['messages'][0]['text']='変更'
        exported=reader.snapshot()
        exported['messages'][0]['text']='別の変更'
        self.assertEqual(reader.snapshot(),original)
        with self.assertRaises(ContractError): reader.locate(self.evidence(original,'不存在'))
        self.assertEqual(reader.snapshot(),original)

    def test_non_utf8_surrogate_is_rejected_without_raw_exception(self):
        with self.assertRaisesRegex(ContractError,'^INVALID_UTF8$'): self.reader(self.source('\ud800'))
        source=self.source()
        with self.assertRaisesRegex(ContractError,'^INVALID_UTF8$'):
            self.reader(source).locate(self.evidence(source,'\ud800'))

    def test_core_source_has_no_prediction_import(self):
        path=Path(__file__).resolve().parents[2]/'backend/services/source_evidence.py'
        self.assertEqual(forbidden_core_imports(path.read_text(encoding='utf-8')),[])
