# SPDX-License-Identifier: Apache-2.0
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_UI = ROOT / "apps/web/app/admin/quick-research.tsx"


def _observation_renderer(source: str) -> str:
    start = source.index("function ObservationDetails")
    end = source.index("function resolveConnectedIdentifier")
    return source[start:end]


def test_observation_details_have_readable_fields_and_raw_disclosure() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    renderer = _observation_renderer(source)

    assert "Object.entries(observation.details)" in renderer
    assert "renderObservationValue(fieldValue)" in renderer
    assert "Raw retained JSON" in renderer
    assert "JSON.stringify(observation.details, null, 2)" in renderer
    assert renderer.count("<details>") == 1


def test_observation_values_preserve_scalars_and_composites_deterministically() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert 'if (typeof value === "string") return value;' in source
    assert 'if (value === null) return "null";' in source
    assert 'typeof value === "number" || typeof value === "boolean"' in source
    assert "value.map(stableObservationValue)" in source
    assert ".sort(([left], [right]) => left.localeCompare(right))" in source
    assert "JSON.stringify(stableObservationValue(value))" in source


def test_observation_renderer_is_provider_agnostic_and_does_not_promote_values_to_links() -> None:
    source = CASE_UI.read_text(encoding="utf-8")
    renderer = _observation_renderer(source)

    assert "Object.entries(observation.details)" in renderer
    assert "http://" not in renderer
    assert "https://" not in renderer
    assert "<a " not in renderer
    assert "href=" not in renderer


def test_converged_and_non_converged_paths_share_one_observation_renderer() -> None:
    source = CASE_UI.read_text(encoding="utf-8")

    assert source.count("<ObservationDetails observation={observation} />") == 2
    assert source.count("<pre>{JSON.stringify(observation.details, null, 2)}</pre>") == 1
