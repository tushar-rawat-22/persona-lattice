# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import pytest

from app.intelligence.source_bindings import SourceBindingError, source_binding_for
from app.intelligence.source_catalog import SOURCE_BY_NAME, SourceStatus
from app.providers.webfinger_admission import (
    WebFingerAdmissionError,
    admitted_webfinger_links,
    webfinger_request_target,
)


def test_explicit_profile_url_builds_same_host_https_webfinger_request() -> None:
    target = webfinger_request_target("https://mastodon.social/@Gargron")
    assert target.resource == "https://mastodon.social/@Gargron"
    assert target.hostname == "mastodon.social"
    assert target.endpoint == (
        "https://mastodon.social/.well-known/webfinger?"
        "resource=https%3A%2F%2Fmastodon.social%2F%40Gargron"
    )


@pytest.mark.parametrize(
    "profile_url",
    [
        "http://social.example/@alice",
        "https://localhost/@alice",
        "https://social.local/@alice",
        "https://127.0.0.1/@alice",
        "https://[::1]/@alice",
        "https://bad_label.social.example/@alice",
        "https://user@social.example/@alice",
        "https://social.example:8443/@alice",
        "https://social.example/",
        "https://social.example/.well-known/webfinger",
        "https://social.example/@alice?tracking=1",
        "https://social.example/@alice#fragment",
    ],
)
def test_request_target_rejects_unsafe_or_ambiguous_profile_urls(profile_url: str) -> None:
    with pytest.raises(WebFingerAdmissionError):
        webfinger_request_target(profile_url)


def test_jrd_must_be_anchored_to_explicit_requested_profile() -> None:
    with pytest.raises(WebFingerAdmissionError, match="not anchored"):
        admitted_webfinger_links(
            {
                "subject": "acct:mallory@social.example",
                "aliases": ["https://social.example/@mallory"],
                "links": [],
            },
            requested_resource="https://social.example/@alice",
        )


def test_jrd_admits_only_reviewed_https_profile_and_actor_links() -> None:
    result = admitted_webfinger_links(
        {
            "subject": "acct:alice@social.example",
            "aliases": ["https://social.example/@alice"],
            "links": [
                {
                    "rel": "http://webfinger.net/rel/profile-page",
                    "type": "text/html",
                    "href": "https://social.example/@alice",
                },
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": "https://social.example/users/alice",
                },
                {
                    "rel": "http://ostatus.org/schema/1.0/subscribe",
                    "template": "https://social.example/authorize_interaction?uri={uri}",
                },
            ],
        },
        requested_resource="https://social.example/@alice",
    )
    assert result == (
        "https://social.example/@alice",
        "https://social.example/users/alice",
    )


def test_jrd_does_not_turn_subject_into_generic_username_or_name_fields() -> None:
    result = admitted_webfinger_links(
        {
            "subject": "acct:alice@social.example",
            "aliases": ["https://social.example/@alice"],
            "properties": {"https://example.invalid/display-name": "Alice"},
            "links": [],
        },
        requested_resource="https://social.example/@alice",
    )
    assert result == ()


@pytest.mark.parametrize(
    "href",
    [
        "http://social.example/users/alice",
        "https://127.0.0.1/users/alice",
        "https://bad_label.social.example/users/alice",
        "https://user@social.example/users/alice",
        "https://social.example:8443/users/alice",
        "https://social.example/users/alice?tracking=1",
        "https://social.example/users/alice#fragment",
    ],
)
def test_admitted_link_rejects_unsafe_locator(href: str) -> None:
    with pytest.raises(WebFingerAdmissionError):
        admitted_webfinger_links(
            {
                "subject": "https://social.example/@alice",
                "links": [{"rel": "self", "href": href}],
            },
            requested_resource="https://social.example/@alice",
        )


def test_webfinger_remains_planned_and_unbound_after_preflight() -> None:
    source = SOURCE_BY_NAME["webfinger_activitypub"]
    assert source.status is SourceStatus.PLANNED
    assert source.source_policy_reviewed is False
    assert source.recursive_eligible is False
    with pytest.raises(SourceBindingError, match="no executable runtime binding"):
        source_binding_for("webfinger_activitypub")
