from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_search_service
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse, summary="综合搜索术语、人物与作品")
def search(
    payload: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return search_service.search(payload)
