# SPDX-License-Identifier: Apache-2.0


class ProviderExecutionError(RuntimeError):
    retryable = False
    code = "provider_error"


class ProviderPolicyError(ProviderExecutionError):
    code = "provider_policy_blocked"


class ProviderValidationError(ProviderExecutionError):
    code = "provider_validation_error"


class ProviderAuthError(ProviderExecutionError):
    code = "provider_auth_error"


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
