# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]


def _service_by_name(blueprint: dict[str, object], name: str) -> dict[str, object]:
    services = blueprint.get("services")
    assert isinstance(services, list)
    matches = [service for service in services if isinstance(service, dict) and service.get("name") == name]
    assert len(matches) == 1
    return matches[0]


def _env_by_key(service: dict[str, object], key: str) -> dict[str, object]:
    env_vars = service.get("envVars")
    assert isinstance(env_vars, list)
    matches = [item for item in env_vars if isinstance(item, dict) and item.get("key") == key]
    assert len(matches) == 1
    return matches[0]


def test_render_blueprint_keeps_research_api_private() -> None:
    blueprint = yaml.safe_load((REPO_ROOT / "render.yaml").read_text(encoding="utf-8"))
    assert isinstance(blueprint, dict)

    api = _service_by_name(blueprint, "personalattice-api")
    web = _service_by_name(blueprint, "personalattice-web")

    assert api["type"] == "pserv"
    assert api["runtime"] == "docker"
    assert "healthCheckPath" not in api
    assert _env_by_key(api, "PORT")["value"] == "10001"
    assert _env_by_key(api, "PERSONALATTICE_COOKIE_SECURE")["value"] == "true"
    assert _env_by_key(api, "PERSONALATTICE_SESSION_COOKIE")["value"] == "__Host-personalattice_session"

    for secret_key in (
        "PERSONALATTICE_ADMIN_USERNAME",
        "PERSONALATTICE_ADMIN_PASSWORD_HASH",
        "BRAVE_SEARCH_API_KEY",
    ):
        secret = _env_by_key(api, secret_key)
        assert secret.get("sync") is False
        assert "value" not in secret

    disk = api.get("disk")
    assert isinstance(disk, dict)
    assert disk["mountPath"] == "/var/data/personalattice"

    assert web["type"] == "web"
    assert web["rootDir"] == "apps/web"
    assert _env_by_key(web, "NEXT_PUBLIC_API_URL")["value"] == "/api"

    hostport = _env_by_key(web, "PERSONALATTICE_API_HOSTPORT")
    from_service = hostport.get("fromService")
    assert isinstance(from_service, dict)
    assert from_service == {
        "type": "pserv",
        "name": "personalattice-api",
        "property": "hostport",
    }
