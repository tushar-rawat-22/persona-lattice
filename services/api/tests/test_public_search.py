# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.public_search import _decode_results, _exact_query


def test_exact_query_quotes_identifier_and_strips_embedded_quotes() -> None:
    assert _exact_query('  user"name  ') == '"username"'


def test_decode_results_bounds_and_deduplicates_public_urls() -> None:
    payload = {
        "web": {
            "results": [
                {
                    "title": "First",
                    "url": "https://Example.com/profile#fragment",
                    "description": "Public mention",
                },
                {
                    "title": "Duplicate",
                    "url": "https://example.com/profile",
                    "description": "Duplicate URL",
                },
                {
                    "title": "Credentials are rejected",
                    "url": "https://user:pass@example.com/private",
                    "description": "bad",
                },
                {
                    "title": "Non-web scheme rejected",
                    "url": "file:///etc/passwd",
                    "description": "bad",
                },
            ]
        }
    }

    results = _decode_results(payload)
    assert len(results) == 1
    assert results[0].url == "https://example.com/profile"
    assert results[0].title == "First"


def test_decode_results_accepts_empty_web_results() -> None:
    assert _decode_results({"web": {"results": []}}) == ()
    assert _decode_results({}) == ()
