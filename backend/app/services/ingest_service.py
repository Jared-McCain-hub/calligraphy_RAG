from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import settings
from app.models import IngestStatus
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.term_repository import TermRepository
from app.schemas.ingest import IngestRequest, IngestResponse, ReindexRequest, ReindexResponse
from app.services.rag_runtime import RAGRuntime


class IngestService:
    """Runs a synchronous ingest pipeline and persists chunks to MySQL."""

    def __init__(
        self,
        runtime: RAGRuntime,
        knowledge_repository: KnowledgeRepository | None = None,
        term_repository: TermRepository | None = None,
    ) -> None:
        self.runtime = runtime
        self.knowledge_repository = knowledge_repository
        self.term_repository = term_repository

    def create_job(self, payload: IngestRequest) -> IngestResponse:
        raw_text = payload.raw_text or self._build_stub_text(payload)
        if self.knowledge_repository is None:
            result = self.runtime.ingest_document(
                title=payload.title,
                raw_text=raw_text,
                language=payload.language,
                source_type=payload.source_type,
                source_ref=payload.source_ref,
            )
            term_labels = [f"{term.name_cn}/{term.name_en}" for term in result.matched_terms[:3]]
            term_message = f" 识别术语：{', '.join(term_labels)}。" if term_labels else ""
            return IngestResponse(
                job_id=result.job_id,
                status="succeeded",
                message=(
                    "导入流程已完成：原始文本已标准化、切片、向量化并写入内存检索索引。"
                    f" 共生成 {result.chunk_count} 个 chunk。{term_message}"
                ),
                updated_at=result.updated_at,
                document_id=result.document_id,
                processed_chunks=result.chunk_count,
                embedding_provider=settings.embedding_provider,
                embedding_model=settings.embedding_model,
                indexed_targets=["knowledge_documents", "knowledge_chunks", "retrieval_runtime"],
            )

        job = self.knowledge_repository.create_ingest_job(
            source_type=payload.source_type,
            requested_by=payload.requested_by,
        )
        self.knowledge_repository.update_ingest_job(job, status=IngestStatus.RUNNING)
        self.knowledge_repository.commit()
        try:
            normalized_text = self.runtime._normalize_text(raw_text)
            summary = self.runtime._summarize_text(normalized_text)
            checksum = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
            document = self.knowledge_repository.upsert_document(
                title=payload.title,
                language=payload.language,
                source_type=payload.source_type,
                source_ref=payload.source_ref,
                summary=summary,
                parsed_text=normalized_text,
                checksum=checksum,
                metadata_json={"seed": False},
            )
            self.knowledge_repository.replace_document_chunks(document)

            chunk_texts = self.runtime._chunk_text(normalized_text)
            matched_terms = self._collect_terms(payload.title, normalized_text)
            matched_term_by_id = {term.id: term for term in matched_terms}

            for chunk_index, chunk_text in enumerate(chunk_texts):
                chunk_terms = self._collect_terms(chunk_text)
                for term in chunk_terms:
                    matched_term_by_id[term.id] = term
                chunk = self.knowledge_repository.create_chunk(
                    document=document,
                    chunk_index=chunk_index,
                    language=payload.language,
                    source_type=payload.source_type,
                    source_ref=payload.source_ref,
                    text=chunk_text,
                    normalized_text=chunk_text.lower(),
                    token_count=len(self.runtime._tokenize(chunk_text)),
                    embedding_model=settings.embedding_model,
                    embedding_provider=settings.embedding_provider,
                    embedding_id=f"emb-{uuid4()}",
                    citation_label=f"{payload.title} 第 {chunk_index + 1} 段",
                )
                for term in chunk_terms:
                    self.knowledge_repository.link_chunk_term(chunk_id=chunk.id, term_id=term.id)

            self.knowledge_repository.update_ingest_job(
                job,
                status=IngestStatus.SUCCEEDED,
                document_id=document.id,
                processed_chunks=len(chunk_texts),
            )
            self.knowledge_repository.commit()
        except Exception as exc:
            self.knowledge_repository.rollback()
            job = self.knowledge_repository.session.get(type(job), job.id) or job
            self.knowledge_repository.update_ingest_job(
                job,
                status=IngestStatus.FAILED,
                error_message=str(exc),
            )
            self.knowledge_repository.commit()
            raise

        term_labels = [f"{term.name_cn}/{term.name_en}" for term in list(matched_term_by_id.values())[:3]]
        term_message = f" 识别术语：{', '.join(term_labels)}。" if term_labels else ""
        return IngestResponse(
            job_id=job.id,
            status="succeeded",
            message=(
                "导入流程已完成：原始文本已标准化、切片，并持久化到 MySQL 的文档与 chunk 表。"
                f" 共生成 {len(chunk_texts)} 个 chunk。{term_message}"
            ),
            updated_at=job.finished_at or datetime.now(timezone.utc),
            document_id=document.id,
            processed_chunks=len(chunk_texts),
            embedding_provider=settings.embedding_provider,
            embedding_model=settings.embedding_model,
            indexed_targets=["knowledge_documents", "knowledge_chunks", "knowledge_chunk_entity_links"],
        )

    def reindex(self, payload: ReindexRequest) -> ReindexResponse:
        timestamp = datetime.now(timezone.utc)
        if self.knowledge_repository is None:
            processed_chunks = self.runtime.reindex_chunks()
        else:
            chunks = self.knowledge_repository.list_chunks()
            processed_chunks = 0
            for chunk in chunks:
                self.knowledge_repository.update_chunk_index_state(
                    chunk,
                    normalized_text=(chunk.text or "").lower(),
                    token_count=len(self.runtime._tokenize(chunk.text or "")),
                    embedding_provider=settings.embedding_provider,
                    embedding_model=settings.embedding_model,
                    embedding_id=chunk.embedding_id or f"emb-{uuid4()}",
                )
                processed_chunks += 1
            self.knowledge_repository.commit()
        return ReindexResponse(
            job_id=f"reindex-{payload.target}-{int(timestamp.timestamp())}",
            status="succeeded",
            message="已完成 chunk 向量重建，可用于后续替换为 Qdrant/Neo4j 的真实索引流程。",
            updated_at=timestamp,
            target=payload.target,
            processed_chunks=processed_chunks,
        )

    @staticmethod
    def _build_stub_text(payload: IngestRequest) -> str:
        return (
            f"{payload.title} 是一条待扩展语料。"
            " 当前导入接口会先以同步方式完成文本清洗、切片、向量化与术语抽取，"
            " 便于前后端联调检索与问答流程。"
        )

    def _collect_terms(self, *texts: str):
        if self.term_repository is not None:
            return self.term_repository.collect_terms(*texts)
        return self.runtime.build_glossary([text for text in texts if text])
