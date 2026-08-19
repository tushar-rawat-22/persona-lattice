# SPDX-License-Identifier: Apache-2.0
from enum import Enum


class IdentifierKind(str, Enum):
    NAME = "name"
    PHONE = "phone"
    EMAIL = "email"
    USERNAME = "username"
    URL = "url"
    DOMAIN = "domain"
    ORGANIZATION = "organization"


class ObservationSourceKind(str, Enum):
    USER_SUPPLIED = "user_supplied"
    PUBLIC_WEB = "public_web"
    PUBLIC_PROFILE = "public_profile"
    PUBLIC_DOCUMENT = "public_document"
    PROVIDER = "provider"
    REGISTRY = "registry"
    UPLOAD = "upload"


class ClaimOrigin(str, Enum):
    HUMAN = "human"
    RULE = "rule"
    AI = "ai"


class EvidenceRelation(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    UNRESOLVED = "unresolved"


class FreshnessState(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"
