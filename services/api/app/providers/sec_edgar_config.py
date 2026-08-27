# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from collections.abc import Mapping
import os

from .sec_edgar_transport import validate_sec_user_agent


SEC_EDGAR_USER_AGENT_ENV = "SEC_EDGAR_USER_AGENT"


def sec_edgar_user_agent_from_env(
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Return the validated non-secret SEC client identity, if configured.

    SEC asks automated EDGAR clients to declare a User-Agent containing a
    maintainable contact. This is operator identity metadata, not an API key or
    credential, so it intentionally stays outside ``AuthMode``/secret loading.
    Missing or blank configuration means the optional source is not configured;
    a non-blank malformed value fails closed through the transport validator.
    """

    source = os.environ if environ is None else environ
    raw = source.get(SEC_EDGAR_USER_AGENT_ENV)
    if raw is None or not raw.strip():
        return None
    return validate_sec_user_agent(raw)


def sec_edgar_configured(environ: Mapping[str, str] | None = None) -> bool:
    """Return whether a valid SEC EDGAR operator User-Agent is configured."""

    return sec_edgar_user_agent_from_env(environ) is not None
