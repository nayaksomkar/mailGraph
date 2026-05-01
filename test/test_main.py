from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "status" in resp.json()

def test_list_emails():
    resp = client.get("/emails")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_search():
    resp = client.get("/search?q=test")
    assert resp.status_code == 200

def test_list_drafts():
    resp = client.get("/drafts")
    assert resp.status_code == 200

def test_list_tags():
    resp = client.get("/tags")
    assert resp.status_code == 200

def test_get_nonexistent_email():
    resp = client.get("/emails/nonexistent")
    assert resp.status_code == 404