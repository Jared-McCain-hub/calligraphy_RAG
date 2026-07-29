from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from starlette.requests import Request

from app.api.deps import get_chat_service
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse, ChatSessionDetailResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("app.audit")


@router.post("/query", response_model=ChatQueryResponse, summary="发起问答")
def query_chat(
    request: Request,
    payload: ChatQueryRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatQueryResponse:
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "Chat query received. ip=%s session_id=%s language=%s question_len=%s",
        client_ip,
        payload.session_id or "new",
        payload.language,
        len(payload.question),
    )
    response = chat_service.query(payload)
    logger.info(
        "Chat query completed. ip=%s session_id=%s citations=%s",
        client_ip,
        response.session_id,
        len(response.citations),
    )
    return response


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse, summary="获取会话历史")
def get_chat_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatSessionDetailResponse:
    return chat_service.get_session(session_id)
