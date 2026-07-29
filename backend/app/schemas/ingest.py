from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel, TaskStatus


class IngestRequest(APIModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: str = Field(default="document")
    source_ref: str | None = None
    requested_by: str | None = None
    language: str = Field(default="zh-CN")
    raw_text: str | None = None


class IngestResponse(TaskStatus):
    document_id: str | None = None
    processed_chunks: int = 0
    embedding_provider: str | None = None
    embedding_model: str | None = None
    indexed_targets: list[str] = Field(default_factory=list)


class ReindexRequest(APIModel):
    target: str = Field(default="knowledge_chunks")
    force: bool = False


class ReindexResponse(TaskStatus):
    target: str
    processed_chunks: int = 0
