from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.db import get_db

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_checks_database():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_readiness_hides_database_error():
    class BrokenDB:
        def execute(self, query):
            raise RuntimeError("private connection detail")

    def broken_db():
        yield BrokenDB()

    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.get("/health/ready")
    finally:
        app.dependency_overrides.pop(get_db)
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"
    assert "private connection detail" not in response.text


def test_upload_rejects_file_over_limit(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_size_mb", 1)
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large.txt", b"a" * (1024 * 1024 + 1), "text/plain")},
    )
    assert response.status_code == 413


def test_upload_hides_parser_error_details():
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("invalid.docx", b"not a valid DOCX", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Could not parse document" in response.json()["detail"]
    assert "not a valid DOCX" not in response.text


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
    uploaded = client.post(
        "/api/v1/documents/upload",
        files={"file": ("edit-test.txt", b"Migration notes.", "text/plain")},
    )
    assert uploaded.status_code == 200
    document_id = uploaded.json()["id"]
    response = client.post(
        f"/api/v1/documents/{document_id}/edit",
        json={"text": "The migration had many problems and it was delayed.", "operation": "professional"},
    )
    assert response.status_code == 200
    assert response.json()["original_text"] != response.json()["suggested_text"]
