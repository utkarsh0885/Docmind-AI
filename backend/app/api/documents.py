import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from app.models.schemas import IngestionResponse, DocumentMetadata, MessageResponse, ErrorResponse
from app.services.storage_service import get_storage_service, StorageService
from app.services.ingestion_service import get_ingestion_service, IngestionService
from app.vectordb.chroma_client import get_db_client, ChromaDBClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Document uploaded and ingested successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file type, corrupted file, or missing upload payload"},
        413: {"model": ErrorResponse, "description": "File exceeds maximum size limit"},
        500: {"model": ErrorResponse, "description": "Internal server or database indexing failure"}
    }
)
async def upload_document(
    file: UploadFile = File(...),
    storage: StorageService = Depends(get_storage_service),
    ingestion: IngestionService = Depends(get_ingestion_service)
):
    """
    Upload and ingest a document. Supported formats: PDF, TXT, MD.
    """
    if not file or not file.filename:
        logger.warning("Empty file payload or missing file name.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded or file name is missing."
        )
        
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
    except ValueError as ve:
        logger.error(f"Validation error during ingestion of {file.filename}: {ve}")
        # Clean up file on disk if indexing failed due to validation/parsing failure
        storage.delete_file(file.filename or "")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except HTTPException as he:
        storage.delete_file(file.filename or "")
        raise he
    except Exception as e:
        logger.error(f"Error during ingestion of {file.filename}: {e}")
        # Clean up file on disk if indexing failed
        storage.delete_file(file.filename or "")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )

@router.get(
    "",
    response_model=List[DocumentMetadata],
    responses={
        200: {"description": "List of ingested documents retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Database connection or listing failure"}
    }
)
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
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )

@router.delete(
    "/{filename}",
    response_model=MessageResponse,
    responses={
        200: {"description": "Document deleted successfully"},
        404: {"model": ErrorResponse, "description": "Document not found in storage or database"},
        500: {"model": ErrorResponse, "description": "Database or disk deletion failure"}
    }
)
def delete_document(
    filename: str,
    storage: StorageService = Depends(get_storage_service),
    ingestion: IngestionService = Depends(get_ingestion_service)
):
    """
    Delete a document from both the vector store and disk storage.
    """
    logger.info(f"Received request to delete document: {filename}")
    
    try:
        # 1. Remove from vector database
        db_removed = ingestion.remove_document(filename)
    except Exception as e:
        logger.error(f"Database error during deletion of {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document from database: {str(e)}"
        )
    
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
