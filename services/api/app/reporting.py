# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass

from .research import QuickResearchReport


@dataclass(frozen=True, slots=True)
class ConnectedIdentifier:
    kind: str
    value: str
    source: str
    source_locator: str
    status: str = "observed_public_field"


def _text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _connected_identifiers(report: QuickResearchReport) -> list[dict[str, str]]:
    connected: list[ConnectedIdentifier] = []
    seen: set[tuple[str, str]] = set()

    for observation in report.observations:
        details = observation.details
        candidates = (
            ("email", details.get("email")),
            ("username", details.get("twitter_username")),
            ("url", details.get("blog")),
            ("location_claim", details.get("location")),
            ("organization_claim", details.get("company")),
        )
        for kind, raw in candidates:
            value = _text(raw)
            if value is None:
                continue
            key = (kind, value.casefold())
            if key in seen:
                continue
            seen.add(key)
            connected.append(
                ConnectedIdentifier(
                    kind=kind,
                    value=value,
                    source=observation.source,
                    source_locator=observation.source_locator,
                )
            )

    return [
        {
            "kind": item.kind,
            "value": item.value,
            "source": item.source,
            "source_locator": item.source_locator,
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
        # This is a deliberately small operator index. It duplicates only the exact public fields
        # selected for cross-source navigation; full provider payloads remain owned by observations.
        "connected_identifiers": connected,
        "public_account_candidate_observation_indexes": public_account_indexes,
        "contradiction_observation_indexes": contradiction_indexes,
        "coverage_gaps": _coverage_gaps(report),
        "provenance_rule": "Provider observations are the canonical retained evidence. Structured report sections must not copy complete observation payloads.",
    }
