"""Retriever service using Qdrant for vector search."""

from __future__ import annotations

from dataclasses import dataclass

from app.repositories.qdrant_repository import QdrantRepository, KnowledgeChunk
from app.services.embedding_service import EmbeddingService


@dataclass
class RetrievalResult:
    """Result from retrieval operation."""
    
    chunks: list[KnowledgeChunk]
    query: str
    language: str | None


class QdrantRetrieverService:
    """Service for retrieving knowledge chunks using Qdrant."""
    
    def __init__(
        self,
        repository: QdrantRepository | None = None,
        embedding_service: EmbeddingService | None = None,
        use_memory: bool = True,
    ) -> None:
        """Initialize retriever service.
        
        Args:
            repository: QdrantRepository instance
            embedding_service: EmbeddingService instance
            use_memory: If True, use in-memory Qdrant
        """
        self.repository = repository or QdrantRepository(use_memory=use_memory)
        self.embedding_service = embedding_service or EmbeddingService()
    
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        language: str | None = "zh-CN",
        source_type: str | None = None,
    ) -> RetrievalResult:
        """Retrieve knowledge chunks for a query.
        
        Args:
            query: Query text
            limit: Maximum number of results
            language: Filter by language (None for all)
            source_type: Filter by source type (None for all)
            
        Returns:
            RetrievalResult with matching chunks
        """
        # Generate query vector
        query_vector = self.embedding_service.encode_to_list(query)[0]
        
        # Search in Qdrant
        chunks = self.repository.search(
            query_vector=query_vector,
            limit=limit,
            language=language,
            source_type=source_type,
        )
        
        return RetrievalResult(
            chunks=chunks,
            query=query,
            language=language,
        )
    
    def retrieve_with_context(
        self,
        query: str,
        limit: int = 3,
    ) -> tuple[str, list[KnowledgeChunk]]:
        """Retrieve and format context for LLM.
        
        Args:
            query: Query text
            limit: Maximum number of results
            
        Returns:
            Tuple of (formatted_context, chunks)
        """
        result = self.retrieve(query, limit=limit)
        
        if not result.chunks:
            return "", []
        
        # Build context string
        context_parts = []
        for i, chunk in enumerate(result.chunks, 1):
            context_parts.append(f"[{i}] {chunk.text}")
        
        context = "\n\n".join(context_parts)
        return context, result.chunks
