# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..providers.base import ContactRisk, ProviderStatus
from ..providers.registry import PROVIDER_BY_NAME
from .contracts import LeadKind
from .source_catalog import SOURCE_BY_NAME, SourceStatus


class SourceExecutionBackend(StrEnum):
    LOCAL_DETERMINISTIC = "local_deterministic"
    M3_GOVERNED_ADAPTER = "m3_governed_adapter"
    LEGACY_RESEARCH = "legacy_research"


@dataclass(frozen=True, slots=True)
class SourceBinding:
    source_name: str
    backend: SourceExecutionBackend
    accepts: frozenset[LeadKind]
    provider_name: str | None = None
    migration_note: str = ""

    def __post_init__(self) -> None:
        if not self.source_name or self.source_name.strip() != self.source_name:
            raise ValueError("Source binding name must be non-empty and trimmed.")
        if not self.accepts:
            raise ValueError("Source binding must declare at least one accepted lead kind.")
        if self.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER and not self.provider_name:
            raise ValueError("M3 governed-adapter bindings require provider_name.")
        if self.backend is not SourceExecutionBackend.M3_GOVERNED_ADAPTER and self.provider_name is not None:
            raise ValueError("Only M3 governed-adapter bindings may declare provider_name.")


_LEGACY_RESEARCH_ALLOWLIST = frozenset()
_LOCAL_DETERMINISTIC_ALLOWLIST = frozenset({"local_normalization", "libphonenumber_metadata"})

SOURCE_BINDINGS: tuple[SourceBinding, ...] = (
    SourceBinding("local_normalization", SourceExecutionBackend.LOCAL_DETERMINISTIC, frozenset({LeadKind.EMAIL, LeadKind.URL})),
    SourceBinding("libphonenumber_metadata", SourceExecutionBackend.LOCAL_DETERMINISTIC, frozenset({LeadKind.PHONE})),
    SourceBinding("sherlock", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.USERNAME}), "sherlock", "Quick research executes Sherlock through the shared M3 ProviderRuntime."),
    SourceBinding("github_public_api", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.USERNAME}), "github_public_api", "Quick research executes GitHub public-profile lookup through ProviderRuntime."),
    SourceBinding("gitlab_public_api", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.USERNAME, LeadKind.EMAIL}), "gitlab_public_api", "Username and exact-public-email lookups execute through ProviderRuntime."),
    SourceBinding("codeforces_public_api", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.USERNAME}), "codeforces_public_api", "Public user.info lookup executes through the shared ProviderRuntime."),
    SourceBinding("bluesky_public_profile", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.USERNAME}), "bluesky_public_profile", "Valid AT handles execute through the shared ProviderRuntime; ordinary usernames are filtered before provider execution."),
    SourceBinding("public_dns_infrastructure", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.URL}), "public_dns_infrastructure", "Public URL hostname resolution executes through the shared ProviderRuntime."),
    SourceBinding("rdap_domain_registry", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.DOMAIN}), "rdap_domain_registry", "Explicit DOMAIN seeds execute metadata-only authoritative RDAP through ProviderRuntime; discovered domains remain display-only."),
    SourceBinding("brave_public_web_index", SourceExecutionBackend.M3_GOVERNED_ADAPTER, frozenset({LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.PHONE, LeadKind.URL}), "brave_public_web_index", "Optional exact-match search executes through ProviderRuntime when configured."),
)

SOURCE_BINDING_BY_NAME = {binding.source_name: binding for binding in SOURCE_BINDINGS}
if len(SOURCE_BINDING_BY_NAME) != len(SOURCE_BINDINGS):
    raise RuntimeError("Source bindings contain duplicate logical source names.")


class SourceBindingError(RuntimeError):
    pass


def _validate_binding(binding: SourceBinding) -> None:
    capability = SOURCE_BY_NAME.get(binding.source_name)
    if capability is None:
        raise SourceBindingError(f"Binding {binding.source_name!r} has no source capability declaration.")
    if capability.status not in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}:
        raise SourceBindingError(f"Binding {binding.source_name!r} points at a non-current source status.")
    if not capability.source_policy_reviewed or not capability.recursive_eligible:
        raise SourceBindingError(f"Binding {binding.source_name!r} is not source-policy reviewed and recursive-eligible.")
    if not binding.accepts.issubset(capability.accepts):
        raise SourceBindingError(f"Binding {binding.source_name!r} claims lead kinds absent from the source catalog.")
    if binding.backend is SourceExecutionBackend.LOCAL_DETERMINISTIC:
        if binding.source_name not in _LOCAL_DETERMINISTIC_ALLOWLIST:
            raise SourceBindingError(f"Source {binding.source_name!r} is not approved for local deterministic execution.")
        return
    if binding.backend is SourceExecutionBackend.LEGACY_RESEARCH:
        if binding.source_name not in _LEGACY_RESEARCH_ALLOWLIST:
            raise SourceBindingError(f"Source {binding.source_name!r} cannot expand the legacy research boundary.")
        if not binding.migration_note.strip():
            raise SourceBindingError("Legacy research bindings require an explicit migration note.")
        return
    assert binding.provider_name is not None
    descriptor = PROVIDER_BY_NAME.get(binding.provider_name)
    if descriptor is None:
        raise SourceBindingError(f"M3 provider {binding.provider_name!r} is missing from the provider registry.")
    if descriptor.status != ProviderStatus.DEVELOPMENT.value:
        raise SourceBindingError(f"M3 provider {binding.provider_name!r} is not in the reviewed development status.")
    if descriptor.contact_risk is not ContactRisk.NONE_KNOWN:
        raise SourceBindingError(f"M3 provider {binding.provider_name!r} has contact risk and cannot be a silent recursive binding.")
    if not descriptor.allowed_purposes:
        raise SourceBindingError(f"M3 provider {binding.provider_name!r} has no allowed purposes.")
    try:
        descriptor_kinds = frozenset(LeadKind(kind) for kind in descriptor.supported_identifier_kinds)
    except ValueError as exc:
        raise SourceBindingError(f"M3 provider {binding.provider_name!r} declares an unknown lead kind.") from exc
    if descriptor_kinds != binding.accepts:
        raise SourceBindingError(f"M3 provider {binding.provider_name!r} identifier kinds drift from the V2 binding.")


def validate_source_bindings() -> None:
    for binding in SOURCE_BINDINGS:
        _validate_binding(binding)
    required_current_sources = {
        source.name for source in SOURCE_BY_NAME.values()
        if source.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        and source.source_policy_reviewed and source.recursive_eligible
    }
    bound_sources = set(SOURCE_BINDING_BY_NAME)
    if bound_sources != required_current_sources:
        missing = sorted(required_current_sources - bound_sources)
        extra = sorted(bound_sources - required_current_sources)
        raise SourceBindingError(f"Current recursive source bindings are incomplete or excessive: missing={missing!r}, extra={extra!r}.")


def source_binding_for(source_name: str, *, kind: LeadKind | None = None) -> SourceBinding:
    validate_source_bindings()
    binding = SOURCE_BINDING_BY_NAME.get(source_name)
    if binding is None:
        raise SourceBindingError(f"Source {source_name!r} has no executable runtime binding.")
    if kind is not None and kind not in binding.accepts:
        raise SourceBindingError(f"Source {source_name!r} is not currently bound for {kind.value!r} leads.")
    return binding


validate_source_bindings()
