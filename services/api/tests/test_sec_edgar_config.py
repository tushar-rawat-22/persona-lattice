# SPDX-License-Identifier: Apache-2.0
import pytest

from app.intelligence.contracts import LeadKind
from app.intelligence.source_outcomes import source_provider_exception_record
from app.intelligence.source_states import SourceRunReason, SourceRunState
from app.providers.errors import ProviderConfigurationError, ProviderValidationError
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


def test_non_secret_provider_configuration_maps_to_optional_not_configured() -> None:
    record = source_provider_exception_record(
        source_name="sec_edgar_exact_cik",
        lead_kind=LeadKind.URL,
        exc=ProviderConfigurationError("SEC operator identity is not configured."),
    )

    assert record is not None
    assert record.state is SourceRunState.UNAVAILABLE
    assert record.reason is SourceRunReason.OPTIONAL_NOT_CONFIGURED
    assert record.observation_count == 0
