# SPDX-License-Identifier: Apache-2.0


class ProviderExecutionError(RuntimeError):
    retryable = False
    code = "provider_error"


class ProviderPolicyError(ProviderExecutionError):
    code = "provider_policy_blocked"


class ProviderValidationError(ProviderExecutionError):
    """Validation failure whose execution phase is not necessarily known."""

    code = "provider_validation_error"


class ProviderResultValidationError(ProviderValidationError):
    """Validation failure proven to have happened after provider output returned."""

    code = "provider_result_validation_error"


class ProviderAuthError(ProviderExecutionError):
    code = "provider_auth_error"


class ProviderConfigurationError(ProviderExecutionError):
    """Required non-secret provider configuration is unavailable before contact."""

    code = "provider_configuration_error"


class ProviderResponseTooLarge(ProviderExecutionError):
    code = "provider_response_too_large"


class ProviderTimeoutError(ProviderExecutionError):
    retryable = True
    code = "provider_timeout"


class ProviderTransientError(ProviderExecutionError):
    retryable = True
    code = "provider_transient_error"


class ProviderRemoteRateLimitError(ProviderExecutionError):
    retryable = True
    code = "provider_remote_rate_limit"

    def __init__(self, message: str = "Provider rate limited the request.", retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ProviderRateBudgetExceeded(ProviderExecutionError):
    code = "provider_local_rate_budget"


class ProviderRoutingUnavailableError(ProviderExecutionError):
    """Prerequisite routing authority failed before any subject provider contact."""

    code = "provider_routing_unavailable"


class ProviderPublicWebOptOutError(ProviderExecutionError):
    """Provider returned an explicit public-web visibility opt-out after contact."""

    code = "provider_public_web_opt_out"


class ProviderAccountUnavailableError(ProviderExecutionError):
    """Requested public account exists but is suspended/deactivated or otherwise withheld."""

    code = "provider_account_unavailable"
