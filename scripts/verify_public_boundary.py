#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


TIMEOUT_SECONDS = 10.0
MAX_BODY_BYTES = 64 * 1024


class VerificationFailure(RuntimeError):
    pass


def _base_url(raw: str) -> str:
    value = raw.strip().rstrip("/")
    parts = urlsplit(value)
    if not parts.hostname or parts.query or parts.fragment or parts.username or parts.password:
        raise VerificationFailure("Base URL must be a plain site origin.")
    local = parts.hostname in {"127.0.0.1", "localhost", "::1"}
    if parts.scheme != "https" and not (local and parts.scheme == "http"):
        raise VerificationFailure("Hosted verification requires an HTTPS origin.")
    if parts.path not in {"", "/"}:
        raise VerificationFailure("Base URL must not include a path.")
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def _request(base: str, path: str) -> tuple[int, dict[str, str], bytes]:
    request = Request(
        f"{base}{path}",
        headers={"User-Agent": "PersonaLattice-V1-Boundary-Verifier/1"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(MAX_BODY_BYTES + 1)
            status = response.status
            headers = {key.lower(): value for key, value in response.headers.items()}
    except HTTPError as exc:
        body = exc.read(MAX_BODY_BYTES + 1)
        status = exc.code
        headers = {key.lower(): value for key, value in exc.headers.items()}
    except (URLError, TimeoutError) as exc:
        raise VerificationFailure(f"Request failed for {path}: {type(exc).__name__}.") from exc

    if len(body) > MAX_BODY_BYTES:
        raise VerificationFailure(f"Response for {path} exceeded the verification body limit.")
    return status, headers, body


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationFailure(message)


def _verify_public_shell(base: str) -> None:
    status, headers, body = _request(base, "/")
    _require(status == 200, f"Public shell returned HTTP {status}, expected 200.")
    _require(bool(body), "Public shell returned an empty body.")

    required_headers = {
        "content-security-policy",
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "permissions-policy",
        "strict-transport-security",
    }
    missing = sorted(required_headers - headers.keys())
    _require(not missing, f"Public shell is missing security headers: {', '.join(missing)}.")


def _verify_private_get(base: str, path: str) -> None:
    status, headers, body = _request(base, path)
    _require(status == 401, f"Anonymous {path} returned HTTP {status}, expected 401.")
    _require(headers.get("cache-control") == "no-store", f"Anonymous {path} is not no-store.")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationFailure(f"Anonymous {path} did not return bounded JSON.") from exc

    _require(payload == {"detail": "Admin authentication required."}, f"Anonymous {path} returned unexpected data.")


def verify(base: str) -> None:
    _verify_public_shell(base)
    for path in ("/api/v1/auth/session", "/api/v1/cases", "/api/v1/audit"):
        _verify_private_get(base, path)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 scripts/verify_public_boundary.py https://your-site.example", file=sys.stderr)
        return 2

    try:
        base = _base_url(argv[1])
        verify(base)
    except VerificationFailure as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: public shell is reachable and anonymous private reads remain denied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
