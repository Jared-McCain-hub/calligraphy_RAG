from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel, EntityReference


class SearchRequest(APIModel):
    query: str = Field(min_length=1, max_length=512)
    entity_types: list[str] = Field(default_factory=list)
    era: str | None = None
    style: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchHit(EntityReference):
    score: float = Field(default=0.0, ge=0.0)
    highlights: list[str] = Field(default_factory=list)


class SearchResponse(APIModel):
    query: str
    normalized_query: str
    total: int
    items: list[SearchHit] = Field(default_factory=list)
