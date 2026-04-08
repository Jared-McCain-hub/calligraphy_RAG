from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.api.deps import get_ingest_service
from app.schemas.ingest import IngestRequest, IngestResponse, ReindexRequest, ReindexResponse
from app.services.ingest_service import IngestService

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("app.audit")


@router.post("/ingest", response_model=IngestResponse, summary="创建语料导入任务")
def create_ingest_job(
    request: Request,
    payload: IngestRequest,
    ingest_service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        "Ingest requested. ip=%s source_type=%s title=%s requested_by=%s",
        client_ip,
        payload.source_type,
        payload.title,
        payload.requested_by or "unknown",
    )
    return ingest_service.create_job(payload)


@router.post("/reindex", response_model=ReindexResponse, summary="创建索引重建任务")
def create_reindex_job(
    request: Request,
    payload: ReindexRequest,
    ingest_service: IngestService = Depends(get_ingest_service),
) -> ReindexResponse:
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        "Reindex requested. ip=%s target=%s force=%s",
        client_ip,
        payload.target,
        payload.force,
    )
    return ingest_service.reindex(payload)
