"""init mysql schema

Revision ID: 20260402_0001
Revises:
Create Date: 2026-04-02 22:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_0001"
down_revision = None
branch_labels = None
depends_on = None


language_code_enum = sa.Enum(
    "zh-CN",
    "en-US",
    "bilingual",
    name="languagecode",
    native_enum=False,
    validate_strings=True,
)
source_type_enum = sa.Enum(
    "document",
    "web",
    "manual",
    "image",
    "table",
    name="sourcetype",
    native_enum=False,
    validate_strings=True,
)
message_role_enum = sa.Enum(
    "system",
    "user",
    "assistant",
    name="messagerole",
    native_enum=False,
    validate_strings=True,
)
ingest_status_enum = sa.Enum(
    "pending",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    name="ingeststatus",
    native_enum=False,
    validate_strings=True,
)
entity_type_enum = sa.Enum(
    "calligrapher",
    "work",
    "term",
    "era",
    "style",
    "knowledge_chunk",
    name="entitytype",
    native_enum=False,
    validate_strings=True,
)
chunk_link_type_enum = sa.Enum(
    "primary_subject",
    "mentions",
    "describes",
    "references",
    name="chunklinktype",
    native_enum=False,
    validate_strings=True,
)
work_authenticity_enum = sa.Enum(
    "unknown",
    "authentic",
    "attributed",
    "disputed",
    name="workauthenticity",
    native_enum=False,
    validate_strings=True,
)


def upgrade() -> None:
    op.create_table(
        "eras",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name_cn", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=True),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_cn"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "styles",
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name_cn", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_cn"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("language", language_code_enum, nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("source_ref", sa.String(length=500), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_documents_checksum", "knowledge_documents", ["checksum"], unique=False)

    op.create_table(
        "chat_sessions",
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("external_user_id", sa.String(length=120), nullable=True),
        sa.Column("preferred_language", language_code_enum, nullable=False),
        sa.Column("context_summary", sa.Text(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_lookup", "chat_sessions", ["external_user_id", "last_message_at"], unique=False)

    op.create_table(
        "calligraphers",
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name_cn", sa.String(length=120), nullable=False),
        sa.Column("name_en", sa.String(length=120), nullable=True),
        sa.Column("courtesy_name", sa.String(length=120), nullable=True),
        sa.Column("art_name", sa.String(length=120), nullable=True),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
        sa.Column("era_id", sa.String(length=36), nullable=True),
        sa.Column("primary_style_id", sa.String(length=36), nullable=True),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("death_year", sa.Integer(), nullable=True),
        sa.Column("hometown", sa.String(length=255), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("achievements", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["era_id"], ["eras.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["primary_style_id"], ["styles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_cn", "era_id", name="uq_calligraphers_name_cn_era_id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_calligraphers_search", "calligraphers", ["name_cn", "name_en", "slug"], unique=False)

    op.create_table(
        "terms",
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("name_cn", sa.String(length=140), nullable=False),
        sa.Column("name_en", sa.String(length=140), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("aliases_json", sa.JSON(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("usage_notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name_cn", "name_en", name="uq_terms_name_cn_name_en"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_terms_search", "terms", ["name_cn", "name_en", "slug"], unique=False)

    op.create_table(
        "works",
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("title_cn", sa.String(length=200), nullable=False),
        sa.Column("title_en", sa.String(length=200), nullable=True),
        sa.Column("calligrapher_id", sa.String(length=36), nullable=True),
        sa.Column("era_id", sa.String(length=36), nullable=True),
        sa.Column("style_id", sa.String(length=36), nullable=True),
        sa.Column("authenticity", work_authenticity_enum, nullable=False),
        sa.Column("creation_period", sa.String(length=120), nullable=True),
        sa.Column("material", sa.String(length=120), nullable=True),
        sa.Column("dimensions", sa.String(length=120), nullable=True),
        sa.Column("current_collection", sa.String(length=255), nullable=True),
        sa.Column("excerpt_text", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["calligrapher_id"], ["calligraphers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["era_id"], ["eras.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["style_id"], ["styles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_works_search", "works", ["title_cn", "title_en", "slug"], unique=False)

    op.create_table(
        "work_term_links",
        sa.Column("work_id", sa.String(length=36), nullable=False),
        sa.Column("term_id", sa.String(length=36), nullable=False),
        sa.Column("relation_note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["term_id"], ["terms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["work_id"], ["works.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("work_id", "term_id"),
        sa.UniqueConstraint("work_id", "term_id", name="uq_work_term_links_work_id_term_id"),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("language", language_code_enum, nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("source_ref", sa.String(length=500), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
        sa.Column("embedding_provider", sa.String(length=120), nullable=True),
        sa.Column("embedding_id", sa.String(length=120), nullable=True),
        sa.Column("citation_label", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunks_document_id_chunk_index"),
        sa.UniqueConstraint("embedding_id"),
    )
    op.create_index(
        "ix_knowledge_chunks_lookup",
        "knowledge_chunks",
        ["document_id", "language", "source_type"],
        unique=False,
    )

    op.create_table(
        "knowledge_chunk_entity_links",
        sa.Column("chunk_id", sa.String(length=36), nullable=False),
        sa.Column("entity_type", entity_type_enum, nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("link_type", chunk_link_type_enum, nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["knowledge_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "chunk_id",
            "entity_type",
            "entity_id",
            "link_type",
            name="uq_chunk_entity_links_dedup",
        ),
    )
    op.create_index(
        "ix_chunk_entity_lookup",
        "knowledge_chunk_entity_links",
        ["entity_type", "entity_id"],
        unique=False,
    )

    op.create_table(
        "chat_messages",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role", message_role_enum, nullable=False),
        sa.Column("language", language_code_enum, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("rewritten_query", sa.Text(), nullable=True),
        sa.Column("citations_json", sa.JSON(), nullable=False),
        sa.Column("recommendations_json", sa.JSON(), nullable=False),
        sa.Column("trace_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_messages_session_role", "chat_messages", ["session_id", "role"], unique=False)

    op.create_table(
        "ingest_jobs",
        sa.Column("status", ingest_status_enum, nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=True),
        sa.Column("requested_by", sa.String(length=120), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_chunks", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingest_jobs_status", "ingest_jobs", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ingest_jobs_status", table_name="ingest_jobs")
    op.drop_table("ingest_jobs")

    op.drop_index("ix_chat_messages_session_role", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chunk_entity_lookup", table_name="knowledge_chunk_entity_links")
    op.drop_table("knowledge_chunk_entity_links")

    op.drop_index("ix_knowledge_chunks_lookup", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_table("work_term_links")

    op.drop_index("ix_works_search", table_name="works")
    op.drop_table("works")

    op.drop_index("ix_terms_search", table_name="terms")
    op.drop_table("terms")

    op.drop_index("ix_calligraphers_search", table_name="calligraphers")
    op.drop_table("calligraphers")

    op.drop_index("ix_chat_sessions_lookup", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index("ix_knowledge_documents_checksum", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")

    op.drop_table("styles")
    op.drop_table("eras")
