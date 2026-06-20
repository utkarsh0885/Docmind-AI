import os
import sys
import asyncio
import logging
import unittest.mock as mock

# Set PYTHONPATH to root of backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.documents import Document
from app.config import settings
from app.vectordb.chroma_client import get_db_client
from app.services.ingestion_service import get_ingestion_service
from app.services.llm_service import get_llm_service

# Configure test logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_no_results")

async def test_relevance_and_bypass():
    logger.info("=" * 60)
    logger.info("  STARTING RELEVANCE THRESHOLD & BYPASS VALIDATION")
    logger.info("=" * 60)
    
    # 1. Initialize services
    db = get_db_client()
    ingestion = get_ingestion_service()
    llm_service = get_llm_service()
    
    # Ensure LLM service has an initialized LLM (or mock it if keys are missing)
    if llm_service.llm is None:
        logger.info("LLM is not initialized in LLMService. Creating a mock LLM for testing.")
        class MockLLM:
            async def ainvoke(self, messages):
                class MockResult:
                    content = "Mocked answer based on context: Project Titan is built on FastAPI."
                return MockResult()
        llm_service.llm = MockLLM()
    
    # Save original configuration so we can restore it later
    original_threshold = settings.RELEVANCE_THRESHOLD
    
    # 2. Ingest a temporary document
    filename = "temp_bypass_test.txt"
    content = "Project Titan is a secure, cloud-native vector storage server built on FastAPI."
    
    # Write temp file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    logger.info(f"Ingesting temp file: {file_path}")
    await ingestion.ingest_file(file_path)
    
    try:
        # Patch/Mock the ainvoke method to track if LLM is called
        original_ainvoke = llm_service.llm.ainvoke
        mock_ainvoke = mock.AsyncMock(return_value=mock.MagicMock(content="Mocked answer based on context: Project Titan is built on FastAPI."))
        llm_service.llm.ainvoke = mock_ainvoke
        
        # Test Case A: Highly related query (should pass threshold, call LLM)
        settings.RELEVANCE_THRESHOLD = 0.1
        logger.info(f"[TEST CASE A] Related query with threshold = {settings.RELEVANCE_THRESHOLD}")
        
        mock_ainvoke.reset_mock()
        answer, sources, citations = await llm_service.generate_response(
            query="What is Project Titan built on?",
            history=[]
        )
        
        logger.info(f"Answer: '{answer}'")
        logger.info(f"Sources: {sources}")
        logger.info(f"Citations count: {len(citations)}")
        
        # Verify LLM was called
        assert mock_ainvoke.called, "FAIL: LLM was NOT called for a highly relevant query!"
        assert len(sources) > 0, "FAIL: Sources list should not be empty for a relevant query."
        logger.info("-> Test Case A PASSED (LLM was invoked, sources/citations returned).")
        logger.info("-" * 60)
        
        # Test Case B: Completely unrelated query (should fail threshold, bypass LLM)
        settings.RELEVANCE_THRESHOLD = 0.8
        logger.info(f"[TEST CASE B] Unrelated query with threshold = {settings.RELEVANCE_THRESHOLD}")
        
        mock_ainvoke.reset_mock()
        answer, sources, citations = await llm_service.generate_response(
            query="What is the capital of France?",
            history=[]
        )
        
        logger.info(f"Answer: '{answer}'")
        logger.info(f"Sources: {sources}")
        logger.info(f"Citations count: {len(citations)}")
        
        # Verify LLM was NOT called
        assert not mock_ainvoke.called, "FAIL: LLM WAS called for an unrelated query! Bypass failed."
        assert answer == "No relevant information found in the knowledge base.", f"FAIL: Unexpected answer: {answer}"
        assert sources == [], f"FAIL: Expected empty sources, got: {sources}"
        assert citations == [], f"FAIL: Expected empty citations, got: {citations}"
        logger.info("-> Test Case B PASSED (LLM was bypassed, returned standard no-results fallback).")
        logger.info("-" * 60)
        
        # Test Case C: Deduplication & Descending Ranking
        logger.info("[TEST CASE C] Deduplication and descending ranking verification")
        
        # Create mock documents
        doc_b1 = Document(page_content="chunk b1", metadata={"filename": "document_b.pdf"})
        doc_b2 = Document(page_content="chunk b2", metadata={"filename": "document_b.pdf"})
        doc_a1 = Document(page_content="chunk a1", metadata={"filename": "document_a.pdf"})
        doc_a2 = Document(page_content="chunk a2", metadata={"filename": "document_a.pdf"})
        doc_c1 = Document(page_content="chunk c1", metadata={"filename": "document_c.pdf"})
        
        # Cosine similarity score = 1.0 - distance / 2.0 -> distance = 2.0 * (1.0 - score)
        # Score 0.95 -> distance = 0.1
        # Score 0.70 -> distance = 0.6
        # Score 0.90 -> distance = 0.2
        # Score 0.85 -> distance = 0.3
        # Score 0.60 -> distance = 0.8
        mock_db_results = [
            (doc_b1, 0.1),  # document_b.pdf score 0.95
            (doc_b2, 0.6),  # document_b.pdf score 0.70
            (doc_a1, 0.2),  # document_a.pdf score 0.90
            (doc_a2, 0.3),  # document_a.pdf score 0.85
            (doc_c1, 0.8),  # document_c.pdf score 0.60
        ]
        
        # Patch db_client.similarity_search_with_scores
        original_search = llm_service.db_client.similarity_search_with_scores
        llm_service.db_client.similarity_search_with_scores = mock.MagicMock(return_value=mock_db_results)
        
        # Set threshold to 0.0 to ensure all are processed
        settings.RELEVANCE_THRESHOLD = 0.0
        
        try:
            mock_ainvoke.reset_mock()
            answer, sources, citations = await llm_service.generate_response(
                query="Verify deduplication and ranking logic",
                history=[]
            )
            
            logger.info(f"Sources returned: {sources}")
            
            # Check deduplication: exactly 3 unique files should remain
            assert len(sources) == 3, f"FAIL: Expected 3 unique sources, got {len(sources)}"
            
            # Check correctness of values and order (descending)
            # Index 0: document_b.pdf (0.95)
            assert sources[0].file_path == "document_b.pdf", f"Expected document_b.pdf at index 0, got {sources[0].file_path}"
            assert abs(sources[0].score - 0.95) < 1e-4, f"Expected score 0.95, got {sources[0].score}"
            
            # Index 1: document_a.pdf (0.90)
            assert sources[1].file_path == "document_a.pdf", f"Expected document_a.pdf at index 1, got {sources[1].file_path}"
            assert abs(sources[1].score - 0.90) < 1e-4, f"Expected score 0.90, got {sources[1].score}"
            
            # Index 2: document_c.pdf (0.60)
            assert sources[2].file_path == "document_c.pdf", f"Expected document_c.pdf at index 2, got {sources[2].file_path}"
            assert abs(sources[2].score - 0.60) < 1e-4, f"Expected score 0.60, got {sources[2].score}"
            
            logger.info("-> Test Case C PASSED (Deduplication correct, max score kept, sorted descending).")
            
        finally:
            # Restore search function
            llm_service.db_client.similarity_search_with_scores = original_search

        logger.info("=" * 60)
        logger.info("  ALL RELEVANCE THRESHOLD, BYPASS, & DEDUPLICATION CHECKS PASSED")
        logger.info("=" * 60)
        
    finally:
        # Restore configuration and mock, then cleanup files
        settings.RELEVANCE_THRESHOLD = original_threshold
        llm_service.llm.ainvoke = original_ainvoke
        logger.info("Cleaning up temp files and database records...")
        ingestion.remove_document(filename)
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    asyncio.run(test_relevance_and_bypass())
