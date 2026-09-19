# SPDX-License-Identifier: Apache-2.0
import logging
from time import perf_counter_ns
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response


# Reuse Uvicorn's configured error logger so the safe operational events are
# emitted even when raw Uvicorn access logging is disabled by the launcher.
LOGGER_NAME = "uvicorn.error"
_LOGGER = logging.getLogger(LOGGER_NAME)
_UNMATCHED_ROUTE = "unmatched"
_PRIVATE_CACHE_CONTROL = "no-store"


def _route_class(request: Request) -> str:
    """Return the registered route template, never the raw request target."""

    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if not isinstance(template, str) or not template.startswith("/"):
        return _UNMATCHED_ROUTE
    return template


def _duration_ms(started_ns: int) -> float:
    return max(0.0, (perf_counter_ns() - started_ns) / 1_000_000)


def _record(request: Request, status_code: int, started_ns: int) -> None:
    _LOGGER.info(
        "http_request method=%s route=%s status=%d duration_ms=%.3f",
        request.method,
        _route_class(request),
        status_code,
        _duration_ms(started_ns),
    )


def install_operational_access_logging(app: FastAPI) -> None:
    """Install metadata-safe observability and private-response cache policy.

    The middleware records only method, registered route template, status and
    duration. It deliberately never reads the raw target, query string,
    headers, cookies or request body. Every API response is marked ``no-store``
    because this service is a private authenticated evidence surface and even
    error/session responses can reveal operator state when cached by a browser
    or intermediary.
    """

    @app.middleware("http")
    async def operational_access_log(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_ns = perf_counter_ns()
        try:
            response = await call_next(request)
        except BaseException:
            _record(request, 500, started_ns)
            raise
        response.headers["Cache-Control"] = _PRIVATE_CACHE_CONTROL
        _record(request, response.status_code, started_ns)
        return response
