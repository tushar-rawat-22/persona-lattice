# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"


def _source_locator_renderer(source: str) -> str:
    start = source.index("function safeWebSourceLocator")
    end = source.index("function sourceOutcomeDetails")
    return source[start:end]


def _observation_renderer(source: str) -> str:
    start = source.index("function ObservationDetails")
    end = source.index("function resolveConnectedIdentifier")
    return source[start:end]


def test_source_locator_renderer_only_links_safe_absolute_web_urls() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    renderer = _source_locator_renderer(source)

    assert 'locator !== locator.trim()' in renderer
    assert "new URL(locator)" in renderer
    assert 'parsed.protocol !== "http:" && parsed.protocol !== "https:"' in renderer
    assert "parsed.username || parsed.password" in renderer
    assert "!parsed.hostname" in renderer
    assert 'target="_blank"' in renderer
    assert 'rel="noopener noreferrer"' in renderer
    assert "href={href}" in renderer
    assert "{locator}" in renderer


def test_canonical_provenance_surfaces_share_source_locator_renderer() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert source.count("<SourceLocator locator={report.seed_provenance.source_locator} />") == 1
    assert source.count("<SourceLocator locator={candidateLocator} />") == 1
    assert source.count("<SourceLocator locator={provenance.source_locator} />") == 1
    assert source.count("<SourceLocator locator={observation.source_locator} />") == 2
    assert source.count("<SourceLocator locator={resolved.source_locator} />") == 1


def test_observation_detail_values_are_never_promoted_to_links() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    renderer = _observation_renderer(source)

    assert "renderObservationValue(fieldValue)" in renderer
    assert "SourceLocator" not in renderer
    assert "<a " not in renderer
    assert "href=" not in renderer
