# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_PAGE = ROOT / "apps/web/app/page.tsx"
NEXT_CONFIG = ROOT / "apps/web/next.config.ts"


def test_public_preview_has_no_private_api_fetch_or_environment_access() -> None:
    source = PUBLIC_PAGE.read_text(encoding="utf-8")

    assert "fetch(" not in source
    assert '"/api/' not in source
    assert "process.env" not in source
    assert "Admin credentials required" in source
    assert "Real intake and stored case data are never sent to an unauthenticated browser." in source
    assert "This surface is demo-only." in source


def test_production_web_proxy_defaults_to_loopback_api() -> None:
    source = NEXT_CONFIG.read_text(encoding="utf-8")

    assert '"http://127.0.0.1:8000"' in source
    assert 'source: "/api/:path*"' in source
    assert "destination: `${apiOrigin}/:path*`" in source


def test_web_security_headers_cover_launch_baseline() -> None:
    source = NEXT_CONFIG.read_text(encoding="utf-8")

    assert "Content-Security-Policy" in source
    assert "frame-ancestors 'none'" in source
    assert "form-action 'self'" in source
    assert 'X-Content-Type-Options", value: "nosniff"' in source
    assert 'X-Frame-Options", value: "DENY"' in source
    assert 'Referrer-Policy", value: "no-referrer"' in source
    assert "Strict-Transport-Security" in source
    assert "camera=(), microphone=(), geolocation=(), payment=(), usb=()" in source
