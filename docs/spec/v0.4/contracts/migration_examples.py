"""Synthetic Source migration example, not an application migration adapter.

Source contract provenance is supplied by the trusted import path in a future
adapter, never authenticated by a model-provided version field or this helper.
"""
import copy
import hashlib
import json
from pathlib import Path
import zipfile
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def old_asset(relative):
    with zipfile.ZipFile(ROOT/'archive/v0.3-original.zip') as archive:
        return json.loads(archive.read('4-me-not-collab-v0.3/'+relative))


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode('utf-8')).hexdigest()


def convert_source_example(source, *, source_contract, target_contract=3):
    if source_contract != 2 or target_contract != 3:
        raise ValueError('EXPLICIT_V2_TO_V3_ONLY')
    if source.get('schema_version') != source_contract:
        raise ValueError('SOURCE_VERSION_MISMATCH')
    old = old_asset('contracts/memory.schema.json')
    new = json.loads((ROOT/'contracts/memory.schema.json').read_text(encoding='utf-8'))
    def validate(schema, value):
        Draft202012Validator({'$defs': schema['$defs'], '$ref':'#/$defs/Source'},
            format_checker=FormatChecker()).validate(value)
    validate(old, source)
    result = copy.deepcopy(source)
    result['schema_version'] = 3
    validate(new, result)
    original_content = {k:v for k,v in source.items() if k != 'schema_version'}
    migrated_content = {k:v for k,v in result.items() if k != 'schema_version'}
    if original_content != migrated_content:
        raise ValueError('IMMUTABLE_SOURCE_CHANGED')
    return result, {'converter':'w30-06-source-example-v1', 'source_contract':2,
        'target_contract':3, 'input_digest':digest(source), 'output_digest':digest(result),
        'preserved_content_digest':digest(original_content)}


def check_dependency_evidence_example(recorded_features, verified_features):
    """Reject unknown evidence; not a dependency traversal or permission grant."""
    if verified_features is None:
        raise ValueError('UNKNOWN_DEPENDENCIES_READ_ONLY')
    if set(recorded_features) != set(verified_features):
        raise ValueError('DEPENDENCY_MISMATCH')
