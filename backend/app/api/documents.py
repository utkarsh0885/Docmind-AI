import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from app.models.schemas import IngestionResponse, DocumentMetadata, MessageResponse
from app.services.storage_service import get_storage_service, StorageService
from app.services.ingestion_service import get_ingestion_service, IngestionService
from app.vectordb.chroma_client import get_db_client, ChromaDBClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=IngestionResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    storage: StorageService = Depends(get_storage_service),
    ingestion: IngestionService = Depends(get_ingestion_service)
):
    """
    Upload and ingest a document. Supported formats: PDF, TXT, MD.
    """
    logger.info(f"Received request to upload file: {file.filename}")
    
    # 1. Save file locally
    saved_path = await storage.save_file(file)
    
    try:
        # 2. Ingest document (parse, chunk, embed, save to ChromaDB)
        result = await ingestion.ingest_file(saved_path)
        
        return IngestionResponse(
            filename=result["filename"],
            status="success",
            chunks_created=result["chunks_created"],
            message=f"Document '{result['filename']}' successfully processed and indexed into {result['chunks_created']} chunks."
        )
    except Exception as e:
        logger.error(f"Error during ingestion of {file.filename}: {e}")
        # Clean up file on disk if indexing failed
        storage.delete_file(file.filename or "")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )

@router.get("", response_model=List[DocumentMetadata])
def list_documents(db: ChromaDBClient = Depends(get_db_client)):
    """
    List all unique ingested documents from the vector database.
    """
    try:
        files = db.list_ingested_files()
        
        # Convert raw database summaries to schema models
        response = []
        for idx, f in enumerate(files):
            response.append(
                DocumentMetadata(
                    id=str(idx),
                    filename=f["filename"],
                    size_bytes=f["size_bytes"],
                    upload_time=f["upload_time"],
                    chunk_count=f["chunk_count"]
                )
            )
        return response
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

@router.delete("/{filename}", response_model=MessageResponse)
def delete_document(
    filename: str,
    storage: StorageService = Depends(get_storage_service),
    ingestion: IngestionService = Depends(get_ingestion_service)
):
    """
    Delete a document from both the vector store and disk storage.
    """
    logger.info(f"Received request to delete document: {filename}")
    
    # 1. Remove from vector database
    db_removed = ingestion.remove_document(filename)
    
    # 2. Remove from disk storage
    disk_removed = storage.delete_file(filename)
    
    if not db_removed and not disk_removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{filename}' not found in database or storage."
        )
        
    return MessageResponse(
        message=f"Successfully deleted document '{filename}' from database and disk storage."
    )
