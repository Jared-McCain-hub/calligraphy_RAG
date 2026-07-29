"""Qdrant vector repository for knowledge chunks retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.core.config import settings


@dataclass
class KnowledgeChunk:
    """Represents a knowledge chunk from Qdrant."""
    
    id: str
    text: str
    score: float
    document_id: str
    document_title: str
    chunk_index: int
    language: str
    source_type: str
    source_ref: str | None
    entity_type: str | None
    entity_id: str | None
    entity_name: str | None


class QdrantRepository:
    """Repository for vector operations with Qdrant."""
    
    COLLECTION_NAME = "calligraphy_knowledge"
    VECTOR_SIZE = 768  # sentence-transformers dimension
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = False,
        api_key: str | None = None,
    ) -> None:
        """Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            use_memory: If True, use in-memory mode (no server needed)
            api_key: API key for Qdrant Cloud
        """
        if use_memory:
            self.client = QdrantClient(":memory:")
        elif api_key:
            self.client = QdrantClient(
                url=f"https://{host}",
                api_key=api_key,
            )
        else:
            self.client = QdrantClient(host=host, port=port)
        
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        """Create collection if not exists."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.COLLECTION_NAME for c in collections)
        
        if not exists:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
    
    def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> int:
        """Upsert knowledge chunks with vectors.
        
        Args:
            chunks: List of chunk metadata dicts
            vectors: List of embedding vectors
            
        Returns:
            Number of points upserted
        """
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append(
                PointStruct(
                    id=chunk.get("id", str(i)),
                    vector=vector,
                    payload={
                        "text": chunk.get("text", ""),
                        "document_id": chunk.get("document_id", ""),
                        "document_title": chunk.get("document_title", ""),
                        "chunk_index": chunk.get("chunk_index", 0),
                        "language": chunk.get("language", "zh-CN"),
                        "source_type": chunk.get("source_type", "document"),
                        "source_ref": chunk.get("source_ref"),
                        "entity_type": chunk.get("entity_type"),
                        "entity_id": chunk.get("entity_id"),
                        "entity_name": chunk.get("entity_name"),
                    },
                )
            )
        
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points,
        )
        return len(points)
    
    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        language: str | None = None,
        source_type: str | None = None,
    ) -> list[KnowledgeChunk]:
        """Search similar chunks by vector.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            language: Filter by language
            source_type: Filter by source type
            
        Returns:
            List of KnowledgeChunk objects
        """
        query_filter = None
        conditions = []
        
        if language:
            conditions.append(
                FieldCondition(
                    key="language",
                    match=MatchValue(value=language),
                )
            )
        
        if source_type:
            conditions.append(
                FieldCondition(
                    key="source_type",
                    match=MatchValue(value=source_type),
                )
            )
        
        if conditions:
            query_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
        )
        
        chunks = []
        for result in results:
            payload = result.payload or {}
            chunks.append(
                KnowledgeChunk(
                    id=str(result.id),
                    text=payload.get("text", ""),
                    score=result.score,
                    document_id=payload.get("document_id", ""),
                    document_title=payload.get("document_title", ""),
                    chunk_index=payload.get("chunk_index", 0),
                    language=payload.get("language", "zh-CN"),
                    source_type=payload.get("source_type", "document"),
                    source_ref=payload.get("source_ref"),
                    entity_type=payload.get("entity_type"),
                    entity_id=payload.get("entity_id"),
                    entity_name=payload.get("entity_name"),
                )
            )
        
        return chunks
    
    def delete_collection(self) -> None:
        """Delete the collection."""
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
    
    def count_points(self) -> int:
        """Count total points in collection."""
        result = self.client.count(self.COLLECTION_NAME)
        return result.count
