"""W30-04 local type boundary. No Gate, authentication, receipt or execution.

CallerFields is an adapter output contract, NOT a capability. Python code can
construct it: production must restrict its construction to a verified adapter.
There is intentionally no JSON-to-authenticated-caller factory here.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Mapping
from uuid import UUID

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
MEMORY = json.loads((ROOT / "contracts/memory.schema.json").read_text(encoding="utf-8"))
BOUNDARY = json.loads((ROOT / "contracts/authority-boundary.schema.json").read_text(encoding="utf-8"))
OPERATIONS = json.loads((ROOT / "contracts/operation-registry.json").read_text(encoding="utf-8"))
RESOURCES = Registry().with_resources([
    (s["$id"], Resource.from_contents(s)) for s in (MEMORY, BOUNDARY)
])
ACTOR_KIND = {"owner": "user", "model": "model", "system": "rule", "importer": "importer"}


def validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(
        {"$ref": BOUNDARY["$id"] + "#/$defs/" + name},
        registry=RESOURCES, format_checker=FormatChecker())


@dataclass(frozen=True)
class CallerFields:
    role: str
    id: str
    vault_id: str

    def __post_init__(self):
        validator("CallerFields").validate(asdict(self))


def check_actor_binding(caller: CallerFields, audit_actor: Mapping) -> None:
    """Compare an operation's audit actor, never a Source speaker/claimant.

    Identity mapping must already be resolved by the adapter. This comparison
    does not assume existing account IDs equal Actor IDs or vault IDs.
    """
    if type(caller) is not CallerFields:
        raise TypeError("CALLER_ADAPTER_REQUIRED")
    validator("AuditActor").validate(audit_actor)
    if (audit_actor["kind"] != ACTOR_KIND[caller.role]
            or UUID(audit_actor["id"]) != UUID(caller.id)):
        raise ValueError("ACTOR_BINDING_MISMATCH")


def required_authorities(*, caller: CallerFields, candidate: Mapping,
                         vault_id: str) -> frozenset[str]:
    """Validate separate inputs and return requirements, NEVER granted rights.

    Does not decide actor eligibility, consent, risk, receipt validity or allow.
    Those use-site checks remain the responsibility of the future Gate.
    """
    if type(caller) is not CallerFields:
        raise TypeError("CALLER_ADAPTER_REQUIRED")
    if UUID(caller.vault_id) != UUID(vault_id):
        raise ValueError("VAULT_MISMATCH")
    validator("CandidateRequest").validate(candidate)
    values = OPERATIONS[candidate["operation"]]["authorities"]
    validator("AuthoritySet").validate(values)
    return frozenset(values)


def check_required_set(operation: str, values: list[str]) -> None:
    """Check registry completeness of a reported requirement set, not a grant."""
    validator("AuthoritySet").validate(values)
    if operation not in OPERATIONS:
        raise ValueError("UNKNOWN_OPERATION")
    if set(values) != set(OPERATIONS[operation]["authorities"]):
        raise ValueError("REQUIRED_AUTHORITIES_MISMATCH")
