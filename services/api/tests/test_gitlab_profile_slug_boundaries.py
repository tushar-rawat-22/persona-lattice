# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.providers.gitlab_public import gitlab_profile_username_from_url


def test_gitlab_profile_slug_length_boundaries_are_fail_closed() -> None:
    assert gitlab_profile_username_from_url("https://gitlab.com/a") is None
    assert gitlab_profile_username_from_url(f"https://gitlab.com/{'a' * 255}") == "a" * 255
    assert gitlab_profile_username_from_url(f"https://gitlab.com/{'a' * 256}") is None
