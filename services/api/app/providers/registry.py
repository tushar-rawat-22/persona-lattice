# SPDX-License-Identifier: Apache-2.0
from .base import ContactRisk, ProviderDescriptor


PROVIDERS: tuple[ProviderDescriptor, ...] = (
    ProviderDescriptor(
        name="numverify",
        capability="phone_intelligence",
        status="planned",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Development adapter after provider-terms review.",
    ),
    ProviderDescriptor(
        name="abstract_phone_intelligence",
        capability="phone_intelligence",
        status="planned",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Development adapter after provider-terms review.",
    ),
    ProviderDescriptor(
        name="ipqualityscore",
        capability="phone_risk",
        status="planned",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="Development adapter after provider-terms review.",
    ),
    ProviderDescriptor(
        name="maigret",
        capability="username_discovery",
        status="planned",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="MIT-licensed optional adapter; not vendored.",
    ),
    ProviderDescriptor(
        name="sherlock",
        capability="username_discovery",
        status="planned",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="MIT-licensed optional verifier; not vendored.",
    ),
    ProviderDescriptor(
        name="whatsmyname",
        capability="username_dataset",
        status="license_review",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="CC BY-SA dataset boundary must be reviewed before bundling.",
    ),
    ProviderDescriptor(
        name="truecaller_manual",
        capability="caller_id",
        status="manual_only",
        contact_risk=ContactRisk.POSSIBLE,
        reason="Excluded from silent/public automation because search visibility may exist.",
    ),
    ProviderDescriptor(
        name="phoneinfoga",
        capability="phone_osint",
        status="reference_only",
        contact_risk=ContactRisk.NONE_KNOWN,
        reason="GPL code is not copied into the Apache core.",
    ),
)
