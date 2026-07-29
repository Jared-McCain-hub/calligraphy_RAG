"""Embedding service using sentence-transformers."""

from __future__ import annotations

from typing import Literal

import numpy as np

# Lazy import to avoid loading model on startup
_model = None


def _get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model


class EmbeddingService:
    """Service for generating text embeddings."""
    
    # Model dimension (MiniLM-L12-v2)
    DIMENSION = 768
    
    @staticmethod
    def encode(
        texts: str | list[str],
        normalize: bool = True,
    ) -> np.ndarray:
        """Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            normalize: Whether to normalize vectors
            
        Returns:
            Numpy array of embeddings (shape: [n_texts, 768])
        """
        model = _get_model()
        
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = model.encode(
            texts,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        
        return embeddings
    
    @staticmethod
    def encode_to_list(texts: str | list[str]) -> list[list[float]]:
        """Generate embeddings as list of lists (JSON-serializable).
        
        Args:
            texts: Single text or list of texts
            
        Returns:
            List of embedding vectors
        """
        embeddings = EmbeddingService.encode(texts)
        return embeddings.tolist()
    
    @staticmethod
    def similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score [-1, 1]
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
