import os

os.environ["WEB_LEARNING_ENABLED"] = "false"
os.environ["QDRANT_URL"] = ""
os.environ["QDRANT_API_KEY"] = ""

from app.main import app
from fastapi.testclient import TestClient


def test_healthz():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["ok"] is True
