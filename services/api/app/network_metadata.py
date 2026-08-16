# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
import ipaddress
import socket


_MAX_PUBLIC_IPS = 8


def _resolve_public_ips_sync(hostname: str) -> tuple[str, ...]:
    compact = hostname.strip().rstrip(".").lower()
    if not compact or len(compact) > 253:
        return ()

    try:
        literal = ipaddress.ip_address(compact)
    except ValueError:
        literal = None
    if literal is not None:
        return (literal.compressed,) if literal.is_global else ()

    try:
        rows = socket.getaddrinfo(
            compact,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        return ()

    addresses: list[str] = []
    seen: set[str] = set()
    for _family, _socktype, _proto, _canonname, sockaddr in rows:
        raw = sockaddr[0]
        try:
            parsed = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if not parsed.is_global:
            continue
        value = parsed.compressed
        if value in seen:
            continue
        seen.add(value)
        addresses.append(value)
        if len(addresses) >= _MAX_PUBLIC_IPS:
            break
    return tuple(addresses)


async def resolve_public_host_ips(hostname: str) -> tuple[str, ...]:
    """Resolve globally reachable website/domain infrastructure addresses only.

    These addresses describe public network infrastructure for the hostname. They
    are not evidence of a person's device IP or physical location.
    """

    return await asyncio.to_thread(_resolve_public_ips_sync, hostname)
