"""Local contracts. Caller supplies the reviewed schema; no DB or Gate imports."""
import copy
from jsonschema import Draft202012Validator, FormatChecker


class ContractError(ValueError):
    """Safe code-only error: do not echo raw source or candidate text."""


class MemoryContracts:
    def __init__(self, schema):
        Draft202012Validator.check_schema(schema)
        self._schema = copy.deepcopy(schema)

    def validate(self, name, value):
        if name not in self._schema['$defs']:
            raise ContractError('UNKNOWN_CONTRACT')
        validator = Draft202012Validator(
            {'$defs': self._schema['$defs'], '$ref': '#/$defs/'+name},
            format_checker=FormatChecker())
        if not validator.is_valid(value):
            raise ContractError('INVALID_'+name)
        return copy.deepcopy(value)
