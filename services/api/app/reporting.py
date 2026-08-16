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
    source_evidence = [
        {
            "source": observation.source,
            "source_locator": observation.source_locator,
            "summary": observation.summary,
            "details": dict(observation.details),
        }
        for observation in report.observations
    ]
    public_accounts = [
        item
        for item in source_evidence
        if item["details"].get("account_candidate") is True
    ]
    contradictions = [
        item
        for item in source_evidence
        if item["details"].get("contradiction") is True
        or item["details"].get("account_state") == "illegal"
    ]
    connected = _connected_identifiers(report)
    source_names = sorted({observation.source for observation in report.observations})

    return {
        "report_version": "private-evidence-report-v1",
        "seed": {
            "kind": report.kind.value,
            "normalized_value": report.normalized_value,
        },
        "executive_summary": {
            "observation_count": len(report.observations),
            "source_count": len(source_names),
            "sources": source_names,
            "connected_identifier_count": len(connected),
            "public_account_candidate_count": len(public_accounts),
            "identity_probability": None,
            "identity_claim": False,
            "interpretation": "Evidence report only. PersonaLattice does not assert that candidate accounts belong to the same person without corroborating evidence.",
        },
        "connected_identifiers": connected,
        "public_account_candidates": public_accounts,
        "contradictions": contradictions,
        "source_evidence": source_evidence,
        "warnings": list(report.warnings),
        "coverage_gaps": _coverage_gaps(report),
        "provenance_rule": "Every displayed fact must remain attributable to its source locator; absent evidence is reported as unknown rather than inferred.",
    }
