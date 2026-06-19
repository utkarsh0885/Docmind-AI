import os
import logging
from langchain_core.embeddings import Embeddings
from app.config import settings

logger = logging.getLogger("app.embeddings")

class MockEmbeddings(Embeddings):
    """
    Mock embeddings class for local environment startup when external keys
    are not set. Used strictly as a development fallback.
    """
    def __init__(self, size: int = 1536):
        self.size = size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * self.size for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * self.size

class GoogleGeminiEmbeddingsWithFallback(Embeddings):
    """
    Google Gemini Embeddings wrapper that prioritizes models/text-embedding-004,
    falling back to gemini-embedding-001 or embedding-001 automatically if unavailable.
    """
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        # We start with the prioritized model text-embedding-004
        self.model_name = "models/text-embedding-004"
        self.fallback_candidates = ["models/gemini-embedding-001", "models/embedding-001"]
        self._init_client()

    def _init_client(self):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        logger.info(f"Initializing GoogleGenerativeAIEmbeddings with model: {self.model_name}")
        self.client = GoogleGenerativeAIEmbeddings(
            google_api_key=self.google_api_key,
            model=self.model_name
        )

    def _handle_exception(self, e: Exception, method_name: str, *args, **kwargs):
        err_msg = str(e)
        if any(term in err_msg for term in ["NOT_FOUND", "404", "not found", "not supported"]):
            if self.fallback_candidates:
                next_model = self.fallback_candidates.pop(0)
                logger.warning(
                    f"Model {self.model_name} failed. "
                    f"Attempting fallback to: {next_model}..."
                )
                self.model_name = next_model
                self._init_client()
                # Retry call recursively
                method = getattr(self.client, method_name)
                return method(*args, **kwargs)
        raise e

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            return self.client.embed_documents(texts)
        except Exception as e:
            return self._handle_exception(e, "embed_documents", texts)

    def embed_query(self, text: str) -> list[float]:
        try:
            return self.client.embed_query(text)
        except Exception as e:
            return self._handle_exception(e, "embed_query", text)

def get_embedding_model() -> Embeddings:
    """
    Factory function to get the configured embedding model.
    Prioritizes Google Generative AI (text-embedding-004 with fallback) if GOOGLE_API_KEY exists.
    Falls back to development MockEmbeddings if missing.
    """
    api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
    
    if api_key and len(api_key.strip()) > 0:
        try:
            logger.info("GOOGLE_API_KEY validated. Initializing GoogleGeminiEmbeddingsWithFallback...")
            return GoogleGeminiEmbeddingsWithFallback(google_api_key=api_key)
        except Exception as e:
            logger.error(
                f"Failed to initialize GoogleGenerativeAIEmbeddings: {e}. "
                "Falling back to MockEmbeddings for safety."
            )
            return MockEmbeddings()
    else:
        logger.warning(
            "CRITICAL WARNING: GOOGLE_API_KEY is missing from configuration. "
            "Google Gemini embeddings are DISABLED. "
            "Falling back to lightweight MockEmbeddings for local development."
        )
        return MockEmbeddings()

pre_loaded_embeddings = None

def get_cached_embeddings() -> Embeddings:
    """Helper to cache embedding model instantiation."""
    global pre_loaded_embeddings
    if pre_loaded_embeddings is None:
        pre_loaded_embeddings = get_embedding_model()
    return pre_loaded_embeddings
