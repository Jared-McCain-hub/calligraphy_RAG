from __future__ import annotations

from app.schemas.graph import GraphEdge, GraphNode, GraphQueryRequest, GraphResponse
from app.services.catalog_service import CALLIGRAPHER_WANG, ERA_JIN, STYLE_RUNNING, WORK_LANTINGJI


class GraphService:
    """MVP knowledge graph subgraph service."""

    def get_subgraph(self, payload: GraphQueryRequest) -> GraphResponse:
        query = payload.keyword or payload.entity_id or "default-subgraph"

        nodes = [
            GraphNode(
                id=CALLIGRAPHER_WANG.id,
                entity_type="calligrapher",
                label=CALLIGRAPHER_WANG.name_cn,
                properties={"name_en": CALLIGRAPHER_WANG.name_en or ""},
            ),
            GraphNode(
                id=WORK_LANTINGJI.id,
                entity_type="work",
                label=WORK_LANTINGJI.title_cn,
                properties={"title_en": WORK_LANTINGJI.title_en or ""},
            ),
            GraphNode(
                id=STYLE_RUNNING.id,
                entity_type="style",
                label=STYLE_RUNNING.name,
            ),
            GraphNode(
                id=ERA_JIN.id,
                entity_type="era",
                label=ERA_JIN.name,
            ),
        ]
        edges = [
            GraphEdge(
                source=CALLIGRAPHER_WANG.id,
                target=WORK_LANTINGJI.id,
                relation="CREATED",
            ),
            GraphEdge(
                source=WORK_LANTINGJI.id,
                target=STYLE_RUNNING.id,
                relation="HAS_STYLE",
            ),
            GraphEdge(
                source=WORK_LANTINGJI.id,
                target=ERA_JIN.id,
                relation="BELONGS_TO_ERA",
            ),
        ]
        return GraphResponse(
            query=query,
            nodes=nodes[: payload.limit],
            edges=edges,
        )
