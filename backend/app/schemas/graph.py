from __future__ import annotations

from pydantic import Field

from app.schemas.common import APIModel


class GraphQueryRequest(APIModel):
    keyword: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    depth: int = Field(default=1, ge=1, le=3)
    limit: int = Field(default=20, ge=1, le=100)


class GraphNode(APIModel):
    id: str
    entity_type: str
    label: str
    properties: dict[str, str] = Field(default_factory=dict)


class GraphEdge(APIModel):
    source: str
    target: str
    relation: str
    properties: dict[str, str] = Field(default_factory=dict)


class GraphResponse(APIModel):
    query: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
