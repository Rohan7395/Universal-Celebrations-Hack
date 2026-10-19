import dataclasses

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import eleven
from app.main import app

client = TestClient(app)


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = dataclasses.replace(
        eleven.settings, elevenlabs_api_key="test-key", elevenlabs_agent_id="agent_test"
    )
    monkeypatch.setattr(eleven, "settings", settings)


def test_signed_url_returns_url_and_keeps_key_server_side(
    configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = {}

    def fake_get(url, params, headers, timeout):
        seen.update(url=url, params=params, headers=headers)
        return httpx.Response(200, json={"signed_url": "wss://example/convai?token=abc"})

    monkeypatch.setattr(eleven.httpx, "get", fake_get)
    response = client.get("/api/eleven/signed-url")
    assert response.status_code == 200
    assert response.json() == {"signed_url": "wss://example/convai?token=abc"}
    assert seen["params"] == {"agent_id": "agent_test"}
    assert seen["headers"] == {"xi-api-key": "test-key"}
    assert "test-key" not in response.text


def test_signed_url_maps_upstream_error_to_502(
    configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(eleven.httpx, "get", lambda *a, **k: httpx.Response(401, json={}))
    assert client.get("/api/eleven/signed-url").status_code == 502


def test_signed_url_without_config_is_503(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = dataclasses.replace(eleven.settings, elevenlabs_api_key="", elevenlabs_agent_id="")
    monkeypatch.setattr(eleven, "settings", settings)
    assert client.get("/api/eleven/signed-url").status_code == 503
