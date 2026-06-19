from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message author: 'user' or 'assistant'")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's query/message")
    history: List[ChatMessage] = Field(default=[], description="Previous conversation history")

class SourceCitation(BaseModel):
    source: str = Field(..., description="Source file name or path")
    page: Optional[int] = Field(None, description="Page number of the citation, if applicable")
    snippet: str = Field(..., description="Snippet of text that was retrieved")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's generated response")
    sources: List[SourceCitation] = Field(default=[], description="List of sources used to generate the response")

class DocumentMetadata(BaseModel):
    id: str = Field(..., description="Unique ID of the document chunk or metadata record")
    filename: str = Field(..., description="Name of the file")
    size_bytes: int = Field(..., description="Size of the file in bytes")
    upload_time: str = Field(..., description="Timestamp of when the file was processed")
    chunk_count: int = Field(..., description="Number of text chunks ingested")

class IngestionResponse(BaseModel):
    filename: str = Field(..., description="Name of the ingested file")
    status: str = Field(..., description="Status of ingestion (e.g., 'success')")
    chunks_created: int = Field(..., description="Number of text chunks created and stored")
    message: str = Field(..., description="Detailed status message")

class MessageResponse(BaseModel):
    message: str = Field(..., description="General message response")
