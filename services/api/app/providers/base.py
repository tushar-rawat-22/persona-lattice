# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ContactRisk(str, Enum):
    NONE_KNOWN = "none_known"
    POSSIBLE = "possible"
    LIKELY = "likely"
    DIRECT_CONTACT = "direct_contact"


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    capability: str
    status: str
    contact_risk: ContactRisk
    reason: str


class Provider(Protocol):
    descriptor: ProviderDescriptor
