"""
Tests for the RAG retrieval pipeline logic inside LLMService.

Covers:
  - Top-5 retrieval validation (k=5)
  - Relevance score computation and threshold filtering
  - Source ranking (descending by score)
  - Document deduplication (highest score kept per file)
  - Citation generation
  - Citation schema validation
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from langchain_core.documents import Document

from app.services.llm_service import LLMService
from app.models.schemas import SourceScore, SourceCitation
from app.config import settings


# ---------------------------------------------------------------------------
# Helper: build a patched LLMService without touching real ChromaDB / LLM
# ---------------------------------------------------------------------------
def _make_service(mock_search_results, mock_llm_content="Mocked LLM answer."):
    """Create an LLMService with mocked DB client and LLM."""
    svc = object.__new__(LLMService)  # skip __init__
    svc.db_client = MagicMock()
    svc.db_client.similarity_search_with_scores = MagicMock(
        return_value=mock_search_results
    )
    svc.llm = MagicMock()
    svc.llm.ainvoke = AsyncMock(
        return_value=MagicMock(content=mock_llm_content)
    )
    return svc


def _run(coro):
    """Python 3.13-compatible wrapper for running a coroutine synchronously."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 1. Top-5 retrieval validation
# ---------------------------------------------------------------------------
class TestTop5Retrieval:
    def test_similarity_search_called_with_k5(self):
        """The service must call similarity_search_with_scores with k=5."""
        docs = [
            (Document(page_content=f"chunk {i}", metadata={"filename": "f.txt", "page": 1}), 0.2)
            for i in range(5)
        ]
        svc = _make_service(docs)

        _run(svc.generate_response("test query", []))

        svc.db_client.similarity_search_with_scores.assert_called_once_with(
            "test query", k=5
        )

    def test_all_five_chunks_passed_to_llm(self):
        """When 5 chunks pass the threshold, all 5 should be included in
        the LLM prompt context."""
        docs = [
            (Document(page_content=f"chunk {i}", metadata={"filename": f"file_{i}.txt", "page": 1}), 0.2)
            for i in range(5)
        ]
        svc = _make_service(docs)

        answer, sources, citations = _run(svc.generate_response("test query", []))

        # LLM was invoked
        svc.llm.ainvoke.assert_called_once()
        # All 5 unique files should appear
        assert len(sources) == 5
        assert len(citations) == 5


# ---------------------------------------------------------------------------
# 2. Relevance score validation
# ---------------------------------------------------------------------------
class TestRelevanceScore:
    def test_score_computation_from_l2_distance(self):
        """Verify the formula: score = max(0, min(1, 1.0 - distance/2.0))."""
        # distance=0.0 → score=1.0, distance=0.4 → score=0.80
        docs = [
            (Document(page_content="perfect match", metadata={"filename": "a.pdf", "page": 1}), 0.0),
            (Document(page_content="good match", metadata={"filename": "b.pdf", "page": 1}), 0.4),
        ]
        svc = _make_service(docs)

        _, sources, _ = _run(svc.generate_response("query", []))

        assert sources[0].score == 1.0
        assert sources[1].score == 0.8

    def test_threshold_filters_low_scores(self):
        """Chunks with scores below RELEVANCE_THRESHOLD should be excluded."""
        original_threshold = settings.RELEVANCE_THRESHOLD
        try:
            settings.RELEVANCE_THRESHOLD = 0.5
            docs = [
                (Document(page_content="relevant", metadata={"filename": "a.pdf", "page": 1}), 0.2),   # score=0.90
                (Document(page_content="irrelevant", metadata={"filename": "b.pdf", "page": 1}), 1.4), # score=0.30
            ]
            svc = _make_service(docs)

            _, sources, _ = _run(svc.generate_response("query", []))

            # Only the first document should pass the threshold
            assert len(sources) == 1
            assert sources[0].file_path == "a.pdf"
        finally:
            settings.RELEVANCE_THRESHOLD = original_threshold

    def test_all_below_threshold_returns_fallback(self):
        """When all chunks fall below the threshold, LLM should be bypassed."""
        original_threshold = settings.RELEVANCE_THRESHOLD
        try:
            settings.RELEVANCE_THRESHOLD = 0.99
            docs = [
                (Document(page_content="c1", metadata={"filename": "x.txt", "page": 1}), 0.1),  # score=0.95
            ]
            svc = _make_service(docs)

            answer, sources, citations = _run(svc.generate_response("query", []))

            assert answer == "No relevant information found in the knowledge base."
            assert sources == []
            assert citations == []
            svc.llm.ainvoke.assert_not_called()
        finally:
            settings.RELEVANCE_THRESHOLD = original_threshold

    def test_score_clamped_to_zero_for_large_distance(self):
        """Distances > 2.0 should produce a score clamped at 0.0."""
        original_threshold = settings.RELEVANCE_THRESHOLD
        try:
            settings.RELEVANCE_THRESHOLD = 0.0
            docs = [
                (Document(page_content="far away", metadata={"filename": "z.txt", "page": 1}), 3.0),
            ]
            svc = _make_service(docs)

            _, sources, _ = _run(svc.generate_response("query", []))

            assert len(sources) == 1
            assert sources[0].score == 0.0
        finally:
            settings.RELEVANCE_THRESHOLD = original_threshold


# ---------------------------------------------------------------------------
# 3. Source ranking validation
# ---------------------------------------------------------------------------
class TestSourceRanking:
    def test_sources_sorted_descending_by_score(self):
        """Returned sources must be sorted highest score first."""
        docs = [
            (Document(page_content="c1", metadata={"filename": "low.pdf", "page": 1}), 1.0),   # score=0.50
            (Document(page_content="c2", metadata={"filename": "high.pdf", "page": 1}), 0.1),  # score=0.95
            (Document(page_content="c3", metadata={"filename": "mid.pdf", "page": 1}), 0.6),   # score=0.70
        ]
        svc = _make_service(docs)

        _, sources, _ = _run(svc.generate_response("query", []))

        scores = [s.score for s in sources]
        assert scores == sorted(scores, reverse=True)
        assert sources[0].file_path == "high.pdf"
        assert sources[-1].file_path == "low.pdf"

    def test_single_source_ranking(self):
        """A single source should still be returned as a list of length 1."""
        docs = [
            (Document(page_content="only one", metadata={"filename": "solo.pdf", "page": 1}), 0.4),
        ]
        svc = _make_service(docs)

        _, sources, _ = _run(svc.generate_response("query", []))

        assert len(sources) == 1


# ---------------------------------------------------------------------------
# 4. Deduplication validation
# ---------------------------------------------------------------------------
class TestDeduplication:
    def test_same_file_multiple_chunks_returns_once(self):
        """When multiple chunks come from the same file, the file should
        appear once in sources with the highest score."""
        docs = [
            (Document(page_content="chunk A", metadata={"filename": "doc.pdf", "page": 1}), 0.1),  # score=0.95
            (Document(page_content="chunk B", metadata={"filename": "doc.pdf", "page": 3}), 0.6),  # score=0.70
            (Document(page_content="chunk C", metadata={"filename": "doc.pdf", "page": 5}), 1.0),  # score=0.50
        ]
        svc = _make_service(docs)

        _, sources, _ = _run(svc.generate_response("query", []))

        assert len(sources) == 1
        assert sources[0].file_path == "doc.pdf"
        assert sources[0].score == 0.95  # highest score kept

    def test_mixed_files_deduplication(self):
        """A mix of files should be deduplicated correctly, keeping the
        maximum score for each unique filename."""
        docs = [
            (Document(page_content="b1", metadata={"filename": "b.pdf", "page": 1}), 0.1),   # score=0.95
            (Document(page_content="b2", metadata={"filename": "b.pdf", "page": 2}), 0.6),   # score=0.70
            (Document(page_content="a1", metadata={"filename": "a.pdf", "page": 1}), 0.2),   # score=0.90
            (Document(page_content="a2", metadata={"filename": "a.pdf", "page": 4}), 0.3),   # score=0.85
            (Document(page_content="c1", metadata={"filename": "c.pdf", "page": 1}), 0.8),   # score=0.60
        ]
        svc = _make_service(docs)

        _, sources, _ = _run(svc.generate_response("query", []))

        assert len(sources) == 3

        # Check descending order
        assert sources[0].file_path == "b.pdf"
        assert abs(sources[0].score - 0.95) < 1e-4

        assert sources[1].file_path == "a.pdf"
        assert abs(sources[1].score - 0.90) < 1e-4

        assert sources[2].file_path == "c.pdf"
        assert abs(sources[2].score - 0.60) < 1e-4


# ---------------------------------------------------------------------------
# 5. Citation generation
# ---------------------------------------------------------------------------
class TestCitationGeneration:
    def test_citations_generated_for_each_unique_chunk(self):
        """Each unique chunk should produce one citation entry."""
        docs = [
            (Document(page_content="Chunk 1 text.", metadata={"filename": "f.pdf", "page": 1}), 0.2),
            (Document(page_content="Chunk 2 text.", metadata={"filename": "f.pdf", "page": 2}), 0.4),
            (Document(page_content="Chunk 3 text.", metadata={"filename": "g.pdf", "page": 1}), 0.6),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 3

    def test_duplicate_snippets_are_deduplicated(self):
        """If two chunks have identical page_content, only one citation should be generated."""
        docs = [
            (Document(page_content="Same text.", metadata={"filename": "f.pdf", "page": 1}), 0.2),
            (Document(page_content="Same text.", metadata={"filename": "f.pdf", "page": 2}), 0.4),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 1

    def test_long_snippet_is_truncated(self):
        """Snippets longer than 250 characters should be truncated with '...'."""
        long_text = "A" * 300
        docs = [
            (Document(page_content=long_text, metadata={"filename": "f.pdf", "page": 1}), 0.2),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 1
        assert citations[0].snippet.endswith("...")
        assert len(citations[0].snippet) == 253  # 250 chars + "..."

    def test_no_chunks_produces_no_citations(self):
        """When no chunks pass the threshold, citations should be empty."""
        original_threshold = settings.RELEVANCE_THRESHOLD
        try:
            settings.RELEVANCE_THRESHOLD = 0.99
            docs = [
                (Document(page_content="text", metadata={"filename": "f.pdf", "page": 1}), 0.2),  # score=0.90
            ]
            svc = _make_service(docs)

            _, _, citations = _run(svc.generate_response("query", []))

            assert citations == []
        finally:
            settings.RELEVANCE_THRESHOLD = original_threshold

    def test_citation_originates_from_retrieved_docs_and_matches_filenames(self):
        """Verify that every citation matches the content and filename of retrieved docs."""
        docs = [
            (Document(page_content="Unique chunk content alpha.", metadata={"filename": "alpha.pdf", "page": 1}), 0.2),
            (Document(page_content="Unique chunk content beta.", metadata={"filename": "beta.txt", "page": 2}), 0.4),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 2
        for citation in citations:
            # Check source exists in retrieved documents
            assert citation.source in ["alpha.pdf", "beta.txt"]
            # Check snippet content originates from retrieved page_content
            matching_doc = next((d[0] for d in docs if d[0].metadata["filename"] == citation.source), None)
            assert matching_doc is not None
            assert citation.snippet in matching_doc.page_content

    def test_citation_snippets_are_never_empty(self):
        """Verify that chunks with empty/whitespace page_content are ignored and generate no citations."""
        docs = [
            (Document(page_content="   ", metadata={"filename": "empty.pdf", "page": 1}), 0.2),
            (Document(page_content="", metadata={"filename": "empty.pdf", "page": 2}), 0.3),
            (Document(page_content="Valid snippet", metadata={"filename": "valid.pdf", "page": 1}), 0.4),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 1
        assert citations[0].source == "valid.pdf"
        assert citations[0].snippet == "Valid snippet"


# ---------------------------------------------------------------------------
# 6. Citation schema validation
# ---------------------------------------------------------------------------
class TestCitationSchema:
    def test_citation_has_required_fields_and_types(self):
        """Each citation must contain source (str), page (int), and snippet (str) fields."""
        docs = [
            (Document(page_content="Test content.", metadata={"filename": "test.pdf", "page": 3}), 0.2),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 1
        c = citations[0]
        assert isinstance(c, SourceCitation)
        assert isinstance(c.source, str)
        assert c.source == "test.pdf"
        assert isinstance(c.page, int)
        assert c.page == 3
        assert isinstance(c.snippet, str)
        assert c.snippet == "Test content."

    def test_source_score_has_required_fields(self):
        """Each source must contain file_path and score fields."""
        docs = [
            (Document(page_content="text", metadata={"filename": "abc.pdf", "page": 1}), 0.3),
        ]
        svc = _make_service(docs)

        _, sources, _ = _run(svc.generate_response("query", []))

        assert len(sources) == 1
        s = sources[0]
        assert isinstance(s, SourceScore)
        assert s.file_path == "abc.pdf"
        assert isinstance(s.score, float)
        assert 0.0 <= s.score <= 1.0

    def test_citation_defaults_page_to_1(self):
        """When metadata has no 'page' key, the citation should default to page 1."""
        docs = [
            (Document(page_content="No page metadata.", metadata={"filename": "notes.txt"}), 0.2),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert citations[0].page == 1

    def test_citation_page_invalid_type_coercion(self):
        """When the metadata 'page' key is an invalid format (string or float), it must default to an integer 1."""
        docs = [
            (Document(page_content="String page.", metadata={"filename": "test.pdf", "page": "two"}), 0.2),
            (Document(page_content="Float page.", metadata={"filename": "test.pdf", "page": 5.7}), 0.3),
        ]
        svc = _make_service(docs)

        _, _, citations = _run(svc.generate_response("query", []))

        assert len(citations) == 2
        # Both must be coerced to integer 1 and 5 respectively
        assert isinstance(citations[0].page, int)
        assert citations[0].page == 1
        assert isinstance(citations[1].page, int)
        assert citations[1].page == 5
