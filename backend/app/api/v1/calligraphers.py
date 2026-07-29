from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_catalog_service
from app.schemas.catalog import CalligrapherDetailResponse
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/calligraphers", tags=["calligraphers"])


@router.get("/{calligrapher_id}", response_model=CalligrapherDetailResponse, summary="获取书法家详情")
def get_calligrapher(
    calligrapher_id: str,
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> CalligrapherDetailResponse:
    try:
        return catalog_service.get_calligrapher(calligrapher_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calligrapher '{calligrapher_id}' not found.",
        ) from exc
