import logging
from fastapi import HTTPException, status
from typing import List, Dict, Any, Tuple
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from app.config import settings
from app.vectordb.chroma_client import get_db_client
from app.models.schemas import ChatMessage, SourceCitation, SourceScore

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.db_client = get_db_client()
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> BaseChatModel:
        """
        Dynamically initializes the selected LLM provider.
        """
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY is missing from environment. Chat model will fail to initialize.")
                return None
            try:
                from langchain_openai import ChatOpenAI
                logger.info("Initializing ChatOpenAI (gpt-4o-mini)...")
                return ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model="gpt-4o-mini",
                    temperature=0.2
                )
            except Exception as e:
                logger.error(f"Failed to load ChatOpenAI: {e}")
                return None
                
        elif provider == "google":
            if not settings.GOOGLE_API_KEY:
                logger.error("GOOGLE_API_KEY is missing from environment. Chat model will fail to initialize.")
                return None
            
            candidates = [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]
            
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            for model_name in candidates:
                try:
                    logger.info(f"Testing Gemini model candidate: {model_name}...")
                    test_llm = ChatGoogleGenerativeAI(
                        google_api_key=settings.GOOGLE_API_KEY,
                        model=model_name,
                        temperature=0.2
                    )
                    # Perform a simple check to verify if the key has access to the model
                    test_llm.invoke("Hi")
                    logger.info(f"Successfully initialized ChatGoogleGenerativeAI with model: {model_name}")
                    return test_llm
                except Exception as e:
                    logger.warning(f"Gemini model candidate {model_name} failed: {e}")
            
            logger.error("All Gemini LLM model candidates failed to initialize.")
            return None
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            return None

    def _build_messages(self, query: str, contexts: List[Document], history: List[ChatMessage]) -> List[Any]:
        """
        Builds the structured message prompts including context and conversation history.
        """
        system_prompt = (
            "You are an enterprise knowledge assistant. Answer the user's question using ONLY the provided contexts below. "
            "If the context does not contain the answer or is insufficient, clearly state: "
            "'I cannot find the answer to this in the uploaded documents.' "
            "Do not make up facts or use external knowledge outside the provided contexts.\n\n"
            "Contexts:\n"
        )
        
        for idx, doc in enumerate(contexts):
            source = doc.metadata.get("filename", "Unknown Source")
            page = doc.metadata.get("page", 1)
            system_prompt += f"--- Context {idx + 1} (Source: {source}, Page: {page}) ---\n"
            system_prompt += f"{doc.page_content}\n\n"
            
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history
        for msg in history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
                
        # Add current user message
        messages.append(HumanMessage(content=query))
        return messages

    async def generate_response(self, query: str, history: List[ChatMessage]) -> Tuple[str, List[SourceScore], List[SourceCitation]]:
        """
        Retrieves context documents with distance scores, builds messages, calls the LLM,
        and formats sources with normalized relevance scores and citations.
        """
        # Log structured information: query received
        logger.info(f"Query received: '{query}'")
        
        # 1. Retrieve relevant contexts with distance scores (HCL compliance: k=5)
        retrieved_docs_with_scores = self.db_client.similarity_search_with_scores(query, k=5)
        
        # Log structured information: retrieved chunks count (raw count from database)
        logger.info(f"Retrieved chunks count: {len(retrieved_docs_with_scores)}")
        
        # Filter chunks by relevance threshold and compute scores
        # ChromaDB default space is 'l2' (squared L2 distance).
        # For unit-normalized embeddings, squared L2 distance d is related to cosine similarity by:
        # d = ||u - v||^2 = ||u||^2 + ||v||^2 - 2 * (u . v) = 1 + 1 - 2 * cosine_similarity = 2 * (1 - cosine_similarity).
        # Therefore, cosine_similarity = 1.0 - (d / 2.0).
        # To normalize this cosine similarity metric into a [0, 1] range:
        # relevance_score = max(0.0, min(1.0, 1.0 - (d / 2.0))).
        relevant_docs_with_scores = []
        for doc, distance in retrieved_docs_with_scores:
            score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
            if score >= settings.RELEVANCE_THRESHOLD:
                relevant_docs_with_scores.append((doc, distance, score))
        
        # Sort relevant chunks by relevance score descending to ensure top-5 relevance ordering
        relevant_docs_with_scores.sort(key=lambda x: x[2], reverse=True)
        
        # Log structured information: chunk scores
        chunk_scores = [round(x[2], 4) for x in relevant_docs_with_scores]
        logger.info(f"Chunk scores: {chunk_scores}")
        
        # If no chunks are relevant, bypass Gemini LLM and return standardized response
        if not relevant_docs_with_scores:
            logger.info("No results detected")
            logger.info("Unique documents matched: []")
            logger.info("Ranked document scores: []")
            return "No relevant information found in the knowledge base.", [], []
            
        # 2. Check if LLM is initialized
        if self.llm is None:
            # Re-attempt initialization in case API keys were added dynamically
            self.llm = self._initialize_llm()
            if self.llm is None:
                logger.error(f"LLM initialization failed for provider '{settings.LLM_PROVIDER}'. Keys are missing or invalid.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"LLM Provider '{settings.LLM_PROVIDER}' is not configured. Please configure API key in the environment."
                )

        # 3. Construct prompt messages using only the relevant document chunks
        retrieved_docs = [doc for doc, _, _ in relevant_docs_with_scores]
        messages = self._build_messages(query, retrieved_docs, history)
        
        try:
            logger.info("Invoking LLM chain...")
            llm_result = await self.llm.ainvoke(messages)
            response_text = str(llm_result.content)
            
            # 4. Calculate relevance scores and format unique sources sorted by score descending
            file_scores = {}
            for doc, _, score in relevant_docs_with_scores:
                file_path = doc.metadata.get("filename", "Unknown Source")
                if file_path not in file_scores or score > file_scores[file_path]:
                    file_scores[file_path] = score
            
            sources = [
                SourceScore(file_path=fp, score=round(sc, 4))
                for fp, sc in file_scores.items()
            ]
            # Sort sources descending by score
            sources.sort(key=lambda x: x.score, reverse=True)
            
            # Log structured information: unique documents matched and ranked document scores
            unique_docs = list(file_scores.keys())
            ranked_scores = [sc.score for sc in sources]
            logger.info(f"Unique documents matched: {unique_docs}")
            logger.info(f"Ranked document scores: {ranked_scores}")
            
            # 5. Process and format citations
            citations = []
            seen_snippets = set()
            for doc, _, _ in relevant_docs_with_scores:
                snippet = doc.page_content.strip()
                # Skip empty or whitespace-only snippets
                if not snippet:
                    continue
                if snippet in seen_snippets:
                    continue
                seen_snippets.add(snippet)
                
                # Coerce page metadata to integer safely
                page_raw = doc.metadata.get("page", 1)
                try:
                    page = int(page_raw)
                except (ValueError, TypeError):
                    page = 1
                
                citations.append(
                    SourceCitation(
                        source=doc.metadata.get("filename", "Unknown Source"),
                        page=page,
                        snippet=snippet[:250] + "..." if len(snippet) > 250 else snippet
                    )
                )
            
            # Log structured citation details
            logger.info(f"Citations generated count: {len(citations)}")
            logger.info(f"Citation sources used: {list(set(c.source for c in citations))}")
                
            return response_text, sources, citations
            
        except Exception as e:
            logger.error(f"Error during LLM inference: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM inference failed: {str(e)}"
            )

llm_service = LLMService()

def get_llm_service() -> LLMService:
    return llm_service
