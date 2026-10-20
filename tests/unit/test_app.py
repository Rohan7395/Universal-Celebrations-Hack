from fastapi.testclient import TestClient

from app.api.models import Severity
from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
