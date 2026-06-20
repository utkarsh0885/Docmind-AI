"""
Tests for the /api/chat/query endpoint.

Covers:
  - Successful query with relevant chunks
  - Empty / whitespace-only query string
  - No documents uploaded (empty vector DB)
  - No retrieval results passing threshold
  - Invalid request body (missing required fields)
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Successful query — LLM returns an answer with sources and citations
# ---------------------------------------------------------------------------
class TestSuccessfulQuery:
    def test_successful_query_returns_200(self, client):
        """A well-formed query with relevant chunks should return HTTP 200
        with answer, sources, and citations populated."""
        mock_docs_with_scores = [
            (
                Document(
                    page_content="Project Titan is built on FastAPI.",
                    metadata={"filename": "titan.pdf", "page": 1},
                ),
                0.1,  # L2 distance → score ≈ 0.95
            ),
            (
                Document(
                    page_content="It uses cosine similarity for retrieval.",
                    metadata={"filename": "titan.pdf", "page": 2},
                ),
                0.4,  # L2 distance → score ≈ 0.80
            ),
        ]

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Project Titan is built on FastAPI.")
        )

        from app.services.llm_service import llm_service

        original_db = llm_service.db_client
        original_llm = llm_service.llm
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(
                return_value=mock_docs_with_scores
            )
            llm_service.llm = mock_llm

            response = client.post(
                "/api/chat/query",
                json={"message": "What is Project Titan?", "history": []},
            )
        finally:
            llm_service.db_client = original_db
            llm_service.llm = original_llm

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "response" in data
        assert "sources" in data
        assert "citations" in data
        assert len(data["sources"]) > 0
        assert len(data["citations"]) > 0

    def test_response_contains_both_answer_and_response_fields(self, client):
        """Both 'answer' and 'response' fields must be present and identical
        to preserve frontend compatibility."""
        mock_docs = [
            (
                Document(
                    page_content="FastAPI is awesome.",
                    metadata={"filename": "notes.txt", "page": 1},
                ),
                0.2,
            ),
        ]
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="FastAPI is awesome.")
        )

        from app.services.llm_service import llm_service

        original_db = llm_service.db_client
        original_llm = llm_service.llm
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(
                return_value=mock_docs
            )
            llm_service.llm = mock_llm

            resp = client.post(
                "/api/chat/query",
                json={"message": "Tell me about FastAPI", "history": []},
            )
        finally:
            llm_service.db_client = original_db
            llm_service.llm = original_llm

        data = resp.json()
        assert data["answer"] == data["response"]


# ---------------------------------------------------------------------------
# 2. Empty query string (now returns HTTP 400 Bad Request)
# ---------------------------------------------------------------------------
class TestEmptyQuery:
    def test_empty_string_query(self, client):
        """An empty string query should return HTTP 400 with a structured error."""
        resp = client.post(
            "/api/chat/query", json={"message": "", "history": []}
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "cannot be empty" in data["message"]

    def test_whitespace_only_query(self, client):
        """A whitespace-only query should return HTTP 400."""
        resp = client.post(
            "/api/chat/query", json={"message": "   ", "history": []}
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "cannot be empty" in data["message"]


# ---------------------------------------------------------------------------
# 3. No documents uploaded (vector DB is empty)
# ---------------------------------------------------------------------------
class TestNoDocumentsUploaded:
    def test_no_documents_returns_fallback(self, client):
        """When the vector DB returns zero results (no docs ingested),
        the endpoint should return the standard no-results message."""
        from app.services.llm_service import llm_service

        original_db = llm_service.db_client
        original_llm = llm_service.llm
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(
                return_value=[]
            )
            # LLM should NOT be called
            llm_service.llm = MagicMock()
            llm_service.llm.ainvoke = AsyncMock()

            resp = client.post(
                "/api/chat/query",
                json={"message": "What is the remote work policy?", "history": []},
            )
        finally:
            llm_service.db_client = original_db
            llm_service.llm = original_llm

        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "No relevant information found in the knowledge base."
        assert data["sources"] == []
        assert data["citations"] == []


# ---------------------------------------------------------------------------
# 4. No retrieval results passing threshold
# ---------------------------------------------------------------------------
class TestNoRetrievalResults:
    def test_low_relevance_chunks_bypasses_llm(self, client):
        """When all retrieved chunks have scores below the threshold,
        Gemini should be bypassed and the fallback response returned."""
        # All distances produce scores below default threshold (0.35)
        low_score_docs = [
            (
                Document(
                    page_content="Irrelevant chunk",
                    metadata={"filename": "random.txt", "page": 1},
                ),
                1.8,  # score = 1.0 - 1.8/2.0 = 0.1
            ),
            (
                Document(
                    page_content="Another irrelevant chunk",
                    metadata={"filename": "random.txt", "page": 2},
                ),
                1.6,  # score = 1.0 - 1.6/2.0 = 0.2
            ),
        ]

        from app.services.llm_service import llm_service

        original_db = llm_service.db_client
        original_llm = llm_service.llm
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(
                return_value=low_score_docs
            )
            mock_llm = MagicMock()
            mock_llm.ainvoke = AsyncMock()
            llm_service.llm = mock_llm

            resp = client.post(
                "/api/chat/query",
                json={"message": "What is the meaning of life?", "history": []},
            )
        finally:
            llm_service.db_client = original_db
            llm_service.llm = original_llm

        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "No relevant information found in the knowledge base."
        assert data["sources"] == []
        assert data["citations"] == []
        # Verify Gemini was NOT called
        mock_llm.ainvoke.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Invalid request body (returns HTTP 400 Bad Request with unified error response)
# ---------------------------------------------------------------------------
class TestInvalidRequestBody:
    def test_missing_message_field(self, client):
        """Omitting the required 'message' field should return 400."""
        resp = client.post("/api/chat/query", json={"history": []})
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]

    def test_wrong_type_for_message(self, client):
        """Sending a non-string/list message should return 400."""
        resp = client.post(
            "/api/chat/query", json={"message": ["hello"], "history": []}
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]

    def test_malformed_history(self, client):
        """Invalid history entries should return 400."""
        resp = client.post(
            "/api/chat/query",
            json={
                "message": "Hello",
                "history": [{"bad_key": "value"}],
            },
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]

    def test_empty_json_body(self, client):
        """An empty JSON object should return 400."""
        resp = client.post("/api/chat/query", json={})
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]

    def test_no_body_at_all(self, client):
        """Sending no body should return 400."""
        resp = client.post("/api/chat/query")
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        assert "Validation error" in data["message"]


# ---------------------------------------------------------------------------
# 6. Service & Configuration Failures (Gemini errors and missing keys)
# ---------------------------------------------------------------------------
class TestServiceFailures:
    def test_missing_api_keys_returns_500(self, client):
        """When LLM configuration fails due to missing keys, return HTTP 500."""
        from app.services.llm_service import llm_service
        from langchain_core.documents import Document

        mock_docs = [(Document(page_content="relevant info", metadata={"filename": "doc.txt"}), 0.2)]
        original_db = llm_service.db_client
        original_llm = llm_service.llm
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(return_value=mock_docs)
            # Simulate key missing initialization failure
            llm_service.llm = None
            llm_service._initialize_llm = MagicMock(return_value=None)

            resp = client.post(
                "/api/chat/query",
                json={"message": "Query with missing config", "history": []}
            )
        finally:
            llm_service.db_client = original_db
            llm_service.llm = original_llm
            delattr(llm_service, "_initialize_llm")

        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] is True
        assert "not configured" in data["message"]

    def test_gemini_api_failure_returns_502(self, client):
        """When the LLM provider fails during inference, return HTTP 502."""
        from app.services.llm_service import llm_service
        from langchain_core.documents import Document

        mock_docs = [(Document(page_content="relevant info", metadata={"filename": "doc.txt"}), 0.2)]
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API connection refused by Gemini service"))

        original_db = llm_service.db_client
        original_llm = llm_service.llm
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(return_value=mock_docs)
            llm_service.llm = mock_llm

            resp = client.post(
                "/api/chat/query",
                json={"message": "Inference failing query", "history": []}
            )
        finally:
            llm_service.db_client = original_db
            llm_service.llm = original_llm

        assert resp.status_code == 502
        data = resp.json()
        assert data["error"] is True
        assert "inference failed" in data["message"]

