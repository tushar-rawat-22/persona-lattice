# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass

from .research import QuickResearchReport


CONNECTED_IDENTIFIER_FIELD_BY_KIND = {
    "email": "email",
    "username": "twitter_username",
    "url": "blog",
    "location_claim": "location",
    "organization_claim": "company",
}


@dataclass(frozen=True, slots=True)
class ConnectedIdentifierReference:
    kind: str
    observation_index: int
    detail_field: str
    status: str = "observed_public_field"


def _text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _connected_identifiers(report: QuickResearchReport) -> list[dict[str, object]]:
    connected: list[ConnectedIdentifierReference] = []
    seen: set[tuple[str, str]] = set()

    for observation_index, observation in enumerate(report.observations):
        details = observation.details
        for kind, detail_field in CONNECTED_IDENTIFIER_FIELD_BY_KIND.items():
            value = _text(details.get(detail_field))
            if value is None:
                continue
            key = (kind, value.casefold())
            if key in seen:
                continue
            seen.add(key)
            connected.append(
                ConnectedIdentifierReference(
                    kind=kind,
                    observation_index=observation_index,
                    detail_field=detail_field,
                )
            )

    return [
        {
            "kind": item.kind,
            "observation_index": item.observation_index,
            "detail_field": item.detail_field,
            "status": item.status,
        }
        for item in connected
    ]


def _coverage_gaps(report: QuickResearchReport) -> list[str]:
    gaps: list[str] = []
    if report.kind.value == "username":
        gaps.extend(
            [
                "Same-handle accounts are candidates, not proof that the same person controls them.",
                "Private profiles, private messages and non-public account data are not queried.",
            ]
        )
    elif report.kind.value == "phone":
        gaps.extend(
            [
                "No subscriber name or connected account is inferred from numbering metadata.",
                "A public-source search provider is still required to discover attributable web mentions of this number.",
            ]
        )
    elif report.kind.value == "email":
        gaps.extend(
            [
                "No person is inferred to own the email without an attributable public or authorized source.",
                "External public-web email mention discovery is not enabled without an approved provider.",
            ]
        )
    elif report.kind.value == "url":
        gaps.extend(
            [
                "The target URL is not fetched yet; only canonical URL metadata is recorded.",
                "Remote-page retrieval requires the hardened SSRF-safe web-fetch boundary before activation.",
            ]
        )
    return gaps


def build_structured_report(report: QuickResearchReport) -> dict[str, object]:
    connected = _connected_identifiers(report)
    public_account_indexes = [
        index
        for index, observation in enumerate(report.observations)
        if observation.details.get("account_candidate") is True
    ]
    contradiction_indexes = [
        index
        for index, observation in enumerate(report.observations)
        if observation.details.get("contradiction") is True
        or observation.details.get("account_state") == "illegal"
    ]
    source_names = sorted({observation.source for observation in report.observations})

    return {
        "report_version": "private-evidence-report-v2",
        "executive_summary": {
            "observation_count": len(report.observations),
            "source_count": len(source_names),
            "sources": source_names,
            "connected_identifier_count": len(connected),
            "public_account_candidate_count": len(public_account_indexes),
            "identity_probability": None,
            "identity_claim": False,
            "interpretation": "Evidence report only. PersonaLattice does not assert that candidate accounts belong to the same person without corroborating evidence.",
        },
        # Canonical observations own connected-field values and provider provenance. This index
        # retains only the exact field and observation reference needed for operator navigation.
        "connected_identifiers": connected,
        "public_account_candidate_observation_indexes": public_account_indexes,
        "contradiction_observation_indexes": contradiction_indexes,
        "coverage_gaps": _coverage_gaps(report),
        "provenance_rule": "Provider observations are the canonical retained evidence. Structured report sections reference canonical observations instead of copying their values or provider provenance.",
    }
