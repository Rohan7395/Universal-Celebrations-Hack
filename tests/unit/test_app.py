from fastapi.testclient import TestClient

from app.api.models import FlagResponse, Severity
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_flag_stub_returns_contract_shape() -> None:
    response = client.post(
        "/api/flag",
        json={"client_id": "walter", "what_was_said": "I felt dizzy and fell", "call_id": "c1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"severity", "actions", "say"}
    parsed = FlagResponse.model_validate(body)
    assert parsed.severity is Severity.URGENT
    assert parsed.say


def test_flag_call_id_is_optional() -> None:
    response = client.post("/api/flag", json={"client_id": "walter", "what_was_said": "hi"})
    assert response.status_code == 200


def test_flag_rejects_missing_fields() -> None:
    assert client.post("/api/flag", json={"client_id": "walter"}).status_code == 422


def test_severity_rank_order() -> None:
    assert [s.rank for s in Severity] == [0, 1, 2, 3]
    assert Severity.EMERGENCY.rank > Severity.URGENT.rank > Severity.WATCH.rank


def test_serves_web_dir_when_present(tmp_path, monkeypatch) -> None:
    from dataclasses import replace

    import app.main as main

    (tmp_path / "index.html").write_text("<h1>dashboard</h1>")
    monkeypatch.setattr(main, "settings", replace(main.settings, web_dir=tmp_path))
    web_client = TestClient(main.create_app())
    assert "dashboard" in web_client.get("/").text
    assert web_client.get("/api/health").json() == {"status": "ok"}
