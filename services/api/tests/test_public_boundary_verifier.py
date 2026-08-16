# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts/verify_public_boundary.py"
SPEC = importlib.util.spec_from_file_location("verify_public_boundary", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
verify_public_boundary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_public_boundary)


def test_hosted_verifier_requires_https() -> None:
    with pytest.raises(verify_public_boundary.VerificationFailure, match="HTTPS"):
        verify_public_boundary._base_url("http://example.com")


def test_hosted_verifier_allows_local_http_for_smoke_testing() -> None:
    assert verify_public_boundary._base_url("http://127.0.0.1:3000/") == "http://127.0.0.1:3000"


def test_hosted_verifier_rejects_credentials_and_paths() -> None:
    with pytest.raises(verify_public_boundary.VerificationFailure):
        verify_public_boundary._base_url("https://user:password@example.com")
    with pytest.raises(verify_public_boundary.VerificationFailure):
        verify_public_boundary._base_url("https://example.com/admin")


def test_private_boundary_requires_exact_401_no_store_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        verify_public_boundary,
        "_request",
        lambda _base, _path: (
            401,
            {"cache-control": "no-store"},
            b'{"detail":"Admin authentication required."}',
        ),
    )
    verify_public_boundary._verify_private_get("https://example.com", "/api/v1/cases")


def test_private_boundary_rejects_unexpected_anonymous_data(monkeypatch) -> None:
    monkeypatch.setattr(
        verify_public_boundary,
        "_request",
        lambda _base, _path: (
            200,
            {"cache-control": "no-store"},
            b'{"seed_value":"must-not-leak"}',
        ),
    )
    with pytest.raises(verify_public_boundary.VerificationFailure, match="expected 401"):
        verify_public_boundary._verify_private_get("https://example.com", "/api/v1/cases")
