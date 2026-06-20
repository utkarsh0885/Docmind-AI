"""
Tests for the /api/documents endpoints.

Covers:
  - Successful document upload (mocked storage + ingestion)
  - Unsupported file type (e.g. .exe)
  - Missing file in request
"""
import io
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.services.storage_service import get_storage_service
from app.services.ingestion_service import get_ingestion_service


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Successful upload
# ---------------------------------------------------------------------------
class TestSuccessfulUpload:
    def test_upload_txt_file_returns_201(self, client):
        """Uploading a valid .txt file should return 201 with ingestion details."""
        fake_content = b"This is a test document for ingestion."

        mock_storage = MagicMock()
        mock_storage.save_file = AsyncMock(return_value="/tmp/test_doc.txt")

        mock_ingestion = MagicMock()
        mock_ingestion.ingest_file = AsyncMock(
            return_value={
                "filename": "test_doc.txt",
                "chunks_created": 3,
                "size_bytes": len(fake_content),
            }
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion
        try:
            resp = client.post(
                "/api/documents/upload",
                files={"file": ("test_doc.txt", io.BytesIO(fake_content), "text/plain")},
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"] == "test_doc.txt"
        assert data["status"] == "success"
        assert data["chunks_created"] == 3
        assert "message" in data

    def test_upload_pdf_file_returns_201(self, client):
        """Uploading a valid .pdf file should also return 201."""
        fake_pdf = b"%PDF-1.4 fake pdf content"

        mock_storage = MagicMock()
        mock_storage.save_file = AsyncMock(return_value="/tmp/report.pdf")

        mock_ingestion = MagicMock()
        mock_ingestion.ingest_file = AsyncMock(
            return_value={
                "filename": "report.pdf",
                "chunks_created": 10,
                "size_bytes": len(fake_pdf),
            }
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion
        try:
            resp = client.post(
                "/api/documents/upload",
                files={"file": ("report.pdf", io.BytesIO(fake_pdf), "application/pdf")},
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 201
        assert resp.json()["chunks_created"] == 10


# ---------------------------------------------------------------------------
# 2. Unsupported file type
# ---------------------------------------------------------------------------
class TestUnsupportedFileType:
    def test_upload_exe_returns_400(self, client):
        """Uploading a .exe file should be rejected with HTTP 400 and structured error."""
        mock_storage = MagicMock()
        mock_storage.save_file = AsyncMock(
            side_effect=HTTPException(
                status_code=400,
                detail="File extension '.exe' is not allowed. Supported: pdf, txt, md",
            )
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_ingestion_service] = lambda: MagicMock()
        try:
            resp = client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "malware.exe",
                        io.BytesIO(b"MZ executable"),
                        "application/octet-stream",
                    )
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "not allowed" in data["message"]

    def test_upload_jpg_returns_400(self, client):
        """Uploading a .jpg file should be rejected with HTTP 400."""
        mock_storage = MagicMock()
        mock_storage.save_file = AsyncMock(
            side_effect=HTTPException(
                status_code=400,
                detail="File extension '.jpg' is not allowed. Supported: pdf, txt, md",
            )
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_ingestion_service] = lambda: MagicMock()
        try:
            resp = client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "photo.jpg",
                        io.BytesIO(b"\xff\xd8\xff"),
                        "image/jpeg",
                    )
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "not allowed" in data["message"]


# ---------------------------------------------------------------------------
# 3. Missing file
# ---------------------------------------------------------------------------
class TestMissingFile:
    def test_no_file_field_returns_400(self, client):
        """Sending a POST without the 'file' form field should return 400 (validation error)."""
        resp = client.post("/api/documents/upload")
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]

    def test_wrong_field_name_returns_400(self, client):
        """Sending a file under the wrong field name should return 400 (validation error)."""
        resp = client.post(
            "/api/documents/upload",
            files={
                "document": (
                    "test.txt",
                    io.BytesIO(b"content"),
                    "text/plain",
                )
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]


# ---------------------------------------------------------------------------
# 4. Ingestion Failures (Corrupted PDF & Database Deletion Failures)
# ---------------------------------------------------------------------------
class TestIngestionFailures:
    def test_upload_corrupted_pdf_returns_400(self, client):
        """Uploading a corrupted PDF should result in ValueError mapping to HTTP 400."""
        mock_storage = MagicMock()
        mock_storage.save_file = AsyncMock(return_value="/tmp/corrupted.pdf")

        mock_ingestion = MagicMock()
        mock_ingestion.ingest_file = AsyncMock(
            side_effect=ValueError("Failed to parse PDF document: PDF header signature not found")
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion
        try:
            resp = client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "corrupted.pdf",
                        io.BytesIO(b"corrupted pdf bytes"),
                        "application/pdf",
                    )
                },
            )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Failed to parse PDF document" in data["message"]

    def test_delete_database_failure_returns_500(self, client):
        """Database error during document deletion should return HTTP 500."""
        mock_storage = MagicMock()
        mock_storage.delete_file = MagicMock(return_value=True)

        mock_ingestion = MagicMock()
        mock_ingestion.remove_document = MagicMock(
            side_effect=Exception("ChromaDB connection timeout error")
        )

        app.dependency_overrides[get_storage_service] = lambda: mock_storage
        app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion
        try:
            resp = client.delete("/api/documents/important_doc.pdf")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] is True
        assert "Failed to delete document from database" in data["message"]

