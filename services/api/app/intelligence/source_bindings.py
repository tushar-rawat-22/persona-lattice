# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ..providers.base import ContactRisk, ProviderStatus
from ..providers.registry import PROVIDER_BY_NAME
from .contracts import LeadKind
from .source_catalog import SOURCE_BY_NAME, SourceStatus


class SourceExecutionBackend(StrEnum):
    """Existing execution boundary behind one current logical source."""

    LOCAL_DETERMINISTIC = "local_deterministic"
    M3_GOVERNED_ADAPTER = "m3_governed_adapter"
    LEGACY_RESEARCH = "legacy_research"


@dataclass(frozen=True, slots=True)
class SourceBinding:
    """Bridge from V2 capability metadata to existing runtime code.

    A binding is not permission to execute. It states which existing execution
    boundary currently owns a catalogued source so policy can reject drift before
    a source is invoked.
    """

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
        if (
            self.backend is not SourceExecutionBackend.M3_GOVERNED_ADAPTER
            and self.provider_name is not None
        ):
            raise ValueError("Only M3 governed-adapter bindings may declare provider_name.")


# These are migration bridges for private-V1 network behavior that still lives in
# research.py or its helpers. New V2 sources are forbidden from joining this set.
# They must use the governed provider boundary before activation.
_LEGACY_RESEARCH_ALLOWLIST = frozenset(
    {
        "github_public_api",
        "gitlab_public_api",
        "codeforces_public_api",
        "public_dns_infrastructure",
        "brave_public_web_index",
    }
)

_LOCAL_DETERMINISTIC_ALLOWLIST = frozenset(
    {
        "local_normalization",
        "libphonenumber_metadata",
    }
)


SOURCE_BINDINGS: tuple[SourceBinding, ...] = (
    SourceBinding(
        source_name="local_normalization",
        backend=SourceExecutionBackend.LOCAL_DETERMINISTIC,
        accepts=frozenset({LeadKind.EMAIL, LeadKind.URL}),
    ),
    SourceBinding(
        source_name="libphonenumber_metadata",
        backend=SourceExecutionBackend.LOCAL_DETERMINISTIC,
        accepts=frozenset({LeadKind.PHONE}),
    ),
    SourceBinding(
        source_name="sherlock",
        backend=SourceExecutionBackend.M3_GOVERNED_ADAPTER,
        provider_name="sherlock",
        accepts=frozenset({LeadKind.USERNAME}),
        migration_note=(
            "Sherlock already uses the M3 descriptor/policy/adapter contract in quick research; "
            "move final execution through ProviderExecutor during source-runtime unification."
        ),
    ),
    SourceBinding(
        source_name="github_public_api",
        backend=SourceExecutionBackend.LEGACY_RESEARCH,
        accepts=frozenset({LeadKind.USERNAME}),
        migration_note="Migrate the public-profile lookup into the governed provider runtime.",
    ),
    SourceBinding(
        source_name="gitlab_public_api",
        backend=SourceExecutionBackend.LEGACY_RESEARCH,
        accepts=frozenset({LeadKind.USERNAME, LeadKind.EMAIL}),
        migration_note=(
            "Migrate username and exact-public-email paths into the governed provider runtime."
        ),
    ),
    SourceBinding(
        source_name="codeforces_public_api",
        backend=SourceExecutionBackend.LEGACY_RESEARCH,
        accepts=frozenset({LeadKind.USERNAME}),
        migration_note="Migrate the public-profile lookup into the governed provider runtime.",
    ),
    SourceBinding(
        source_name="public_dns_infrastructure",
        backend=SourceExecutionBackend.LEGACY_RESEARCH,
        accepts=frozenset({LeadKind.URL, LeadKind.DOMAIN}),
        migration_note=(
            "Public DNS performs bounded network I/O and must be brought behind the same runtime "
            "admission model before new network metadata sources are added."
        ),
    ),
    SourceBinding(
        source_name="brave_public_web_index",
        backend=SourceExecutionBackend.LEGACY_RESEARCH,
        accepts=frozenset(
            {LeadKind.USERNAME, LeadKind.EMAIL, LeadKind.PHONE, LeadKind.URL}
        ),
        migration_note=(
            "Keep optional metered search behind one governed runtime before adding more search sources."
        ),
    ),
)


SOURCE_BINDING_BY_NAME = {binding.source_name: binding for binding in SOURCE_BINDINGS}
if len(SOURCE_BINDING_BY_NAME) != len(SOURCE_BINDINGS):
    raise RuntimeError("Source bindings contain duplicate logical source names.")


class SourceBindingError(RuntimeError):
    pass


def _validate_binding(binding: SourceBinding) -> None:
    capability = SOURCE_BY_NAME.get(binding.source_name)
    if capability is None:
        raise SourceBindingError(
            f"Binding {binding.source_name!r} has no source capability declaration."
        )
    if capability.status not in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}:
        raise SourceBindingError(
            f"Binding {binding.source_name!r} points at a non-current source status."
        )
    if not capability.source_policy_reviewed or not capability.recursive_eligible:
        raise SourceBindingError(
            f"Binding {binding.source_name!r} is not source-policy reviewed and recursive-eligible."
        )
    if binding.accepts != capability.accepts:
        raise SourceBindingError(
            f"Binding {binding.source_name!r} identifier kinds drift from the source catalog."
        )

    if binding.backend is SourceExecutionBackend.LOCAL_DETERMINISTIC:
        if binding.source_name not in _LOCAL_DETERMINISTIC_ALLOWLIST:
            raise SourceBindingError(
                f"Source {binding.source_name!r} is not approved for local deterministic execution."
            )
        return

    if binding.backend is SourceExecutionBackend.LEGACY_RESEARCH:
        if binding.source_name not in _LEGACY_RESEARCH_ALLOWLIST:
            raise SourceBindingError(
                f"Source {binding.source_name!r} cannot expand the legacy research boundary."
            )
        if not binding.migration_note.strip():
            raise SourceBindingError("Legacy research bindings require an explicit migration note.")
        return

    assert binding.backend is SourceExecutionBackend.M3_GOVERNED_ADAPTER
    assert binding.provider_name is not None
    descriptor = PROVIDER_BY_NAME.get(binding.provider_name)
    if descriptor is None:
        raise SourceBindingError(
            f"M3 provider {binding.provider_name!r} is missing from the provider registry."
        )
    if descriptor.status != ProviderStatus.DEVELOPMENT.value:
        raise SourceBindingError(
            f"M3 provider {binding.provider_name!r} is not in the reviewed development status."
        )
    if descriptor.contact_risk is not ContactRisk.NONE_KNOWN:
        raise SourceBindingError(
            f"M3 provider {binding.provider_name!r} has contact risk and cannot be a silent recursive binding."
        )
    if not descriptor.allowed_purposes:
        raise SourceBindingError(
            f"M3 provider {binding.provider_name!r} has no allowed purposes."
        )
    try:
        descriptor_kinds = frozenset(
            LeadKind(kind) for kind in descriptor.supported_identifier_kinds
        )
    except ValueError as exc:
        raise SourceBindingError(
            f"M3 provider {binding.provider_name!r} declares an unknown lead kind."
        ) from exc
    if descriptor_kinds != binding.accepts:
        raise SourceBindingError(
            f"M3 provider {binding.provider_name!r} identifier kinds drift from the V2 binding."
        )


def validate_source_bindings() -> None:
    """Fail closed if catalog, migration bindings and M3 provider policy drift."""

    for binding in SOURCE_BINDINGS:
        _validate_binding(binding)

    required_current_sources = {
        source.name
        for source in SOURCE_BY_NAME.values()
        if source.status in {SourceStatus.ACTIVE, SourceStatus.OPTIONAL}
        and source.source_policy_reviewed
        and source.recursive_eligible
    }
    bound_sources = set(SOURCE_BINDING_BY_NAME)
    if bound_sources != required_current_sources:
        missing = sorted(required_current_sources - bound_sources)
        extra = sorted(bound_sources - required_current_sources)
        raise SourceBindingError(
            "Current recursive source bindings are incomplete or excessive: "
            f"missing={missing!r}, extra={extra!r}."
        )


def source_binding_for(
    source_name: str,
    *,
    kind: LeadKind | None = None,
) -> SourceBinding:
    """Return a validated current binding; never upgrades planned/deferred sources."""

    validate_source_bindings()
    binding = SOURCE_BINDING_BY_NAME.get(source_name)
    if binding is None:
        raise SourceBindingError(f"Source {source_name!r} has no executable runtime binding.")
    if kind is not None and kind not in binding.accepts:
        raise SourceBindingError(
            f"Source {source_name!r} is not bound for {kind.value!r} leads."
        )
    return binding


# Import-time validation turns accidental catalog/provider/binding drift into a
# deterministic startup/test failure rather than a surprise during research.
validate_source_bindings()
