"""Contract-3 source boundary and exact text locations. No storage or permission."""
import copy
from hashlib import sha256
from uuid import UUID
from backend.services.memory_contracts import ContractError, MemoryContracts


def _uuid(value):
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError):
        raise ContractError('INVALID_ID') from None


def _utf8(text):
    try:
        return text.encode('utf-8')
    except UnicodeEncodeError:
        raise ContractError('INVALID_UTF8') from None


class SourceEvidence:
    def __init__(self, contracts: MemoryContracts, source, *, expected_vault, source_contract):
        # These coordinates must come from a trusted adapter, never an AI DTO.
        if type(source_contract) is not int or source_contract != 3:
            raise ContractError('EXPLICIT_SOURCE_MIGRATION_REQUIRED')
        self._contracts = contracts
        self._source = contracts.validate('Source',source)
        if _uuid(self._source['vault_id']) != _uuid(expected_vault):
            raise ContractError('VAULT_MISMATCH')
        self._messages = {}
        self._raw = {}
        for message in self._source['messages']:
            identifier = _uuid(message['message_id'])
            if identifier in self._messages:
                raise ContractError('DUPLICATE_MESSAGE_ID')
            self._messages[identifier] = message
            self._raw[identifier] = _utf8(message['text'])

    def snapshot(self):
        return copy.deepcopy(self._source)

    def _message(self, source_id, message_id):
        if _uuid(source_id) != _uuid(self._source['source_id']):
            raise ContractError('SOURCE_MISMATCH')
        identifier = _uuid(message_id)
        if identifier not in self._messages:
            raise ContractError('MESSAGE_NOT_IN_SOURCE')
        return self._messages[identifier], self._raw[identifier]

    def message_digest(self, source_id, message_id):
        _, raw = self._message(source_id,message_id)
        return sha256(raw).hexdigest()

    def locate(self, evidence):
        candidate = self._contracts.validate('EvidenceInput',evidence)
        message, raw = self._message(candidate['source_id'],candidate['message_id'])
        quote = _utf8(candidate['quote'])
        start = raw.find(quote)
        if start < 0:
            raise ContractError('EVIDENCE_NOT_FOUND')
        if raw.find(quote,start+1) >= 0:  # Includes overlapping occurrences.
            raise ContractError('EVIDENCE_AMBIGUOUS')
        return self.verify_text_locator({'type':'text','span':{
            'source_id':self._source['source_id'],'message_id':message['message_id'],
            'quote':candidate['quote'],'start_byte':start,'end_byte':start+len(quote)}})

    def validate_locator_shape(self, locator):
        # Audio/image are shape-only unions: W39 owns media existence and ranges.
        return self._contracts.validate('EvidenceLocator',locator)

    def verify_text_locator(self, locator):
        value = self.validate_locator_shape(locator)
        if value['type'] != 'text':
            raise ContractError('MEDIA_RESOLUTION_NOT_IMPLEMENTED')
        span = value['span']
        _, raw = self._message(span['source_id'],span['message_id'])
        # JSON Schema integers include integral JSON numbers (for example 4.0).
        start, end = int(span['start_byte']), int(span['end_byte'])
        if not 0 <= start < end <= len(raw):
            raise ContractError('INVALID_BYTE_RANGE')
        try:
            raw[:start].decode('utf-8')
            raw[start:end].decode('utf-8')
        except UnicodeDecodeError:
            raise ContractError('INVALID_UTF8_BOUNDARY') from None
        if raw[start:end] != _utf8(span['quote']):
            raise ContractError('EVIDENCE_QUOTE_MISMATCH')
        return value  # Exact bytes only; no semantic support, adoption or permission.

    def validate_version_ref_shape(self, reference):
        return self._contracts.validate('VersionRef',reference)
