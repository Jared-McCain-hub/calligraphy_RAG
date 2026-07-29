"""Complete RAG service combining Qdrant retrieval and Qwen generation."""

from __future__ import annotations

from dataclasses import dataclass

from app.repositories.qdrant_repository import KnowledgeChunk
from app.services.qdrant_retriever_service import QdrantRetrieverService
from app.services.qwen_service import QwenService, QwenGeneration
from app.core.config import settings


@dataclass
class Citation:
    """Citation for a generated answer."""
    
    title: str
    source_type: str
    source_ref: str | None
    score: float


@dataclass
class RAGResponse:
    """Complete RAG response with answer and citations."""
    
    answer: str
    citations: list[Citation]
    used_qwen: bool
    error: str | None = None


class QdrantRAGService:
    """Full RAG pipeline: retrieve -> generate."""
    
    SYSTEM_PROMPT = """你是一个专业的中国书法知识助手。你的任务是基于提供的知识片段回答用户问题。

要求：
1. 只使用提供的知识片段中的信息回答
2. 如果知识片段中没有相关信息，如实告知用户
3. 回答要简洁准确，避免冗余
4. 保持客观中立的语气"""

    USER_PROMPT_TEMPLATE = """请基于以下知识片段回答问题：

{context}

问题：{question}

请给出简洁准确的回答，如果知识片段中没有相关信息，请明确说明。"""

    def __init__(
        self,
        retriever: QdrantRetrieverService | None = None,
        qwen: QwenService | None = None,
    ) -> None:
        """Initialize RAG service.
        
        Args:
            retriever: QdrantRetrieverService instance
            qwen: QwenService instance
        """
        self.retriever = retriever or QdrantRetrieverService(use_memory=True)
        self.qwen = qwen or QwenService(settings)
    
    def chat(
        self,
        question: str,
        top_k: int = 3,
    ) -> RAGResponse:
        """Process a chat query through full RAG pipeline.
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            
        Returns:
            RAGResponse with answer and citations
        """
        # 1. Retrieve context
        context, chunks = self.retriever.retrieve_with_context(
            query=question,
            limit=top_k,
        )
        
        if not chunks:
            return RAGResponse(
                answer="抱歉，我在知识库中没有找到相关信息。",
                citations=[],
                used_qwen=False,
                error="No relevant chunks found",
            )
        
        # 2. Generate answer with Qwen
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )
        
        generation: QwenGeneration = self.qwen.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        
        # 3. Build citations
        citations = []
        seen_titles = set()
        for chunk in chunks:
            if chunk.document_title not in seen_titles:
                citations.append(
                    Citation(
                        title=chunk.document_title,
                        source_type=chunk.source_type,
                        source_ref=chunk.source_ref,
                        score=chunk.score,
                    )
                )
                seen_titles.add(chunk.document_title)
        
        # 4. Build response
        answer = generation.content or "抱歉，生成回答时出现问题。"
        
        return RAGResponse(
            answer=answer,
            citations=citations,
            used_qwen=generation.used_network,
            error=generation.error_message,
        )
