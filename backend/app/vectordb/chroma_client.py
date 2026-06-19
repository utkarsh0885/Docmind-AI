import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.config import settings
from app.embeddings.factory import get_cached_embeddings

logger = logging.getLogger(__name__)

class ChromaDBClient:
    def __init__(self):
        self.embeddings = get_cached_embeddings()
        self.persist_directory = settings.CHROMADB_PERSIST_DIR
        self.collection_name = settings.CHROMADB_COLLECTION_NAME
        self.vector_store = None
        self._initialize_store()

    def _initialize_store(self):
        try:
            logger.info(f"Initializing ChromaDB vector store at: {self.persist_directory}")
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            logger.info("ChromaDB vector store initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise e

    def get_store(self) -> Chroma:
        if self.vector_store is None:
            self._initialize_store()
        return self.vector_store

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        """
        store = self.get_store()
        try:
            logger.info(f"Adding {len(documents)} document chunks to ChromaDB.")
            ids = store.add_documents(documents)
            logger.info("Successfully added documents to ChromaDB.")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            raise e

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Perform a similarity search in ChromaDB.
        """
        store = self.get_store()
        try:
            logger.info(f"Searching vector database for query: '{query}' (k={k})")
            results = store.similarity_search(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def delete_by_filename(self, filename: str) -> bool:
        """
        Delete all document chunks corresponding to a specific filename.
        """
        store = self.get_store()
        try:
            # Retrieve all document IDs matching the filename metadata
            collection = store._collection
            results = collection.get(
                where={"filename": filename},
                include=["metadatas"]
            )
            ids = results.get("ids", [])
            if not ids:
                logger.info(f"No chunks found in database for filename: {filename}")
                return False

            logger.info(f"Deleting {len(ids)} chunks from ChromaDB for file: {filename}")
            collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Failed to delete chunks for file {filename}: {e}")
            raise e

    def list_ingested_files(self) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB to list all unique files ingested, along with metadata summaries.
        """
        store = self.get_store()
        try:
            collection = store._collection
            results = collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            # Aggregate by filename
            files_dict = {}
            for meta in metadatas:
                if not meta or "filename" not in meta:
                    continue
                
                filename = meta["filename"]
                if filename not in files_dict:
                    files_dict[filename] = {
                        "filename": filename,
                        "size_bytes": meta.get("size_bytes", 0),
                        "upload_time": meta.get("upload_time", "Unknown"),
                        "chunk_count": 0
                    }
                files_dict[filename]["chunk_count"] += 1
                
            return list(files_dict.values())
        except Exception as e:
            logger.error(f"Failed to list ingested files from ChromaDB: {e}")
            return []

db_client = ChromaDBClient()
def get_db_client() -> ChromaDBClient:
    return db_client
