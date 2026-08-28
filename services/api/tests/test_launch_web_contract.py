# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PUBLIC_PAGE = ROOT / "apps/web/app/page.tsx"
NEXT_CONFIG = ROOT / "apps/web/next.config.ts"


def test_public_preview_has_no_private_api_fetch_or_environment_access() -> None:
    source = PUBLIC_PAGE.read_text(encoding="utf-8")
    normalized = " ".join(source.split())

    assert "fetch(" not in source
    assert '"/api/' not in source
    assert "process.env" not in source
    assert "Visitors can inspect the product, not operate it." in normalized
    assert "Synthetic case only · No research runs from this page" in normalized
    assert (
        "Real-person intake and retained cases remain behind the admin session and CSRF boundary."
        in normalized
    )


def test_production_web_proxy_keeps_browser_same_origin_and_api_on_loopback() -> None:
    source = NEXT_CONFIG.read_text(encoding="utf-8")

    assert 'NEXT_PUBLIC_API_URL: "/api"' in source
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
