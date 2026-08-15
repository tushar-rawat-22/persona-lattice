# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import resources
import json
import os
import sys
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

from .base import ProviderObservationData, ProviderQuery, ProviderResult
from .errors import ProviderExecutionError, ProviderValidationError
from .registry import PROVIDER_BY_NAME

SHERLOCK_UPSTREAM_VERSION = "0.16.0"
SHERLOCK_SITE_ALLOWLIST = (
    "BitBucket",
    "Codeberg",
    "Codeforces",
    "GitHub",
    "GitLab",
    "Kaggle",
    "Keybase",
    "Replit.com",
)
MAX_SHERLOCK_SITES = len(SHERLOCK_SITE_ALLOWLIST)
MAX_DIAGNOSTIC_CHARS = 256
MAX_WORKER_OUTPUT_BYTES = 128 * 1024


class AccountDiscoveryState(str, Enum):
    CLAIMED = "claimed"
    AVAILABLE = "available"
    UNKNOWN = "unknown"
    ILLEGAL = "illegal"
    WAF = "waf"


@dataclass(frozen=True, slots=True)
class SherlockResult:
    site_name: str
    state: AccountDiscoveryState
    profile_url: str | None
    http_status: int | None
    diagnostic: str | None
    detection_method: str


Worker = Callable[[str, tuple[str, ...], float], Awaitable[list[SherlockResult]]]


def _canonical_public_url(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parts = urlsplit(value.strip())
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            return None
        if parts.username or parts.password:
            return None
        port = parts.port
    except ValueError:
        return None

    hostname = parts.hostname.lower()
    if port is not None and not (
        (parts.scheme.lower() == "https" and port == 443)
        or (parts.scheme.lower() == "http" and port == 80)
    ):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname
    return urlunsplit((parts.scheme.lower(), netloc, parts.path, parts.query, ""))


def _bounded_diagnostic(value: object) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split())
    if not text:
        return None
    return text[:MAX_DIAGNOSTIC_CHARS]


def load_reviewed_sherlock_sites() -> dict[str, dict[str, Any]]:
    """Validate and load the reviewed allowlist from Sherlock's pinned package data."""
    try:
        from sherlock_project import __version__ as installed_version

        if installed_version != SHERLOCK_UPSTREAM_VERSION:
            raise ProviderValidationError(
                "Installed Sherlock version does not match the reviewed version."
            )
        resource = (
            resources.files("sherlock_project")
            .joinpath("resources")
            .joinpath("data.json")
        )
        raw = json.loads(resource.read_text(encoding="utf-8"))
    except ProviderValidationError:
        raise
    except Exception as exc:
        raise ProviderValidationError("Pinned Sherlock site data could not be loaded.") from exc

    if not isinstance(raw, dict):
        raise ProviderValidationError("Pinned Sherlock site data has an invalid shape.")

    selected: dict[str, dict[str, Any]] = {}
    for site_name in SHERLOCK_SITE_ALLOWLIST:
        entry = raw.get(site_name)
        if not isinstance(entry, dict):
            raise ProviderValidationError(
                f"Reviewed Sherlock site is missing from the pinned dataset: {site_name}."
            )
        if entry.get("isNSFW"):
            raise ProviderValidationError("NSFW Sherlock sites are not allowed.")
        if not isinstance(entry.get("url"), str) or not isinstance(entry.get("errorType"), str):
            raise ProviderValidationError("Reviewed Sherlock site metadata is incomplete.")
        selected[site_name] = dict(entry)

    if len(selected) != MAX_SHERLOCK_SITES:
        raise ProviderValidationError("Sherlock site budget does not match the reviewed allowlist.")
    return selected


def _normalize_site_names(site_names: Sequence[str]) -> tuple[str, ...]:
    selected = tuple(site_names)
    if not selected or len(selected) > MAX_SHERLOCK_SITES:
        raise ProviderValidationError("Sherlock site selection exceeds the configured budget.")
    if len(set(selected)) != len(selected):
        raise ProviderValidationError("Sherlock site selection contains duplicates.")
    unknown = set(selected).difference(SHERLOCK_SITE_ALLOWLIST)
    if unknown:
        raise ProviderValidationError("Sherlock site selection contains an unreviewed site.")
    return selected


def _decode_worker_payload(payload: object) -> list[SherlockResult]:
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ProviderValidationError("Sherlock worker returned an invalid envelope.")
    rows = payload.get("results")
    if not isinstance(rows, list) or len(rows) > MAX_SHERLOCK_SITES:
        raise ProviderValidationError("Sherlock worker returned an invalid result count.")

    decoded: list[SherlockResult] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ProviderValidationError("Sherlock worker returned a malformed result.")
        site_name = row.get("site_name")
        state_value = row.get("state")
        detection_method = row.get("detection_method")
        if not isinstance(site_name, str) or site_name not in SHERLOCK_SITE_ALLOWLIST:
            raise ProviderValidationError("Sherlock worker returned an unreviewed site.")
        if not isinstance(detection_method, str) or not detection_method:
            raise ProviderValidationError("Sherlock worker omitted the detection method.")
        try:
            state = AccountDiscoveryState(state_value)
        except (TypeError, ValueError) as exc:
            raise ProviderValidationError("Sherlock worker returned an unknown result state.") from exc

        http_status = row.get("http_status")
        if http_status in ("", None):
            parsed_status = None
        elif isinstance(http_status, int) and 100 <= http_status <= 599:
            parsed_status = http_status
        else:
            raise ProviderValidationError("Sherlock worker returned an invalid HTTP status.")

        profile_url = _canonical_public_url(row.get("profile_url"))
        if state is AccountDiscoveryState.CLAIMED and profile_url is None:
            raise ProviderValidationError("Claimed Sherlock result requires a valid public profile URL.")
        decoded.append(
            SherlockResult(
                site_name=site_name,
                state=state,
                profile_url=profile_url,
                http_status=parsed_status,
                diagnostic=_bounded_diagnostic(row.get("diagnostic")),
                detection_method=detection_method,
            )
        )
    return decoded


async def run_sherlock_worker(
    username: str,
    site_names: tuple[str, ...],
    per_site_timeout: float,
) -> list[SherlockResult]:
    """Run pinned Sherlock in a killable child process with a bounded machine contract."""
    selected = _normalize_site_names(site_names)
    request = json.dumps(
        {
            "version": 1,
            "username": username,
            "site_names": selected,
            "per_site_timeout": per_site_timeout,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    process = await asyncio.create_subprocess_exec(
        os.fspath(sys.executable),
        "-m",
        "app.providers.sherlock_worker",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        stdout, _stderr = await process.communicate(request)
    except asyncio.CancelledError:
        if process.returncode is None:
            process.kill()
        await process.wait()
        raise

    if len(stdout) > MAX_WORKER_OUTPUT_BYTES:
        raise ProviderValidationError("Sherlock worker output exceeded the configured limit.")
    if process.returncode != 0:
        raise ProviderExecutionError("Sherlock worker failed.")
    try:
        payload = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderValidationError("Sherlock worker returned invalid JSON.") from exc

    results = _decode_worker_payload(payload)
    if any(result.site_name not in selected for result in results):
        raise ProviderValidationError("Sherlock worker returned a site outside the requested subset.")
    return results


class SherlockProvider:
    descriptor = PROVIDER_BY_NAME["sherlock"]

    def __init__(
        self,
        *,
        site_names: Sequence[str] = SHERLOCK_SITE_ALLOWLIST,
        worker: Worker = run_sherlock_worker,
    ) -> None:
        load_reviewed_sherlock_sites()
        self.site_names = _normalize_site_names(site_names)
        self.worker = worker

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult:
        if secret is not None:
            raise ProviderValidationError("Sherlock does not accept credentials.")
        if query.identifier_kind != "username":
            raise ProviderValidationError("Sherlock only accepts username identifiers.")

        results = await self.worker(
            query.identifier_value,
            self.site_names,
            min(self.descriptor.timeout_seconds, 5.0),
        )
        if len(results) > len(self.site_names):
            raise ProviderValidationError("Sherlock returned more results than the site budget allows.")

        observations: list[ProviderObservationData] = []
        seen_sites: set[str] = set()
        for result in results:
            if result.site_name not in self.site_names or result.site_name in seen_sites:
                raise ProviderValidationError("Sherlock returned an invalid or duplicate site result.")
            seen_sites.add(result.site_name)
            profile_url = _canonical_public_url(result.profile_url)
            if result.state is AccountDiscoveryState.CLAIMED and profile_url is None:
                raise ProviderValidationError("Claimed Sherlock result has no valid public profile URL.")
            locator = (
                profile_url
                if result.state is AccountDiscoveryState.CLAIMED
                else f"sherlock://site/{quote(result.site_name, safe='')}"
            )
            assert locator is not None
            observations.append(
                ProviderObservationData(
                    source_locator=locator,
                    payload={
                        "site": result.site_name,
                        "account_state": result.state.value,
                        "account_candidate": result.state is AccountDiscoveryState.CLAIMED,
                        "profile_url": (
                            profile_url if result.state is AccountDiscoveryState.CLAIMED else None
                        ),
                        "http_status": result.http_status,
                        "detection_method": result.detection_method,
                        "diagnostic": result.diagnostic,
                        "identity_claim": False,
                    },
                )
            )
        return ProviderResult(observations=tuple(observations))
