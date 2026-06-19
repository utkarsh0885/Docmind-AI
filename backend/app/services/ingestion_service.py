import os
import time
import logging
from typing import List, Dict, Any
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import settings
from app.vectordb.chroma_client import get_db_client

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self):
        self.db_client = get_db_client()

    def load_document(self, file_path: str) -> List[Document]:
        """
        Loads document content depending on its file extension.
        """
        ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Loading document: {file_path} (extension: {ext})")
        
        if ext == ".pdf":
            try:
                loader = PyPDFLoader(file_path)
                return loader.load()
            except Exception as e:
                logger.error(f"Failed to load PDF file {file_path}: {e}")
                raise ValueError(f"Failed to parse PDF document: {e}")
        elif ext in [".txt", ".md"]:
            try:
                loader = TextLoader(file_path, encoding="utf-8")
                return loader.load()
            except Exception as e:
                logger.error(f"Failed to load Text/MD file {file_path}: {e}")
                raise ValueError(f"Failed to parse text document: {e}")
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def split_documents(self, documents: List[Document], filename: str, file_size: int) -> List[Document]:
        """
        Splits lists of LangChain documents into chunks, injecting system-level metadata.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        
        chunks = splitter.split_documents(documents)
        upload_time_str = datetime.now().isoformat()
        
        # Enforce metadata standard across all chunks
        for idx, chunk in enumerate(chunks):
            chunk.metadata["filename"] = filename
            chunk.metadata["size_bytes"] = file_size
            chunk.metadata["upload_time"] = upload_time_str
            chunk.metadata["chunk_index"] = idx
            # If PyPDFLoader is used, page metadata is already loaded; ensure it defaults if not present
            if "page" not in chunk.metadata:
                chunk.metadata["page"] = 1
            else:
                # Page metadata is 0-indexed in PyPDF, convert to 1-indexed for display
                chunk.metadata["page"] = int(chunk.metadata["page"]) + 1
                
        return chunks

    async def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load, split, and save a document to the vector database.
        """
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # 1. Load document
        raw_documents = self.load_document(file_path)
        
        # 2. Split documents into chunks
        chunks = self.split_documents(raw_documents, filename, file_size)
        
        # 3. Add to ChromaDB
        self.db_client.add_documents(chunks)
        
        return {
            "filename": filename,
            "chunks_created": len(chunks),
            "size_bytes": file_size
        }

    def remove_document(self, filename: str) -> bool:
        """
        Delete document chunks from ChromaDB. Returns True if database record was removed.
        """
        db_removed = self.db_client.delete_by_filename(filename)
        return db_removed

ingestion_service = IngestionService()

def get_ingestion_service() -> IngestionService:
    return ingestion_service
