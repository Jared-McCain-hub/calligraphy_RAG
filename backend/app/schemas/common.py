from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class APIModel(BaseModel):
    """Shared base model for HTTP request/response schemas."""


class EntityReference(APIModel):
    id: str
    entity_type: str
    name: str
    summary: str | None = None


class Citation(APIModel):
    chunk_id: str
    quote: str
    source_label: str
    document_title: str | None = None
    source_ref: str | None = None


class RecommendationBlock(APIModel):
    works: list[EntityReference] = Field(default_factory=list)
    calligraphers: list[EntityReference] = Field(default_factory=list)
    terms: list[EntityReference] = Field(default_factory=list)


class TaskStatus(APIModel):
    job_id: str
    status: str
    message: str
    updated_at: datetime
