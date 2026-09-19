# SPDX-License-Identifier: Apache-2.0
import logging
from time import perf_counter_ns

from fastapi import FastAPI, Request
from starlette.responses import Response

LOGGER_NAME = "uvicorn.error"
_LOGGER = logging.getLogger(LOGGER_NAME)
_UNMATCHED_ROUTE = "unmatched"
_PRIVATE_CACHE_CONTROL = "no-store"


def _route_class(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str) and path:
        return path
    return _UNMATCHED_ROUTE


def _record(request: Request, status_code: int, started_ns: int) -> None:
    duration_ms = max(0.0, (perf_counter_ns() - started_ns) / 1_000_000)
    _LOGGER.info(
        "private_api_request method=%s route=%s status=%d duration_ms=%.2f",
        request.method,
        _route_class(request),
        status_code,
        duration_ms,
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
    async def operational_access_log(request: Request, call_next) -> Response:
        started_ns = perf_counter_ns()
        try:
            response = await call_next(request)
        except BaseException:
            _record(request, 500, started_ns)
            raise
        response.headers["Cache-Control"] = _PRIVATE_CACHE_CONTROL
        _record(request, response.status_code, started_ns)
        return response
