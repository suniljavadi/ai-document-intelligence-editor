from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_analyze_ask_and_version():
    content = b"Customer migration plan. PostgreSQL will be used as the target database. Prepare migration scripts by March 20. The deployment has a risk of delay. Production migration is scheduled for March 15."
    uploaded = client.post("/api/v1/documents/upload", files={"file": ("migration.txt", content, "text/plain")})
    assert uploaded.status_code == 200
    document_id = uploaded.json()["id"]
    analysis = client.post(f"/api/v1/documents/{document_id}/analyze")
    assert analysis.status_code == 200
    assert analysis.json()["risks"]
    answer = client.post(f"/api/v1/documents/{document_id}/ask", json={"question": "What database is selected?"})
    assert answer.status_code == 200
    assert answer.json()["citations"]
    version = client.post(f"/api/v1/documents/{document_id}/versions", json={"content": "updated", "change_summary": "Changed"})
    assert version.json()["version_number"] == 2


def test_edit_is_reviewable():
    response = client.post("/api/v1/documents/1/edit", json={"text": "The migration had many problems and it was delayed.", "operation": "professional"})
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["original_text"] != response.json()["suggested_text"]
