# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.providers.rdap_admission import rdap_bootstrap_base_urls


def test_rdap_bootstrap_uses_longest_matching_dns_suffix() -> None:
    payload = {
        "services": [
            [["com"], ["https://rdap.tld.example/rdap/"]],
            [["example.com"], ["https://rdap.zone.example/rdap/"]],
            [["other.com"], ["https://rdap.other.example/rdap/"]],
        ]
    }

    assert rdap_bootstrap_base_urls(payload, domain="host.example.com") == (
        "https://rdap.zone.example/rdap/",
    )


def test_equal_longest_bootstrap_entries_are_combined_in_registry_order() -> None:
    payload = {
        "services": [
            [["example.com"], ["https://rdap-a.zone.example/"]],
            [["example.com"], ["https://rdap-b.zone.example/"]],
            [["com"], ["https://rdap.tld.example/"]],
        ]
    }

    assert rdap_bootstrap_base_urls(payload, domain="host.example.com") == (
        "https://rdap-a.zone.example/",
        "https://rdap-b.zone.example/",
    )
