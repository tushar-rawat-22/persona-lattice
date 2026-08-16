# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from app.network_metadata import _resolve_public_ips_sync


def test_literal_public_ip_is_returned_as_infrastructure() -> None:
    assert _resolve_public_ips_sync("8.8.8.8") == ("8.8.8.8",)


def test_private_loopback_and_link_local_literals_are_rejected() -> None:
    assert _resolve_public_ips_sync("127.0.0.1") == ()
    assert _resolve_public_ips_sync("10.0.0.1") == ()
    assert _resolve_public_ips_sync("169.254.169.254") == ()
    assert _resolve_public_ips_sync("::1") == ()
