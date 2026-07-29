"""Chat API endpoint using Qdrant RAG."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends

from app.services.qdrant_rag_service import QdrantRAGService, RAGResponse


router = APIRouter(prefix="/qdrant", tags=["Qdrant RAG"])


# Singleton service instance
_service: QdrantRAGService | None = None


def get_rag_service() -> QdrantRAGService:
    """Get or create RAG service singleton."""
    global _service
    if _service is None:
        _service = QdrantRAGService()
    return _service


class ChatRequest(BaseModel):
    """Chat request model."""
    
    question: str = Field(..., min_length=1, max_length=500, description="用户问题")
    top_k: int = Field(default=3, ge=1, le=10, description="检索片段数量")


class CitationResponse(BaseModel):
    """Citation in response."""
    
    title: str
    source_type: str
    source_ref: str | None
    score: float


class ChatResponse(BaseModel):
    """Chat response model."""
    
    answer: str
    citations: list[CitationResponse]
    used_qwen: bool
    error: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: QdrantRAGService = Depends(get_rag_service),
) -> ChatResponse:
    """Process a chat query using Qdrant RAG.
    
    This endpoint:
    1. Encodes the question into a vector
    2. Searches similar chunks in Qdrant
    3. Calls Qwen to generate an answer
    4. Returns the answer with citations
    
    Example:
        ```json
        {
            "question": "什么是颜体？",
            "top_k": 3
        }
        ```
    """
    result: RAGResponse = service.chat(
        question=request.question,
        top_k=request.top_k,
    )
    
    return ChatResponse(
        answer=result.answer,
        citations=[
            CitationResponse(
                title=c.title,
                source_type=c.source_type,
                source_ref=c.source_ref,
                score=c.score,
            )
            for c in result.citations
        ],
        used_qwen=result.used_qwen,
        error=result.error,
    )
