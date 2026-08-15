# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from ..models import Purpose


class ContactRisk(str, Enum):
    NONE_KNOWN = "none_known"
    POSSIBLE = "possible"
    LIKELY = "likely"
    DIRECT_CONTACT = "direct_contact"


class SourceCategory(str, Enum):
    SYNTHETIC = "synthetic"
    PHONE_METADATA = "phone_metadata"
    PUBLIC_WEB = "public_web"
    USERNAME_DISCOVERY = "username_discovery"
    REGISTRY = "registry"
    CALLER_ID = "caller_id"
    REFERENCE = "reference"


class ProviderStatus(str, Enum):
    SYNTHETIC = "synthetic"
    DEVELOPMENT = "development"
    PLANNED = "planned"
    REVIEW_REQUIRED = "review_required"
    MANUAL_ONLY = "manual_only"
    REFERENCE_ONLY = "reference_only"


class AuthMode(str, Enum):
    NONE = "none"
    API_KEY = "api_key"


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    capability: str
    status: str
    contact_risk: ContactRisk
    reason: str
    version: str = "unversioned"
    source_category: SourceCategory = SourceCategory.REFERENCE
    allowed_purposes: frozenset[Purpose] = field(default_factory=frozenset)
    supported_identifier_kinds: frozenset[str] = field(default_factory=frozenset)
    auth_mode: AuthMode = AuthMode.NONE
    secret_env: str | None = None
    max_attempts: int = 1
    timeout_seconds: float = 5.0
    max_response_bytes: int = 256 * 1024
    max_concurrency: int = 1
    rate_limit: int = 30
    rate_window_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.version.strip():
            raise ValueError("Provider name and version are required.")
        if any(not value.strip() for value in self.supported_identifier_kinds):
            raise ValueError("Supported identifier kinds cannot contain blank values.")
        if self.max_attempts < 1:
            raise ValueError("Provider max_attempts must be at least 1.")
        if self.timeout_seconds <= 0:
            raise ValueError("Provider timeout_seconds must be positive.")
        if self.max_response_bytes < 1:
            raise ValueError("Provider max_response_bytes must be positive.")
        if self.max_concurrency < 1:
            raise ValueError("Provider max_concurrency must be at least 1.")
        if self.rate_limit < 1 or self.rate_window_seconds <= 0:
            raise ValueError("Provider rate budget must be positive.")
        if self.auth_mode is AuthMode.API_KEY and not self.secret_env:
            raise ValueError("API-key providers require a server-side secret environment name.")


@dataclass(frozen=True, slots=True)
class ProviderQuery:
    subject_id: UUID
    identifier_id: UUID
    identifier_kind: str
    identifier_value: str


@dataclass(frozen=True, slots=True)
class ProviderObservationData:
    source_locator: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ProviderResult:
    observations: tuple[ProviderObservationData, ...]


class Provider(Protocol):
    descriptor: ProviderDescriptor

    async def execute(self, query: ProviderQuery, secret: str | None) -> ProviderResult: ...
