import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/query", response_model=ChatResponse)
async def query_knowledge_base(
    request: ChatRequest,
    llm: LLMService = Depends(get_llm_service)
):
    """
    Query the knowledge assistant. Performs vector search retrieval, builds conversational prompt context, and returns LLM response with citations.
    """
    logger.info(f"Received query: '{request.message}' with history length {len(request.history)}")
    
    try:
        response_text, citations = await llm.generate_response(
            query=request.message,
            history=request.history
        )
        
        return ChatResponse(
            response=response_text,
            sources=citations
        )
    except Exception as e:
        logger.error(f"Error executing knowledge query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your query: {str(e)}"
        )
