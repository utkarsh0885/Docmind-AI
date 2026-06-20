import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_service import get_llm_service, LLMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post(
    "/query",
    response_model=ChatResponse,
    responses={
        200: {
            "description": (
                "Successful query response. Retrieves the top 5 semantically relevant chunks. "
                "If relevant chunks are found, returns the assistant's synthesized response with "
                "sources and citations. If no relevant chunks match the relevance threshold, "
                "bypasses Gemini and returns a standardized fallback answer."
            ),
            "content": {
                "application/json": {
                    "examples": {
                        "successful_rag": {
                            "summary": "Successful Context Retrieval",
                            "description": "Returned when relevant documents exist and Gemini synthesizes an answer.",
                            "value": {
                                "answer": "The standard remote work policy at HCLTech in 2026 permits employees to work up to 3 days from home per week, requiring line manager approval.",
                                "response": "The standard remote work policy at HCLTech in 2026 permits employees to work up to 3 days from home per week, requiring line manager approval.",
                                "sources": [
                                    {"file_path": "hcltech_policy_2026.txt", "score": 0.9421}
                                ],
                                "citations": [
                                    {
                                        "source": "hcltech_policy_2026.txt",
                                        "page": 1,
                                        "snippet": "Policy 101 - Remote Work Arrangement: The standard remote work policy at HCLTech in 2026 permits employees to work up to 3 days from home per week..."
                                    }
                                ]
                            }
                        },
                        "no_results_fallback": {
                            "summary": "No Relevant Results",
                            "description": "Returned when no chunks pass the relevance threshold, bypassing Gemini.",
                            "value": {
                                "answer": "No relevant information found in the knowledge base.",
                                "response": "No relevant information found in the knowledge base.",
                                "sources": [],
                                "citations": []
                            }
                        }
                    }
                }
            }
        }
    }
)
async def query_knowledge_base(
    request: ChatRequest,
    llm: LLMService = Depends(get_llm_service)
):
    """
    Query the knowledge assistant.
    
    Performs vector search retrieval (retrieving the top 5 semantically relevant chunks),
    filters chunks by relevance threshold, builds conversational prompt context using only
    relevant chunks, and returns LLM response with citations.
    
    If no chunks are found or none pass the relevance threshold:
    - Bypasses LLM (Gemini) call to optimize latency and api token consumption.
    - Returns HTTP 200 with standard fallback answer response.
    """
    logger.info(f"Received query: '{request.message}' with history length {len(request.history)}")
    
    try:
        response_text, sources, citations = await llm.generate_response(
            query=request.message,
            history=request.history
        )
        
        return ChatResponse(
            answer=response_text,
            response=response_text,
            sources=sources,
            citations=citations
        )
    except Exception as e:
        logger.error(f"Error executing knowledge query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your query: {str(e)}"
        )
