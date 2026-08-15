# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import json
import sys
from typing import Any

from sherlock_project.notify import QueryNotify
from sherlock_project.result import QueryStatus
from sherlock_project.sherlock import sherlock


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


def _main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict) or request.get("version") != 1:
            return 2
        username = request.get("username")
        site_data = request.get("site_data")
        timeout = request.get("per_site_timeout")
        if not isinstance(username, str) or not username or len(username) > 200:
            return 2
        if not isinstance(site_data, dict) or not site_data or len(site_data) > 8:
            return 2
        if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 10:
            return 2

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
            item = results[site_name]
            result = item.get("status")
            state = _STATUS_MAP.get(getattr(result, "status", None))
            if state is None:
                return 3
            configured = site_data.get(site_name, {})
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
