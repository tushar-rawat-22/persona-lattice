# SPDX-License-Identifier: Apache-2.0
import pytest

from app.providers.errors import ProviderValidationError
from app.providers.sec_edgar_config import (
    SEC_EDGAR_USER_AGENT_ENV,
    sec_edgar_configured,
    sec_edgar_user_agent_from_env,
)


VALID_USER_AGENT = "PersonaLattice ops@example.com"


def test_missing_sec_user_agent_is_not_configured() -> None:
    assert sec_edgar_user_agent_from_env({}) is None
    assert sec_edgar_configured({}) is False


def test_blank_sec_user_agent_is_not_configured() -> None:
    environ = {SEC_EDGAR_USER_AGENT_ENV: "   "}
    assert sec_edgar_user_agent_from_env(environ) is None
    assert sec_edgar_configured(environ) is False


def test_valid_sec_user_agent_is_returned_without_secret_semantics() -> None:
    environ = {SEC_EDGAR_USER_AGENT_ENV: VALID_USER_AGENT}
    assert sec_edgar_user_agent_from_env(environ) == VALID_USER_AGENT
    assert sec_edgar_configured(environ) is True


@pytest.mark.parametrize(
    "value",
    [
        "PersonaLattice",
        " PersonaLattice ops@example.com",
        "PersonaLattice ops@example.com ",
        "PersonaLattice ops@example.com\nInjected: header",
    ],
)
def test_malformed_configured_sec_user_agent_fails_closed(value: str) -> None:
    with pytest.raises(ProviderValidationError):
        sec_edgar_user_agent_from_env({SEC_EDGAR_USER_AGENT_ENV: value})
