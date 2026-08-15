# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from importlib import resources
import json
import sys
from typing import Any

from sherlock_project import __version__ as installed_sherlock_version
from sherlock_project.notify import QueryNotify
from sherlock_project.result import QueryStatus
from sherlock_project.sherlock import sherlock

SHERLOCK_UPSTREAM_VERSION = "0.16.1"
SHERLOCK_SITE_ALLOWLIST = frozenset(
    {
        "BitBucket",
        "Codeberg",
        "Codeforces",
        "GitHub",
        "GitLab",
        "Kaggle",
        "Keybase",
        "Replit.com",
    }
)
MAX_SHERLOCK_SITES = 8


class _DiscardingWriter:
    def write(self, value: str) -> int:
        return len(value)

    def flush(self) -> None:
        return None


_STATUS_MAP = {
    QueryStatus.CLAIMED: "claimed",
    QueryStatus.AVAILABLE: "available",
    QueryStatus.UNKNOWN: "unknown",
    QueryStatus.ILLEGAL: "illegal",
    QueryStatus.WAF: "waf",
}


def _load_site_data(site_names: object) -> dict[str, dict[str, Any]]:
    if installed_sherlock_version != SHERLOCK_UPSTREAM_VERSION:
        raise ValueError("Unexpected Sherlock version.")
    if not isinstance(site_names, list) or not site_names or len(site_names) > MAX_SHERLOCK_SITES:
        raise ValueError("Invalid Sherlock site selection.")
    if any(not isinstance(name, str) for name in site_names):
        raise ValueError("Invalid Sherlock site name.")
    if len(set(site_names)) != len(site_names):
        raise ValueError("Duplicate Sherlock site name.")
    if set(site_names).difference(SHERLOCK_SITE_ALLOWLIST):
        raise ValueError("Unreviewed Sherlock site name.")

    resource = (
        resources.files("sherlock_project")
        .joinpath("resources")
        .joinpath("data.json")
    )
    raw = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Invalid Sherlock packaged site data.")

    selected: dict[str, dict[str, Any]] = {}
    for site_name in site_names:
        entry = raw.get(site_name)
        if not isinstance(entry, dict):
            raise ValueError("Reviewed Sherlock site is missing.")
        if entry.get("isNSFW"):
            raise ValueError("NSFW Sherlock site is not allowed.")
        if not isinstance(entry.get("url"), str) or not isinstance(entry.get("errorType"), str):
            raise ValueError("Malformed Sherlock site metadata.")
        selected[site_name] = dict(entry)
    return selected


def _main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict) or request.get("version") != 1:
            return 2
        username = request.get("username")
        timeout = request.get("per_site_timeout")
        if not isinstance(username, str) or not username or len(username) > 200:
            return 2
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 10:
            return 2
        site_data = _load_site_data(request.get("site_names"))

        sink = _DiscardingWriter()
        with redirect_stdout(sink), redirect_stderr(sink):
            results = sherlock(
                username,
                site_data,
                QueryNotify(),
                dump_response=False,
                proxy=None,
                timeout=max(1, int(timeout)),
            )

        output: list[dict[str, Any]] = []
        for site_name in sorted(results):
            if site_name not in site_data:
                return 3
            item = results[site_name]
            result = item.get("status")
            state = _STATUS_MAP.get(getattr(result, "status", None))
            if state is None:
                return 3
            configured = site_data[site_name]
            output.append(
                {
                    "site_name": site_name,
                    "state": state,
                    "profile_url": item.get("url_user") or None,
                    "http_status": item.get("http_status") or None,
                    "diagnostic": (
                        " ".join(str(getattr(result, "context", "")).split())[:256] or None
                    ),
                    "detection_method": str(configured.get("errorType") or "unknown"),
                }
            )

        json.dump(
            {"version": 1, "results": output},
            sys.stdout,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return 0
    except Exception:
        return 4


if __name__ == "__main__":
    raise SystemExit(_main())
