import os
import sys
import shutil
import time
import logging

# Set PYTHONPATH to root of backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.vectordb.chroma_client import get_db_client
from app.embeddings.factory import get_cached_embeddings, MockEmbeddings
from app.services.ingestion_service import get_ingestion_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_backend")

def create_temp_file(filename: str, content: str) -> str:
    """Create a temporary text file in the uploads directory."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

async def run_verification():
    logger.info("=" * 60)
    logger.info("  STARTING BACKEND PIPELINE VERIFICATION")
    logger.info("=" * 60)
    
    # 1. Check Configuration & Embeddings
    logger.info("[STEP 1/6] Auditing runtime configuration...")
    embeddings = get_cached_embeddings()
    is_fallback = isinstance(embeddings, MockEmbeddings)
    
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Embeddings Class: {embeddings.__class__.__name__}")
    logger.info(f"Fallback Mode Active: {is_fallback}")
    
    # 2. Setup Vector Database Client
    logger.info("[STEP 2/6] Initializing ChromaDB vector client...")
    db = get_db_client()
    
    # 3. Create Sample Document
    logger.info("[STEP 3/6] Generating sample ingestion document...")
    filename = "verification_doc_temp.txt"
    content = (
        "Enterprise Knowledge Assistant System Verification Document.\n"
        "Fact A: Project Titan is a secure, cloud-native vector storage server built on FastAPI.\n"
        "Fact B: The retrieval pipeline uses cosine similarity matching on text-embedding-004.\n"
        "Fact C: Database security rules enforce metadata access boundaries for multitenancy."
    )
    file_path = create_temp_file(filename, content)
    logger.info(f"Created file at: {file_path}")
    
    try:
        # 4. Ingest and Chunk File
        logger.info("[STEP 4/6] Parsing and indexing document to ChromaDB...")
        ingestion = get_ingestion_service()
        result = await ingestion.ingest_file(file_path)
        logger.info(f"Ingestion response: {result}")
        
        if result["chunks_created"] <= 0:
            raise ValueError("Zero chunks created during ingestion.")
        
        # 5. Semantic Retrieval Verification
        logger.info("[STEP 5/6] Running semantic similarity search query...")
        query = "What is Project Titan built on?"
        search_results = db.similarity_search(query, k=1)
        
        if not search_results:
            raise ValueError("No search results returned from vector database.")
            
        retrieved_chunk = search_results[0]
        logger.info(f"Search Query: '{query}'")
        logger.info(f"Retrieved text: '{retrieved_chunk.page_content}'")
        logger.info(f"Retrieved metadata: {retrieved_chunk.metadata}")
        
        # Validate matching metadata
        if retrieved_chunk.metadata.get("filename") != filename:
            raise ValueError("Retrieved metadata filename mismatch.")
        logger.info("Semantic retrieval citation validation PASSED.")
        
        # 6. Deletion and Cleanup
        logger.info("[STEP 6/6] Purging document chunks and deleting temporary files...")
        db_removed = ingestion.remove_document(filename)
        if not db_removed:
            raise ValueError("ChromaDB failed to delete indexed chunks.")
            
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info("Physical file deleted from disk storage.")
            
        logger.info("Cleanup checks PASSED.")
        
        logger.info("=" * 60)
        logger.info("  ALL PIPELINE VERIFICATION CHECKS PASSED SUCCESSFULLY")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"VERIFICATION FAILURE: {e}", exc_info=True)
        # Attempt cleanup if failed mid-run
        if os.path.exists(file_path):
            os.remove(file_path)
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_verification())
    sys.exit(0 if success else 1)
