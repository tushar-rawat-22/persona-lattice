# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import inspect

from app.intelligence.source_bindings import SOURCE_BINDING_BY_NAME
from app.intelligence.source_catalog import SOURCE_BY_NAME
from app.providers.registry import PROVIDER_BY_NAME
from app.providers.sec_edgar import SecEdgarExactCikProvider
from app.providers.shared_runtime import DEFAULT_PROVIDER_RUNTIME


SEC_PROVIDER_NAME = "sec_edgar_exact_cik"


def test_sec_edgar_stays_pre_activation_until_full_governance_slice_lands() -> None:
    """Do not partially register SEC before catalog/binding/runtime ownership land together."""

    assert SEC_PROVIDER_NAME not in PROVIDER_BY_NAME
    assert SEC_PROVIDER_NAME not in SOURCE_BY_NAME
    assert SEC_PROVIDER_NAME not in SOURCE_BINDING_BY_NAME
    assert SEC_PROVIDER_NAME not in DEFAULT_PROVIDER_RUNTIME.adapters


def test_sec_edgar_adapter_still_requires_explicit_descriptor_before_activation() -> None:
    signature = inspect.signature(SecEdgarExactCikProvider)
    descriptor = signature.parameters["descriptor"]

    assert descriptor.default is inspect.Parameter.empty
    assert descriptor.kind is inspect.Parameter.KEYWORD_ONLY
