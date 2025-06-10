from fastapi.testclient import TestClient
from app.main import app


def test_create_request_with_expiry(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    client = TestClient(app)
    with client:
        resp = client.post("/requests", json={"nickname": "test", "expires_days": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
