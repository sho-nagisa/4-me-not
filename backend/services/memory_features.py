"""Registry structure and optional composition ports, never runtime permission."""
from dataclasses import dataclass
from typing import Mapping, Protocol
from backend.services.memory_contracts import ContractError, MemoryContracts


@dataclass(frozen=True)
class Feature:
    feature_id: str
    tier: str
    decision_status: str
    implementation_status: str
    default_control: str
    default_stage: str
    depends_on: tuple[str, ...]


class FeatureRegistry:
    def __init__(self, rows):
        self._features = {}
        if not isinstance(rows, list) or not rows:
            raise ContractError('INVALID_REGISTRY')
        for row in rows:
            if not isinstance(row, dict):
                raise ContractError('INVALID_FEATURE')
            names = ('feature_id','tier','decision_status','implementation_status','default_control','default_stage')
            if any(not isinstance(row.get(n), str) or not row[n] for n in names):
                raise ContractError('INVALID_FEATURE')
            deps = row.get('depends_on')
            if not isinstance(deps, list) or any(not isinstance(d,str) for d in deps) or len(set(deps))!=len(deps):
                raise ContractError('INVALID_DEPENDENCIES')
            feature = Feature(**{n:row[n] for n in names}, depends_on=tuple(deps))
            if feature.feature_id in self._features:
                raise ContractError('DUPLICATE_FEATURE')
            if feature.tier not in ('core','experimental','evaluation_only'):
                raise ContractError('UNKNOWN_TIER')
            if feature.decision_status not in ('agreed-direction','adopted-for-design',
                    'accepted-experimental','candidate','evaluation-plan','reference_only'):
                raise ContractError('UNKNOWN_DECISION_STATUS')
            if feature.default_control not in ('enabled','disabled') or feature.default_stage not in (
                    'shadow','internal','presentation','enabled'):
                raise ContractError('INVALID_DEFAULT_STATE')
            if feature.tier != 'core' and (feature.default_control,feature.default_stage)!=('disabled','shadow'):
                raise ContractError('EXTENSION_DEFAULT_MUST_BE_OFF')
            if feature.decision_status=='candidate' and (feature.default_control,feature.default_stage)!=('disabled','shadow'):
                raise ContractError('CANDIDATE_MUST_NOT_BE_LIVE')
            self._features[feature.feature_id] = feature
        for feature in self._features.values():
            for dependency in feature.depends_on:
                target = self.get(dependency)
                if feature.tier=='core' and target.tier!='core':
                    raise ContractError('CORE_REQUIRES_EXTENSION')
        visited, visiting = set(), set()
        def visit(identifier):
            if identifier in visiting:
                raise ContractError('FEATURE_CYCLE')
            if identifier in visited:
                return
            visiting.add(identifier)
            for dependency in self.get(identifier).depends_on:
                visit(dependency)
            visiting.remove(identifier)
            visited.add(identifier)
        for identifier in self._features:
            visit(identifier)

    def get(self, feature_id):
        if not isinstance(feature_id, str) or feature_id not in self._features:
            raise ContractError('UNKNOWN_FEATURE')
        return self._features[feature_id]

    def features(self):
        return tuple(self._features.values())

    def check_live_classification(self, feature_id):
        """Negative classification check only. Success grants no use permission."""
        feature = self.get(feature_id)
        if feature.tier=='evaluation_only' or feature.decision_status=='candidate':
            raise ContractError('CLASSIFICATION_NOT_LIVE')

    def validate_control_view(self, contracts: MemoryContracts, value):
        view = contracts.validate('FeatureControlView',value)
        self.get(view['feature_id'])
        return view  # Shape only: no state mutation, auth, promotion or epoch lookup.


class OptionalFeaturePort(Protocol):
    """Implemented by an extension, injected by a future trusted adapter."""
    def evaluate(self, candidate: Mapping) -> Mapping: ...


class CoreComposition:
    def __init__(self, registry: FeatureRegistry, extensions: Mapping[str, OptionalFeaturePort] | None = None):
        self.registry = registry
        self._extensions = dict(extensions or {})
        for identifier in self._extensions:
            if registry.get(identifier).tier == 'core':
                raise ContractError('CORE_IS_NOT_AN_OPTIONAL_EXTENSION')

    def has_extension(self, feature_id):
        self.registry.get(feature_id)
        return feature_id in self._extensions

    # No method invokes ports or enables features. Runtime control/Gate is W42-02+.
