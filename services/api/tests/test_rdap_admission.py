# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.extractor import extract_observation_leads
from app.intelligence.source_bindings import SourceBindingError, source_binding_for
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.rdap_admission import (
    RdapAdmissionError,
    admitted_rdap_domain_observation,
    normalize_rdap_domain,
    rdap_bootstrap_base_urls,
    rdap_domain_query_url,
)


def test_domain_normalization_is_bare_dns_only_and_idna_stable() -> None:
    assert normalize_rdap_domain("Example.COM.").domain == "example.com"
    assert normalize_rdap_domain("Bücher.example").domain == "xn--bcher-kva.example"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "localhost",
        "example.local",
        "https://example.com",
        "user@example.com",
        "example.com/path",
        "127.0.0.1",
        "::1",
        "exa mple.com",
    ],
)
def test_domain_normalization_rejects_non_public_or_non_domain_inputs(value: str) -> None:
    with pytest.raises(RdapAdmissionError):
        normalize_rdap_domain(value)


def test_iana_style_bootstrap_selects_only_matching_tld_https_services() -> None:
    payload = {
        "services": [
            [["net"], ["https://rdap.example.net/"]],
            [["com", "example"], ["https://rdap.registry.example/rdap/"]],
        ]
    }
    assert rdap_bootstrap_base_urls(payload, domain="Example.COM") == (
        "https://rdap.registry.example/rdap/",
    )


def test_bootstrap_rejects_unsafe_or_missing_service_urls() -> None:
    with pytest.raises(RdapAdmissionError):
        rdap_bootstrap_base_urls(
            {"services": [[["com"], ["http://rdap.example.com/"]]]},
            domain="example.com",
        )
    with pytest.raises(RdapAdmissionError, match="no authoritative service"):
        rdap_bootstrap_base_urls(
            {"services": [[["net"], ["https://rdap.example.net/"]]]},
            domain="example.com",
        )


def test_domain_query_url_uses_rfc9082_domain_path() -> None:
    assert rdap_domain_query_url(
        "https://rdap.registry.example/rdap",
        domain="Example.COM",
    ) == "https://rdap.registry.example/rdap/domain/example.com"


def test_admitted_observation_retains_only_low_sensitivity_registration_context() -> None:
    locator = "https://rdap.registry.example/rdap/domain/example.com"
    observation = admitted_rdap_domain_observation(
        {
            "objectClassName": "domain",
            "ldhName": "EXAMPLE.COM",
            "status": ["active"],
            "nameservers": [
                {"ldhName": "NS1.EXAMPLE.NET"},
                {"ldhName": "ns1.example.net"},
            ],
            "entities": [
                {
                    "roles": ["registrant"],
                    "vcardArray": [
                        "vcard",
                        [
                            ["fn", {}, "text", "Private Person"],
                            ["org", {}, "text", "Private Org"],
                            ["email", {}, "text", "private@example.com"],
                            ["tel", {}, "text", "+1-202-555-0100"],
                            ["adr", {}, "text", "Private Address"],
                        ],
                    ],
                },
                {
                    "roles": ["registrar"],
                    "vcardArray": ["vcard", [["fn", {}, "text", "Registrar Inc"]]],
                },
            ],
            "remarks": [{"title": "Data Policy", "description": ["redacted"]}],
        },
        requested_domain="example.com",
        source_locator=locator,
    )
    assert observation.source_locator == locator
    assert observation.details == {
        "domain": "example.com",
        "statuses": ("active",),
        "nameservers": ("ns1.example.net",),
        "registration_context": True,
        "identity_claim": False,
        "registrant_contact_retained": False,
        "redaction_authoritative": True,
    }
    retained = repr(observation.details)
    for sensitive_value in (
        "Private Person",
        "Private Org",
        "private@example.com",
        "+1-202-555-0100",
        "Private Address",
        "Registrar Inc",
    ):
        assert sensitive_value not in retained

    leads = extract_observation_leads(
        details=observation.details,
        source="rdap_domain_registry",
        source_locator=observation.source_locator,
    )
    assert leads.candidates == ()
    assert leads.blocked_field_names == ()


def test_response_must_match_requested_domain_and_canonical_locator() -> None:
    with pytest.raises(RdapAdmissionError, match="does not match"):
        admitted_rdap_domain_observation(
            {"objectClassName": "domain", "ldhName": "mallory.com"},
            requested_domain="example.com",
            source_locator="https://rdap.registry.example/rdap/domain/example.com",
        )
    with pytest.raises(RdapAdmissionError, match="source locator"):
        admitted_rdap_domain_observation(
            {"objectClassName": "domain", "ldhName": "example.com"},
            requested_domain="example.com",
            source_locator="https://rdap.registry.example/rdap/domain/mallory.com",
        )


def test_rdap_is_metadata_only_planned_and_unbound() -> None:
    source = SOURCE_BY_NAME["rdap_domain_registry"]
    assert source.status is SourceStatus.PLANNED
    assert source.source_policy_reviewed is False
    assert source.recursive_eligible is False
    assert source.emits == frozenset()
    with pytest.raises(SourceBindingError, match="no executable runtime binding"):
        source_binding_for("rdap_domain_registry")
