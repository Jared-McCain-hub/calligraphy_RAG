from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel, Citation, RecommendationBlock


class ChatQueryRequest(APIModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    language: str = Field(default="zh-CN")
    external_user_id: str | None = None


class ChatMessageView(APIModel):
    id: str
    role: str
    language: str
    content: str
    created_at: datetime
    citations: list[Citation] = Field(default_factory=list)


class ChatQueryResponse(APIModel):
    session_id: str
    answer: str
    answer_language: str
    rewritten_query: str
    citations: list[Citation] = Field(default_factory=list)
    recommendations: RecommendationBlock = Field(default_factory=RecommendationBlock)
    messages: list[ChatMessageView] = Field(default_factory=list)
    trace: dict[str, str] = Field(default_factory=dict)


class ChatSessionDetailResponse(APIModel):
    session_id: str
    title: str
    preferred_language: str
    context_summary: str | None = None
    messages: list[ChatMessageView] = Field(default_factory=list)
