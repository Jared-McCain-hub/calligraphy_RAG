from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SqlEnum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, MetadataMixin, TimestampMixin, UUIDPrimaryKeyMixin


class LanguageCode(str, Enum):
    ZH = "zh-CN"
    EN = "en-US"
    BILINGUAL = "bilingual"


class SourceType(str, Enum):
    DOCUMENT = "document"
    WEB = "web"
    MANUAL = "manual"
    IMAGE = "image"
    TABLE = "table"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class IngestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EntityType(str, Enum):
    CALLIGRAPHER = "calligrapher"
    WORK = "work"
    TERM = "term"
    ERA = "era"
    STYLE = "style"
    KNOWLEDGE_CHUNK = "knowledge_chunk"


class ChunkLinkType(str, Enum):
    PRIMARY_SUBJECT = "primary_subject"
    MENTIONS = "mentions"
    DESCRIBES = "describes"
    REFERENCES = "references"


class WorkAuthenticity(str, Enum):
    UNKNOWN = "unknown"
    AUTHENTIC = "authentic"
    ATTRIBUTED = "attributed"
    DISPUTED = "disputed"


ENUM_KWARGS = {"native_enum": False, "validate_strings": True}


class Era(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "eras"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_cn: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    summary: Mapped[str | None] = mapped_column(Text)
    aliases_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    calligraphers: Mapped[list["Calligrapher"]] = relationship(back_populates="era")
    works: Mapped[list["Work"]] = relationship(back_populates="era")


class Style(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "styles"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_cn: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    aliases_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    calligraphers: Mapped[list["Calligrapher"]] = relationship(back_populates="primary_style")
    works: Mapped[list["Work"]] = relationship(back_populates="style")


class Calligrapher(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "calligraphers"
    __table_args__ = (
        UniqueConstraint("name_cn", "era_id", name="uq_calligraphers_name_cn_era_id"),
        Index("ix_calligraphers_search", "name_cn", "name_en", "slug"),
    )

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name_cn: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(120))
    courtesy_name: Mapped[str | None] = mapped_column(String(120))
    art_name: Mapped[str | None] = mapped_column(String(120))
    aliases_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    era_id: Mapped[str | None] = mapped_column(ForeignKey("eras.id", ondelete="SET NULL"))
    primary_style_id: Mapped[str | None] = mapped_column(ForeignKey("styles.id", ondelete="SET NULL"))
    birth_year: Mapped[int | None] = mapped_column(Integer)
    death_year: Mapped[int | None] = mapped_column(Integer)
    hometown: Mapped[str | None] = mapped_column(String(255))
    biography: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))

    era: Mapped[Era | None] = relationship(back_populates="calligraphers")
    primary_style: Mapped[Style | None] = relationship(back_populates="calligraphers")
    works: Mapped[list["Work"]] = relationship(back_populates="calligrapher")


class Work(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "works"
    __table_args__ = (
        Index("ix_works_search", "title_cn", "title_en", "slug"),
    )

    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    title_cn: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(200))
    calligrapher_id: Mapped[str | None] = mapped_column(
        ForeignKey("calligraphers.id", ondelete="SET NULL")
    )
    era_id: Mapped[str | None] = mapped_column(ForeignKey("eras.id", ondelete="SET NULL"))
    style_id: Mapped[str | None] = mapped_column(ForeignKey("styles.id", ondelete="SET NULL"))
    authenticity: Mapped[WorkAuthenticity] = mapped_column(
        SqlEnum(WorkAuthenticity, **ENUM_KWARGS),
        default=WorkAuthenticity.UNKNOWN,
        nullable=False,
    )
    creation_period: Mapped[str | None] = mapped_column(String(120))
    material: Mapped[str | None] = mapped_column(String(120))
    dimensions: Mapped[str | None] = mapped_column(String(120))
    current_collection: Mapped[str | None] = mapped_column(String(255))
    excerpt_text: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(255))

    calligrapher: Mapped[Calligrapher | None] = relationship(back_populates="works")
    era: Mapped[Era | None] = relationship(back_populates="works")
    style: Mapped[Style | None] = relationship(back_populates="works")
    terms: Mapped[list["Term"]] = relationship(
        secondary="work_term_links",
        back_populates="works",
    )


class Term(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "terms"
    __table_args__ = (
        UniqueConstraint("name_cn", "name_en", name="uq_terms_name_cn_name_en"),
        Index("ix_terms_search", "name_cn", "name_en", "slug"),
    )

    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    name_cn: Mapped[str] = mapped_column(String(140), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(140))
    category: Mapped[str | None] = mapped_column(String(80))
    aliases_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    definition: Mapped[str | None] = mapped_column(Text)
    usage_notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))

    works: Mapped[list[Work]] = relationship(
        secondary="work_term_links",
        back_populates="terms",
    )


class WorkTermLink(TimestampMixin, Base):
    __tablename__ = "work_term_links"
    __table_args__ = (
        UniqueConstraint("work_id", "term_id", name="uq_work_term_links_work_id_term_id"),
    )

    work_id: Mapped[str] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"),
        primary_key=True,
    )
    term_id: Mapped[str] = mapped_column(
        ForeignKey("terms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relation_note: Mapped[str | None] = mapped_column(String(255))


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("ix_knowledge_documents_checksum", "checksum"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[LanguageCode] = mapped_column(SqlEnum(LanguageCode, **ENUM_KWARGS), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SqlEnum(SourceType, **ENUM_KWARGS), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    storage_path: Mapped[str | None] = mapped_column(String(500))
    checksum: Mapped[str | None] = mapped_column(String(128))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text)
    parsed_text: Mapped[str | None] = mapped_column(Text)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunks_document_id_chunk_index"),
        Index("ix_knowledge_chunks_lookup", "document_id", "language", "source_type"),
    )

    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[LanguageCode] = mapped_column(SqlEnum(LanguageCode, **ENUM_KWARGS), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SqlEnum(SourceType, **ENUM_KWARGS), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(500))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    embedding_model: Mapped[str | None] = mapped_column(String(120))
    embedding_provider: Mapped[str | None] = mapped_column(String(120))
    embedding_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    citation_label: Mapped[str | None] = mapped_column(String(255))

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")
    entity_links: Mapped[list["KnowledgeChunkEntityLink"]] = relationship(
        back_populates="chunk",
        cascade="all, delete-orphan",
    )


class KnowledgeChunkEntityLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_chunk_entity_links"
    __table_args__ = (
        Index("ix_chunk_entity_lookup", "entity_type", "entity_id"),
        UniqueConstraint(
            "chunk_id",
            "entity_type",
            "entity_id",
            "link_type",
            name="uq_chunk_entity_links_dedup",
        ),
    )

    chunk_id: Mapped[str] = mapped_column(ForeignKey("knowledge_chunks.id", ondelete="CASCADE"))
    entity_type: Mapped[EntityType] = mapped_column(SqlEnum(EntityType, **ENUM_KWARGS), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    link_type: Mapped[ChunkLinkType] = mapped_column(SqlEnum(ChunkLinkType, **ENUM_KWARGS), nullable=False)
    confidence: Mapped[int | None] = mapped_column(Integer)

    chunk: Mapped[KnowledgeChunk] = relationship(back_populates="entity_links")


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("ix_chat_sessions_lookup", "external_user_id", "last_message_at"),
    )

    title: Mapped[str | None] = mapped_column(String(255))
    external_user_id: Mapped[str | None] = mapped_column(String(120))
    preferred_language: Mapped[LanguageCode] = mapped_column(
        SqlEnum(LanguageCode, **ENUM_KWARGS),
        default=LanguageCode.ZH,
        nullable=False,
    )
    context_summary: Mapped[str | None] = mapped_column(Text)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by=lambda: (ChatMessage.created_at.asc(), ChatMessage.id.asc()),
    )


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_session_role", "session_id", "role"),
    )

    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(SqlEnum(MessageRole, **ENUM_KWARGS), nullable=False)
    language: Mapped[LanguageCode] = mapped_column(
        SqlEnum(LanguageCode, **ENUM_KWARGS),
        default=LanguageCode.ZH,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[str | None] = mapped_column(Text)
    citations_json: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommendations_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    trace_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class IngestJob(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "ingest_jobs"
    __table_args__ = (
        Index("ix_ingest_jobs_status", "status", "created_at"),
    )

    status: Mapped[IngestStatus] = mapped_column(
        SqlEnum(IngestStatus, **ENUM_KWARGS),
        default=IngestStatus.PENDING,
        nullable=False,
    )
    source_type: Mapped[SourceType] = mapped_column(SqlEnum(SourceType, **ENUM_KWARGS), nullable=False)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="SET NULL"))
    requested_by: Mapped[str | None] = mapped_column(String(120))
    filename: Mapped[str | None] = mapped_column(String(255))
    checksum: Mapped[str | None] = mapped_column(String(128))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    processed_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

