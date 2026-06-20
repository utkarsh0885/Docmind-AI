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
# 2. Empty query string
# ---------------------------------------------------------------------------
class TestEmptyQuery:
    def test_empty_string_query(self, client):
        """An empty string query should still return HTTP 200 (the pipeline
        will simply find no relevant chunks)."""
        from app.services.llm_service import llm_service

        original_db = llm_service.db_client
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(
                return_value=[]
            )

            resp = client.post(
                "/api/chat/query", json={"message": "", "history": []}
            )
        finally:
            llm_service.db_client = original_db

        assert resp.status_code == 200
        data = resp.json()
        assert data["sources"] == []
        assert data["citations"] == []

    def test_whitespace_only_query(self, client):
        """A whitespace-only query should behave identically to an empty query."""
        from app.services.llm_service import llm_service

        original_db = llm_service.db_client
        try:
            llm_service.db_client = MagicMock()
            llm_service.db_client.similarity_search_with_scores = MagicMock(
                return_value=[]
            )

            resp = client.post(
                "/api/chat/query", json={"message": "   ", "history": []}
            )
        finally:
            llm_service.db_client = original_db

        assert resp.status_code == 200


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
# 5. Invalid request body
# ---------------------------------------------------------------------------
class TestInvalidRequestBody:
    def test_missing_message_field(self, client):
        """Omitting the required 'message' field should return 422."""
        resp = client.post("/api/chat/query", json={"history": []})
        assert resp.status_code == 422

    def test_wrong_type_for_message(self, client):
        """Sending a non-string message should return 422."""
        resp = client.post(
            "/api/chat/query", json={"message": 12345, "history": []}
        )
        # Pydantic v2 coerces int to str, so this may succeed —
        # but sending a list should fail.
        resp2 = client.post(
            "/api/chat/query", json={"message": ["hello"], "history": []}
        )
        assert resp2.status_code == 422

    def test_malformed_history(self, client):
        """Invalid history entries should return 422."""
        resp = client.post(
            "/api/chat/query",
            json={
                "message": "Hello",
                "history": [{"bad_key": "value"}],
            },
        )
        assert resp.status_code == 422

    def test_empty_json_body(self, client):
        """An empty JSON object should return 422."""
        resp = client.post("/api/chat/query", json={})
        assert resp.status_code == 422

    def test_no_body_at_all(self, client):
        """Sending no body should return 422."""
        resp = client.post("/api/chat/query")
        assert resp.status_code == 422
