import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.api import chat, documents

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    description="Production-grade API for semantic search, document ingestion, and context-aware chat assistants.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request processing time middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error {exc.status_code} at {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Combine validation error details into a clean human-readable string
    err_msgs = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err["loc"] if l != "body")
        msg = err["msg"]
        err_msgs.append(f"'{loc}': {msg}" if loc else msg)
    
    combined_msg = "Validation error: " + "; ".join(err_msgs)
    logger.error(f"Validation error at {request.url.path}: {combined_msg}")
    return JSONResponse(
        status_code=400,  # Map validation errors to 400 Bad Request
        content={
            "error": True,
            "message": combined_msg
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled error at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An internal server error occurred. Please contact system support."
        }
    )

# Register routers
app.include_router(chat.router)
app.include_router(documents.router)

@app.on_event("startup")
def startup_event():
    import sys
    from app.embeddings.factory import get_cached_embeddings, MockEmbeddings
    
    # Pre-warm cache and evaluate model
    embeddings_model = get_cached_embeddings()
    is_fallback = isinstance(embeddings_model, MockEmbeddings)
    
    llm_provider = settings.LLM_PROVIDER
    has_google_key = settings.GOOGLE_API_KEY is not None and len(settings.GOOGLE_API_KEY.strip()) > 0
    has_openai_key = settings.OPENAI_API_KEY is not None and len(settings.OPENAI_API_KEY.strip()) > 0
    
    print("=" * 60, flush=True)
    print("  ENTERPRISE KNOWLEDGE ASSISTANT RUNTIME AUDIT", flush=True)
    print("-" * 60, flush=True)
    print(f"  * LLM Provider:           {llm_provider.upper()}", flush=True)
    
    if llm_provider == "google":
        print(f"  * Google API Key:         {'PRESENT (Production)' if has_google_key else 'MISSING (No Chat)'}", flush=True)
    elif llm_provider == "openai":
        print(f"  * OpenAI API Key:         {'PRESENT (Production)' if has_openai_key else 'MISSING (No Chat)'}", flush=True)
        
    print(f"  * Active Embeddings:      {'Google Generative AI (text-embedding-004)' if not is_fallback else 'MockEmbeddings (Fallback)'}", flush=True)
    print(f"  * Fallback Mode Active:   {str(is_fallback).upper()}", flush=True)
    print("=" * 60, flush=True)
    sys.stdout.flush()

@app.get("/api/health", tags=["health"])
def health_check():
    """
    General API health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "llm_provider": settings.LLM_PROVIDER,
        "allowed_extensions": settings.parsed_allowed_extensions
    }

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    logger.info(f"Starting server in debug mode: {settings.DEBUG}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
