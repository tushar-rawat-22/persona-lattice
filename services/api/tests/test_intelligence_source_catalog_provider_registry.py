# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.registry import PROVIDER_BY_NAME


def test_existing_non_synthetic_provider_registry_entries_are_catalogued() -> None:
    expected = set(PROVIDER_BY_NAME).difference({"synthetic_echo"})
    assert expected.issubset(SOURCE_BY_NAME)


def test_deferred_provider_registry_entries_are_not_recursive_sources() -> None:
    for name in (
        "numverify",
        "abstract_phone_intelligence",
        "ipqualityscore",
        "maigret",
        "whatsmyname",
        "truecaller_manual",
        "phoneinfoga",
    ):
        source = SOURCE_BY_NAME[name]
        assert source.recursive_eligible is False
        assert source.status in {
            SourceStatus.REVIEW_REQUIRED,
            SourceStatus.PLANNED,
            SourceStatus.MANUAL_ONLY,
            SourceStatus.REFERENCE_ONLY,
        }


def test_sherlock_is_the_only_governed_registry_provider_currently_recursive() -> None:
    recursive_registry_sources = {
        name
        for name in PROVIDER_BY_NAME
        if name in SOURCE_BY_NAME and SOURCE_BY_NAME[name].recursive_eligible
    }
    assert recursive_registry_sources == {"sherlock"}
