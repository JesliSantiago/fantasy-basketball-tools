from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_draft_shape():
    body = client.get("/api/draft").json()
    assert set(body) >= {"taken", "mine", "history"}
