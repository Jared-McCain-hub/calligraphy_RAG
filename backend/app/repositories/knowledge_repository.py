from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, case, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ChunkLinkType,
    EntityType,
    IngestJob,
    IngestStatus,
    KnowledgeChunk,
    KnowledgeChunkEntityLink,
    KnowledgeDocument,
    LanguageCode,
    SourceType,
)


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_document_by_source_ref(self, source_ref: str) -> KnowledgeDocument | None:
        stmt = (
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.source_ref == source_ref)
        )
        return self.session.scalar(stmt)

    def get_document_with_chunks(self, document_id: str) -> KnowledgeDocument | None:
        stmt = (
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.id == document_id)
        )
        return self.session.scalar(stmt)

    def create_ingest_job(
        self,
        *,
        source_type: str,
        requested_by: str | None,
    ) -> IngestJob:
        job = IngestJob(
            source_type=self._source_type(source_type),
            requested_by=requested_by,
            status=IngestStatus.PENDING,
            started_at=datetime.now(timezone.utc),
            metadata_json={"seed": False},
        )
        self.session.add(job)
        self.session.flush()
        return job

    def update_ingest_job(
        self,
        job: IngestJob,
        *,
        status: IngestStatus,
        document_id: str | None = None,
        processed_chunks: int | None = None,
        error_message: str | None = None,
    ) -> IngestJob:
        job.status = status
        job.document_id = document_id
        if processed_chunks is not None:
            job.processed_chunks = processed_chunks
        job.error_message = error_message
        if status in {IngestStatus.SUCCEEDED, IngestStatus.FAILED, IngestStatus.CANCELLED}:
            job.finished_at = datetime.now(timezone.utc)
        self.session.flush()
        return job

    def upsert_document(
        self,
        *,
        title: str,
        language: str,
        source_type: str,
        source_ref: str | None,
        summary: str,
        parsed_text: str,
        checksum: str | None,
        metadata_json: dict | None = None,
    ) -> KnowledgeDocument:
        document = self.get_document_by_source_ref(source_ref) if source_ref else None
        if document is None:
            document = KnowledgeDocument(
                title=title,
                language=self._language_code(language),
                source_type=self._source_type(source_type),
                source_ref=source_ref,
                summary=summary,
                parsed_text=parsed_text,
                checksum=checksum,
                metadata_json=metadata_json or {"seed": False},
            )
            self.session.add(document)
        else:
            document.title = title
            document.language = self._language_code(language)
            document.source_type = self._source_type(source_type)
            document.summary = summary
            document.parsed_text = parsed_text
            document.checksum = checksum
            document.metadata_json = metadata_json or document.metadata_json
        self.session.flush()
        return document

    def replace_document_chunks(self, document: KnowledgeDocument) -> None:
        for chunk in list(document.chunks):
            self.session.delete(chunk)
        self.session.flush()

    def create_chunk(
        self,
        *,
        document: KnowledgeDocument,
        chunk_index: int,
        language: str,
        source_type: str,
        source_ref: str | None,
        text: str,
        normalized_text: str,
        token_count: int,
        embedding_model: str | None,
        embedding_provider: str | None,
        embedding_id: str | None,
        citation_label: str,
    ) -> KnowledgeChunk:
        chunk = KnowledgeChunk(
            document_id=document.id,
            chunk_index=chunk_index,
            language=self._language_code(language),
            source_type=self._source_type(source_type),
            source_ref=source_ref,
            text=text,
            normalized_text=normalized_text,
            token_count=token_count,
            embedding_model=embedding_model,
            embedding_provider=embedding_provider,
            embedding_id=embedding_id,
            citation_label=citation_label,
            metadata_json={"seed": False},
        )
        self.session.add(chunk)
        self.session.flush()
        return chunk

    def link_chunk_entity(
        self,
        *,
        chunk_id: str,
        entity_type: EntityType,
        entity_id: str,
        link_type: ChunkLinkType,
        confidence: int | None = 100,
    ) -> bool:
        existing = self.session.scalar(
            select(KnowledgeChunkEntityLink).where(
                and_(
                    KnowledgeChunkEntityLink.chunk_id == chunk_id,
                    KnowledgeChunkEntityLink.entity_type == entity_type,
                    KnowledgeChunkEntityLink.entity_id == entity_id,
                    KnowledgeChunkEntityLink.link_type == link_type,
                )
            )
        )
        if existing is not None:
            return False
        self.session.add(
            KnowledgeChunkEntityLink(
                chunk_id=chunk_id,
                entity_type=entity_type,
                entity_id=entity_id,
                link_type=link_type,
                confidence=confidence,
            )
        )
        self.session.flush()
        return True

    def link_chunk_term(self, *, chunk_id: str, term_id: str) -> bool:
        return self.link_chunk_entity(
            chunk_id=chunk_id,
            entity_type=EntityType.TERM,
            entity_id=term_id,
            link_type=ChunkLinkType.MENTIONS,
            confidence=100,
        )

    def search_candidate_chunks(
        self,
        *,
        query_tokens: list[str],
        language: str,
        limit: int,
    ) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).options(
            selectinload(KnowledgeChunk.document),
            selectinload(KnowledgeChunk.entity_links),
        )

        language_code = self._language_code(language)
        if language_code != LanguageCode.BILINGUAL:
            stmt = stmt.where(
                KnowledgeChunk.language.in_([language_code, LanguageCode.BILINGUAL])
            )

        filtered_tokens = [token for token in query_tokens if token]
        match_score = None
        if filtered_tokens:
            match_score = sum(
                case(
                    (
                        KnowledgeChunk.citation_label.ilike(f"%{token}%"),
                        4,
                    ),
                    (
                        KnowledgeChunk.normalized_text.ilike(f"%{token.lower()}%"),
                        2,
                    ),
                    (
                        KnowledgeChunk.text.ilike(f"%{token}%"),
                        1,
                    ),
                    else_=0,
                )
                for token in filtered_tokens[:8]
            )
            stmt = stmt.where(
                or_(
                    *[
                        or_(
                            KnowledgeChunk.text.ilike(f"%{token}%"),
                            KnowledgeChunk.normalized_text.ilike(f"%{token.lower()}%"),
                            KnowledgeChunk.citation_label.ilike(f"%{token}%"),
                        )
                        for token in filtered_tokens[:8]
                    ]
                )
            )

        if match_score is not None:
            stmt = stmt.order_by(match_score.desc(), KnowledgeChunk.chunk_index.asc(), KnowledgeChunk.id.asc())
        else:
            stmt = stmt.order_by(KnowledgeChunk.chunk_index.asc(), KnowledgeChunk.id.asc())

        return self.session.scalars(stmt.limit(max(limit * 5, 20))).all()

    def list_chunks(self) -> list[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).options(selectinload(KnowledgeChunk.document))
        return self.session.scalars(stmt).all()

    def update_chunk_index_state(
        self,
        chunk: KnowledgeChunk,
        *,
        normalized_text: str,
        token_count: int,
        embedding_provider: str | None,
        embedding_model: str | None,
        embedding_id: str | None,
    ) -> None:
        chunk.normalized_text = normalized_text
        chunk.token_count = token_count
        chunk.embedding_provider = embedding_provider
        chunk.embedding_model = embedding_model
        chunk.embedding_id = embedding_id
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    @staticmethod
    def _language_code(language: str) -> LanguageCode:
        try:
            return LanguageCode(language)
        except ValueError:
            return LanguageCode.ZH

    @staticmethod
    def _source_type(source_type: str) -> SourceType:
        try:
            return SourceType(source_type)
        except ValueError:
            return SourceType.DOCUMENT
