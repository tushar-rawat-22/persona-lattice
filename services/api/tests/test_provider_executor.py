# SPDX-License-Identifier: Apache-2.0
from dataclasses import replace
from uuid import uuid4

import pytest

from app.evidence import (
    EvidenceStore,
    IdentifierKind,
    ObservationSourceKind,
    create_database_engine,
    create_schema,
    make_session_factory,
    normalize_identifier,
)
from app.models import Purpose
from app.providers import (
    AuthMode,
    ExecutionRequest,
    ProviderAuthError,
    ProviderExecutor,
    ProviderObservationData,
    ProviderRateBudgetExceeded,
    ProviderResponseTooLarge,
    ProviderResult,
    ProviderTransientError,
    ProviderValidationError,
    QueryOrigin,
    SyntheticEchoProvider,
)
from app.uploads import (
    CandidateOrigin,
    CandidateType,
    ReviewCandidate,
    ReviewStatus,
)


@pytest.fixture
def store() -> EvidenceStore:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        yield EvidenceStore(session)


def _case(store: EvidenceStore):
    subject = store.add_subject("Synthetic Person")
    identifier = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "person@example.test"),
    )
    return subject, identifier


def _request(subject, identifier, **overrides) -> ExecutionRequest:
    values = {
        "provider_name": "synthetic_echo",
        "subject_id": subject.id,
        "identifier_id": identifier.id,
        "purpose": Purpose.SELF_AUDIT,
        "consent_acknowledged": True,
    }
    values.update(overrides)
    return ExecutionRequest(**values)


@pytest.mark.asyncio
async def test_synthetic_provider_result_becomes_provenance_observation(store: EvidenceStore) -> None:
    subject, identifier = _case(store)
    executor = ProviderExecutor(store=store, adapters=[SyntheticEchoProvider()])

    observations = await executor.execute(_request(subject, identifier))

    assert len(observations) == 1
    observation = observations[0]
    assert observation.source_kind == ObservationSourceKind.PROVIDER
    assert observation.source_name == "synthetic_echo"
    assert observation.identifier_id == identifier.id
    assert observation.payload["provider_version"] == "1"
    assert observation.payload["synthetic"] is True


@pytest.mark.asyncio
async def test_confirmed_document_candidate_must_match_stored_identifier(store: EvidenceStore) -> None:
    subject, identifier = _case(store)
    candidate = ReviewCandidate(
        candidate_id=uuid4(),
        candidate_type=CandidateType.IDENTIFIER,
        origin=CandidateOrigin.RULE,
        source_artifact_id=uuid4(),
        identifier_kind=IdentifierKind.EMAIL,
        value="other@example.test",
        review_status=ReviewStatus.CONFIRMED,
        external_research_authorized=True,
    )
    executor = ProviderExecutor(store=store, adapters=[SyntheticEchoProvider()])

    with pytest.raises(ProviderValidationError, match="does not match"):
        await executor.execute(
            _request(
                subject,
                identifier,
                query_origin=QueryOrigin.CONFIRMED_DOCUMENT_CANDIDATE,
                document_candidate=candidate,
            )
        )


class FlakyProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.descriptor = replace(
            SyntheticEchoProvider.descriptor,
            name="flaky",
            max_attempts=3,
        )

    async def execute(self, query, secret):
        self.calls += 1
        if self.calls < 3:
            raise ProviderTransientError("temporary")
        return ProviderResult(
            observations=(ProviderObservationData("synthetic://flaky", {"ok": True}),)
        )


@pytest.mark.asyncio
async def test_transient_failures_retry_boundedly(store: EvidenceStore) -> None:
    subject, identifier = _case(store)
    provider = FlakyProvider()
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    executor = ProviderExecutor(store=store, adapters=[provider], sleep=fake_sleep)
    observations = await executor.execute(
        replace(_request(subject, identifier), provider_name="flaky")
    )

    assert provider.calls == 3
    assert sleeps == [0.25, 0.5]
    assert observations[0].payload["ok"] is True


class AuthProvider:
    descriptor = replace(
        SyntheticEchoProvider.descriptor,
        name="auth",
        auth_mode=AuthMode.API_KEY,
        secret_env="SYNTHETIC_API_KEY",
    )

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, query, secret):
        self.calls += 1
        return ProviderResult(observations=())


@pytest.mark.asyncio
async def test_missing_secret_fails_before_provider_call(store: EvidenceStore) -> None:
    subject, identifier = _case(store)
    provider = AuthProvider()
    executor = ProviderExecutor(
        store=store,
        adapters=[provider],
        secret_resolver=lambda _name: None,
    )

    with pytest.raises(ProviderAuthError):
        await executor.execute(replace(_request(subject, identifier), provider_name="auth"))
    assert provider.calls == 0


class LargeProvider:
    descriptor = replace(
        SyntheticEchoProvider.descriptor,
        name="large",
        max_response_bytes=64,
    )

    async def execute(self, query, secret):
        return ProviderResult(
            observations=(ProviderObservationData("synthetic://large", {"blob": "x" * 500}),)
        )


@pytest.mark.asyncio
async def test_response_size_limit_is_enforced_before_persistence(store: EvidenceStore) -> None:
    subject, identifier = _case(store)
    executor = ProviderExecutor(store=store, adapters=[LargeProvider()])

    with pytest.raises(ProviderResponseTooLarge):
        await executor.execute(replace(_request(subject, identifier), provider_name="large"))


@pytest.mark.asyncio
async def test_local_rate_budget_counts_each_call_and_recovers_after_window(
    store: EvidenceStore,
) -> None:
    subject, identifier = _case(store)
    provider = SyntheticEchoProvider()
    provider.descriptor = replace(provider.descriptor, rate_limit=1, rate_window_seconds=60)
    now = [100.0]
    executor = ProviderExecutor(
        store=store,
        adapters=[provider],
        rate_clock=lambda: now[0],
    )

    await executor.execute(_request(subject, identifier))
    with pytest.raises(ProviderRateBudgetExceeded):
        await executor.execute(_request(subject, identifier))

    now[0] += 61
    assert await executor.execute(_request(subject, identifier))


class TransientUnderTightBudget:
    def __init__(self) -> None:
        self.calls = 0
        self.descriptor = replace(
            SyntheticEchoProvider.descriptor,
            name="tight-budget",
            max_attempts=3,
            rate_limit=1,
        )

    async def execute(self, query, secret):
        self.calls += 1
        raise ProviderTransientError("temporary")


@pytest.mark.asyncio
async def test_retries_also_consume_local_rate_budget(store: EvidenceStore) -> None:
    subject, identifier = _case(store)
    provider = TransientUnderTightBudget()

    async def no_wait(_delay: float) -> None:
        return None

    executor = ProviderExecutor(store=store, adapters=[provider], sleep=no_wait)

    with pytest.raises(ProviderRateBudgetExceeded):
        await executor.execute(
            replace(_request(subject, identifier), provider_name="tight-budget")
        )
    assert provider.calls == 1
