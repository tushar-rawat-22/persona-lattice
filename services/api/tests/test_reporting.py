# SPDX-License-Identifier: Apache-2.0
from app.reporting import build_structured_report
from app.research import QuickObservation, QuickResearchReport, ResearchKind


def test_structured_username_report_keeps_full_evidence_out_of_projection() -> None:
    report = QuickResearchReport(
        kind=ResearchKind.USERNAME,
        normalized_value="synthetic-user",
        observations=(
            QuickObservation(
                source="github_public_api",
                source_locator="https://github.com/synthetic-user",
                summary="Synthetic public GitHub profile.",
                details={
                    "account_candidate": True,
                    "identity_claim": False,
                    "email": "public@example.test",
                    "twitter_username": "synthetic_social",
                    "blog": "https://example.test",
                    "location": "Example City",
                    "company": "Example Org",
                },
            ),
        ),
    )

    result = build_structured_report(report)
    summary = result["executive_summary"]
    assert result["report_version"] == "private-evidence-report-v2"
    assert summary["identity_probability"] is None
    assert summary["identity_claim"] is False
    assert summary["public_account_candidate_count"] == 1
    assert summary["connected_identifier_count"] == 5

    connected = result["connected_identifiers"]
    assert {item["kind"] for item in connected} == {
        "email",
        "username",
        "url",
        "location_claim",
        "organization_claim",
    }
    assert {item["observation_index"] for item in connected} == {0}
    assert {item["detail_field"] for item in connected} == {
        "email",
        "twitter_username",
        "blog",
        "location",
        "company",
    }
    assert all(item["status"] == "observed_public_field" for item in connected)
    assert all("value" not in item for item in connected)
    assert all("source" not in item for item in connected)
    assert all("source_locator" not in item for item in connected)
    assert result["public_account_candidate_observation_indexes"] == [0]
    assert result["contradiction_observation_indexes"] == []
    assert "source_evidence" not in result
    assert "public_account_candidates" not in result
    assert "contradictions" not in result
    assert "seed" not in result
    assert result["coverage_gaps"]


def test_structured_phone_report_refuses_subscriber_identity_inference() -> None:
    report = QuickResearchReport(
        kind=ResearchKind.PHONE,
        normalized_value="+919876543210",
        observations=(
            QuickObservation(
                source="libphonenumber_metadata",
                source_locator="local://libphonenumber",
                summary="Numbering-plan metadata; not subscriber identity.",
                details={
                    "country_code": 91,
                    "region": "India",
                    "personal_identity_claim": False,
                },
            ),
        ),
    )

    result = build_structured_report(report)
    assert result["executive_summary"]["identity_claim"] is False
    assert result["executive_summary"]["identity_probability"] is None
    assert any("subscriber" in gap.lower() for gap in result["coverage_gaps"])
    assert result["connected_identifiers"] == []
