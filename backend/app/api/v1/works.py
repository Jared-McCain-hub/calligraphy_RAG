from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_catalog_service
from app.schemas.catalog import WorkDetailResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/works", tags=["works"])


@router.get("/{work_id}", response_model=WorkDetailResponse, summary="获取作品详情")
def get_work(
    work_id: str,
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> WorkDetailResponse:
    try:
        return catalog_service.get_work(work_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work '{work_id}' not found.",
        ) from exc
