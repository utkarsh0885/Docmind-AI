import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Settings(BaseSettings):
    # API Configurations
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # LLM Configurations
    LLM_PROVIDER: str = "google"  # "google" or "openai"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Vector Database Configurations
    CHROMADB_PERSIST_DIR: str = os.path.join(BASE_DIR, "chroma_db")
    CHROMADB_COLLECTION_NAME: str = "enterprise_knowledge"
    
    # Storage Configurations
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS: str = "pdf,txt,md"
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    @property
    def parsed_allowed_extensions(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMADB_PERSIST_DIR, exist_ok=True)
