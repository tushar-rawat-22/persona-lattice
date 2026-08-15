# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio
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
    AccountDiscoveryState,
    ExecutionRequest,
    ProviderExecutor,
    ProviderQuery,
    ProviderValidationError,
    SHERLOCK_SITE_ALLOWLIST,
    SHERLOCK_UPSTREAM_VERSION,
    SherlockProvider,
    SherlockResult,
    load_reviewed_sherlock_sites,
)
from app.providers.sherlock import _decode_worker_payload, run_sherlock_worker


def _site(url: str) -> dict[str, str]:
    return {"url": url, "urlMain": url, "errorType": "status_code"}


@pytest.fixture
def store() -> EvidenceStore:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    factory = make_session_factory(engine)
    with factory() as session:
        yield EvidenceStore(session)


def test_pinned_sherlock_package_and_reviewed_site_budget() -> None:
    from sherlock_project import __version__

    assert __version__ == SHERLOCK_UPSTREAM_VERSION == "0.16.1"
    sites = load_reviewed_sherlock_sites()
    assert tuple(sites) == SHERLOCK_SITE_ALLOWLIST
    assert len(sites) == 8
    assert all(not entry.get("isNSFW") for entry in sites.values())


def test_unreviewed_or_incomplete_site_catalog_is_rejected() -> None:
    with pytest.raises(ProviderValidationError, match="unreviewed"):
        SherlockProvider(site_data={"Example": _site("https://example.test/{}")})

    with pytest.raises(ProviderValidationError, match="incomplete"):
        SherlockProvider(site_data={"GitHub": {"url": "https://github.com/{}"}})


@pytest.mark.asyncio
async def test_sherlock_maps_account_states_without_creating_identity_claims() -> None:
    async def worker(username, site_data, timeout):
        assert username == "example-user"
        assert set(site_data) == {"GitHub", "Keybase"}
        assert timeout <= 5
        return [
            SherlockResult(
                site_name="GitHub",
                state=AccountDiscoveryState.CLAIMED,
                profile_url="https://WWW.GITHUB.com/example-user#bio",
                http_status=200,
                diagnostic=None,
                detection_method="status_code",
            ),
            SherlockResult(
                site_name="Keybase",
                state=AccountDiscoveryState.AVAILABLE,
                profile_url="https://keybase.io/example-user",
                http_status=404,
                diagnostic="not found",
                detection_method="status_code",
            ),
        ]

    provider = SherlockProvider(
        site_data={
            "GitHub": _site("https://github.com/{}"),
            "Keybase": _site("https://keybase.io/{}"),
        },
        worker=worker,
    )
    result = await provider.execute(
        ProviderQuery(
            subject_id=uuid4(),
            identifier_id=uuid4(),
            identifier_kind="username",
            identifier_value="example-user",
        ),
        None,
    )

    assert len(result.observations) == 2
    claimed, available = result.observations
    assert claimed.source_locator == "https://www.github.com/example-user"
    assert claimed.payload["account_candidate"] is True
    assert claimed.payload["identity_claim"] is False
    assert claimed.payload["profile_url"] == "https://www.github.com/example-user"
    assert available.source_locator == "sherlock://site/Keybase"
    assert available.payload["account_state"] == "available"
    assert available.payload["account_candidate"] is False
    assert available.payload["profile_url"] is None


@pytest.mark.asyncio
async def test_sherlock_rejects_wrong_identifier_kind_and_duplicate_results() -> None:
    calls = 0

    async def worker(username, site_data, timeout):
        nonlocal calls
        calls += 1
        return [
            SherlockResult(
                "GitHub",
                AccountDiscoveryState.UNKNOWN,
                None,
                None,
                "temporary",
                "status_code",
            ),
            SherlockResult(
                "GitHub",
                AccountDiscoveryState.UNKNOWN,
                None,
                None,
                "temporary",
                "status_code",
            ),
        ]

    provider = SherlockProvider(
        site_data={"GitHub": _site("https://github.com/{}")},
        worker=worker,
    )
    with pytest.raises(ProviderValidationError, match="username"):
        await provider.execute(
            ProviderQuery(uuid4(), uuid4(), "email", "person@example.test"),
            None,
        )
    assert calls == 0

    with pytest.raises(ProviderValidationError, match="duplicate"):
        await provider.execute(
            ProviderQuery(uuid4(), uuid4(), "username", "example-user"),
            None,
        )


def test_worker_contract_rejects_unreviewed_and_malformed_results() -> None:
    with pytest.raises(ProviderValidationError, match="unreviewed"):
        _decode_worker_payload(
            {
                "version": 1,
                "results": [
                    {
                        "site_name": "Unreviewed",
                        "state": "claimed",
                        "profile_url": "https://example.test/u",
                        "http_status": 200,
                        "detection_method": "status_code",
                    }
                ],
            }
        )

    with pytest.raises(ProviderValidationError, match="unknown result state"):
        _decode_worker_payload(
            {
                "version": 1,
                "results": [
                    {
                        "site_name": "GitHub",
                        "state": "definitely_found",
                        "profile_url": "https://github.com/u",
                        "http_status": 200,
                        "detection_method": "status_code",
                    }
                ],
            }
        )


@pytest.mark.asyncio
async def test_worker_process_is_killed_when_execution_is_cancelled(monkeypatch) -> None:
    started = asyncio.Event()

    class FakeProcess:
        returncode = None

        def __init__(self) -> None:
            self.killed = False
            self.waited = False

        async def communicate(self, request):
            assert request
            started.set()
            await asyncio.Event().wait()

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> int:
            self.waited = True
            self.returncode = -9
            return -9

    process = FakeProcess()

    async def fake_create_subprocess_exec(*args, **kwargs):
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    task = asyncio.create_task(
        run_sherlock_worker(
            "example-user",
            {"GitHub": _site("https://github.com/{}")},
            1.0,
        )
    )
    await started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert process.killed is True
    assert process.waited is True


@pytest.mark.asyncio
async def test_sherlock_runs_through_m3_and_persists_provider_observation(
    store: EvidenceStore,
) -> None:
    subject = store.add_subject("Synthetic Person")
    username = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.USERNAME, "example-user"),
    )

    async def worker(_username, _site_data, _timeout):
        return [
            SherlockResult(
                "GitHub",
                AccountDiscoveryState.CLAIMED,
                "https://github.com/example-user",
                200,
                None,
                "status_code",
            )
        ]

    provider = SherlockProvider(
        site_data={"GitHub": _site("https://github.com/{}")},
        worker=worker,
    )
    executor = ProviderExecutor(store=store, adapters=[provider])
    observations = await executor.execute(
        ExecutionRequest(
            provider_name="sherlock",
            subject_id=subject.id,
            identifier_id=username.id,
            purpose=Purpose.SELF_AUDIT,
            consent_acknowledged=True,
        )
    )

    assert len(observations) == 1
    observation = observations[0]
    assert observation.source_kind is ObservationSourceKind.PROVIDER
    assert observation.source_name == "sherlock"
    assert observation.payload["provider_version"] == "0.16.1"
    assert observation.payload["account_candidate"] is True
    assert observation.payload["identity_claim"] is False


@pytest.mark.asyncio
async def test_m3_rejects_non_username_before_sherlock_worker(store: EvidenceStore) -> None:
    subject = store.add_subject("Synthetic Person")
    email = store.add_identifier(
        subject.id,
        normalize_identifier(IdentifierKind.EMAIL, "person@example.test"),
    )
    calls = 0

    async def worker(_username, _site_data, _timeout):
        nonlocal calls
        calls += 1
        return []

    provider = SherlockProvider(
        site_data={"GitHub": _site("https://github.com/{}")},
        worker=worker,
    )
    executor = ProviderExecutor(store=store, adapters=[provider])

    with pytest.raises(ProviderValidationError, match="Identifier kind"):
        await executor.execute(
            ExecutionRequest(
                provider_name="sherlock",
                subject_id=subject.id,
                identifier_id=email.id,
                purpose=Purpose.SELF_AUDIT,
                consent_acknowledged=True,
            )
        )
    assert calls == 0
