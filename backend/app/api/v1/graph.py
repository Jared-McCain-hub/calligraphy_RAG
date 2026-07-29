from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_graph_service
from app.schemas.graph import GraphQueryRequest, GraphResponse
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/subgraph", response_model=GraphResponse, summary="查询知识图谱子图")
def get_subgraph(
    keyword: str | None = None,
    entity_id: str | None = None,
    entity_type: str | None = None,
    depth: int = 1,
    limit: int = 20,
    graph_service: GraphService = Depends(get_graph_service),
) -> GraphResponse:
    return graph_service.get_subgraph(
        GraphQueryRequest(
            keyword=keyword,
            entity_id=entity_id,
            entity_type=entity_type,
            depth=depth,
            limit=limit,
        )
    )
