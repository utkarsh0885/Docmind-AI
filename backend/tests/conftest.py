"""
Shared pytest fixtures for the Enterprise Knowledge Assistant test suite.

Provides a configured FastAPI test client and common mocks for ChromaDB,
LLM services, storage, and ingestion so that tests run without external
dependencies (no Gemini API calls, no ChromaDB on disk).
"""
import os
# Prevent real LLM and vector database initialization during import/test-collection
os.environ["GOOGLE_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""

from unittest.mock import patch
# Patch ChromaDBClient._initialize_store before importing app modules
patch("app.vectordb.chroma_client.ChromaDBClient._initialize_store", return_value=None).start()

import pytest
import asyncio
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.main import app
from app.config import settings
from app.models.schemas import SourceScore, SourceCitation


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------
@pytest.fixture
def client():
    """Yields a synchronous TestClient bound to the FastAPI application."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Mock LLM that returns a deterministic answer
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_llm():
    """Returns an object whose ainvoke() coroutine yields a fixed response."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        return_value=MagicMock(content="Mocked LLM answer for testing.")
    )
    return llm


# ---------------------------------------------------------------------------
# Helpers: pre-built Document objects
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_documents():
    """Returns a list of LangChain Document objects simulating ChromaDB results."""
    return [
        Document(
            page_content="Project Titan is a secure, cloud-native vector storage server built on FastAPI.",
            metadata={"filename": "titan_overview.pdf", "page": 1},
        ),
        Document(
            page_content="The retrieval pipeline uses cosine similarity matching on text-embedding-004.",
            metadata={"filename": "titan_overview.pdf", "page": 2},
        ),
        Document(
            page_content="Database security rules enforce metadata access boundaries for multitenancy.",
            metadata={"filename": "security_guide.pdf", "page": 5},
        ),
        Document(
            page_content="Team alignment sessions are mandatory on Mondays per remote work policy.",
            metadata={"filename": "hr_policy.txt", "page": 1},
        ),
        Document(
            page_content="Password changes are strictly required every 90 days.",
            metadata={"filename": "security_guide.pdf", "page": 12},
        ),
    ]


@pytest.fixture
def sample_docs_with_distances(sample_documents):
    """
    Pairs each sample document with a mock L2 distance.
    Distances are chosen so that the derived relevance scores are:
      0.95, 0.80, 0.70, 0.55, 0.40  (all above default threshold 0.35).
    Formula: distance = 2.0 * (1.0 - score).
    """
    scores = [0.95, 0.80, 0.70, 0.55, 0.40]
    distances = [2.0 * (1.0 - s) for s in scores]
    return list(zip(sample_documents, distances))
