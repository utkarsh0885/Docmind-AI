import os
import sys
import asyncio
import logging
import unittest.mock as mock

# Set PYTHONPATH to root of backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
        logger.info("=" * 60)
        logger.info("  ALL RELEVANCE THRESHOLD & BYPASS CHECKS PASSED")
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
