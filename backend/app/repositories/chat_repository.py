from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ChatMessage, ChatSession, LanguageCode


class ChatRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_session(self, session_id: str) -> ChatSession | None:
        stmt = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return self.session.scalar(stmt)

    def get_or_create_session(
        self,
        *,
        session_id: str,
        preferred_language: str,
        external_user_id: str | None,
        title: str,
    ) -> ChatSession:
        session = self.get_session(session_id)
        if session is not None:
            return session
        session = ChatSession(
            id=session_id,
            title=title,
            preferred_language=self._language_code(preferred_language),
            external_user_id=external_user_id,
            last_message_at=datetime.now(timezone.utc),
            metadata_json={"seed": False},
        )
        self.session.add(session)
        self.session.flush()
        return session

    def add_message(
        self,
        *,
        session_id: str,
        role: str,
        language: str,
        content: str,
        rewritten_query: str | None = None,
        citations_json: list[dict] | None = None,
        recommendations_json: dict | None = None,
        trace_json: dict | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            language=self._language_code(language),
            content=content,
            rewritten_query=rewritten_query,
            citations_json=citations_json or [],
            recommendations_json=recommendations_json or {},
            trace_json=trace_json or {},
            metadata_json={"seed": False},
        )
        self.session.add(message)
        self.session.flush()
        return message

    def update_session_state(
        self,
        session: ChatSession,
        *,
        preferred_language: str,
        context_summary: str | None,
    ) -> None:
        session.preferred_language = self._language_code(preferred_language)
        session.context_summary = context_summary
        session.last_message_at = datetime.now(timezone.utc)
        self.session.flush()

    def get_recent_messages(self, session_id: str, limit: int = 4) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(limit)
        )
        messages = self.session.scalars(stmt).all()
        return list(reversed(messages))

    def commit(self) -> None:
        self.session.commit()

    @staticmethod
    def _language_code(language: str) -> LanguageCode:
        try:
            return LanguageCode(language)
        except ValueError:
            return LanguageCode.ZH
