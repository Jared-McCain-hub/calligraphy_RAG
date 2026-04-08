from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    ChatMessageView,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionDetailResponse,
)
from app.schemas.common import Citation, RecommendationBlock
from app.services.catalog_service import CatalogService, WORK_LANTINGJI
from app.services.qwen_service import QwenService
from app.services.rag_runtime import RAGRuntime, RetrievalHit, StoredMessage, TermEntry
from app.services.retriever_service import RetrieverService
from app.services.term_guard_service import TermGuardService


class ChatService:
    """MVP chat orchestration with retrieval, term guard, and Qwen fallback."""

    def __init__(
        self,
        *,
        runtime: RAGRuntime,
        retriever_service: RetrieverService,
        term_guard_service: TermGuardService,
        qwen_service: QwenService,
        chat_repository: ChatRepository | None = None,
        catalog_service: CatalogService | None = None,
    ) -> None:
        self.runtime = runtime
        self.retriever_service = retriever_service
        self.term_guard_service = term_guard_service
        self.qwen_service = qwen_service
        self.chat_repository = chat_repository
        self.catalog_service = catalog_service

    def query(self, payload: ChatQueryRequest) -> ChatQueryResponse:
        session_id = payload.session_id or str(uuid4())
        rewritten_query = self.retriever_service.rewrite_query(payload.question)
        retrieval_hits = self.retriever_service.retrieve(
            rewritten_query,
            language=payload.language,
            limit=self.runtime.settings.retrieval_top_k,
        )
        citations = self.runtime.build_citations(retrieval_hits)
        glossary_terms = self.term_guard_service.collect_terms(
            payload.question,
            rewritten_query,
            *[hit.chunk.text for hit in retrieval_hits],
        )
        recommendations = self._build_recommendations(payload.question, retrieval_hits, glossary_terms)
        answer, llm_trace = self._generate_answer(
            payload=payload,
            rewritten_query=rewritten_query,
            retrieval_hits=retrieval_hits,
            glossary_terms=glossary_terms,
            session_id=session_id,
        )
        answer = self.term_guard_service.normalize_answer(
            answer,
            language=payload.language,
            terms=glossary_terms,
        )
        trace = {
            "llm_provider": llm_trace["provider"],
            "llm_model": llm_trace["model"],
            "llm_status": llm_trace["status"],
            "retrieval_mode": "mysql_knowledge_chunks",
            "retrieval_hits": str(len(retrieval_hits)),
            "term_guard": "applied" if glossary_terms else "skipped",
        }
        messages = self._persist_turn(
            session_id=session_id,
            payload=payload,
            answer=answer,
            rewritten_query=rewritten_query,
            citations=citations,
            recommendations=recommendations,
            trace=trace,
        )
        return ChatQueryResponse(
            session_id=session_id,
            answer=answer,
            answer_language=payload.language,
            rewritten_query=rewritten_query,
            citations=citations,
            recommendations=recommendations,
            messages=messages,
            trace=trace,
        )

    def get_session(self, session_id: str) -> ChatSessionDetailResponse:
        if self.chat_repository is not None:
            session = self.chat_repository.get_session(session_id)
            if session is not None:
                ordered_messages = sorted(
                    session.messages,
                    key=lambda message: (message.created_at, message.id),
                )
                return ChatSessionDetailResponse(
                    session_id=session.id,
                    title=session.title,
                    preferred_language=session.preferred_language.value,
                    context_summary=session.context_summary,
                    messages=[
                        ChatMessageView(
                            id=message.id,
                            role=message.role.value,
                            language=message.language.value,
                            content=message.content,
                            created_at=message.created_at,
                            citations=[Citation.model_validate(item) for item in message.citations_json or []],
                        )
                        for message in ordered_messages
                    ],
                )

        session = self.runtime.get_session(session_id)
        if session is not None:
            return ChatSessionDetailResponse(
                session_id=session.session_id,
                title=session.title,
                preferred_language=session.preferred_language,
                context_summary=session.context_summary,
                messages=[
                    ChatMessageView(
                        id=message.id,
                        role=message.role,
                        language=message.language,
                        content=message.content,
                        created_at=message.created_at,
                        citations=message.citations,
                    )
                    for message in session.messages
                ],
            )
        return self._build_demo_session(session_id)

    def _generate_answer(
        self,
        *,
        payload: ChatQueryRequest,
        rewritten_query: str,
        retrieval_hits: list[RetrievalHit],
        glossary_terms: list[TermEntry],
        session_id: str,
    ) -> tuple[str, dict[str, str]]:
        history = self._get_recent_history(session_id)
        system_prompt = self._build_system_prompt(payload.language)
        user_prompt = self._build_user_prompt(
            question=payload.question,
            rewritten_query=rewritten_query,
            retrieval_hits=retrieval_hits,
            history=history,
            glossary_terms=glossary_terms,
            language=payload.language,
        )
        generation = self.qwen_service.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        if generation.content:
            return generation.content, {
                "provider": generation.provider,
                "model": generation.model,
                "status": "network" if generation.used_network else "local",
            }

        return self._build_fallback_answer(payload, retrieval_hits, glossary_terms), {
            "provider": generation.provider,
            "model": generation.model,
            "status": generation.error_message or "fallback",
        }

    @staticmethod
    def _build_system_prompt(language: str) -> str:
        base = (
            "你是中国书法知识问答助手。"
            " 回答必须依据提供的检索上下文，不要编造出处。"
            " 如果涉及术语，请优先使用标准中英对照。"
        )
        if language == "en-US":
            return f"{base} Prefer concise English output with explicit terminology."
        if language == "bilingual":
            return f"{base} 请输出中英双语答案。"
        return base

    @staticmethod
    def _build_user_prompt(
        *,
        question: str,
        rewritten_query: str,
        retrieval_hits: list[RetrievalHit],
        history: list[StoredMessage],
        glossary_terms: list[TermEntry],
        language: str,
    ) -> str:
        history_block = "\n".join(f"- {message.role}: {message.content}" for message in history) or "- 无"
        context_block = "\n".join(
            f"[{index + 1}] {hit.chunk.citation_label}: {hit.chunk.text}"
            for index, hit in enumerate(retrieval_hits)
        ) or "[1] 未命中检索结果"
        glossary_block = "\n".join(
            f"- {term.name_cn} = {term.name_en}: {term.summary}" for term in glossary_terms
        ) or "- 无"
        return (
            f"用户问题：{question}\n"
            f"改写检索词：{rewritten_query}\n"
            f"目标语言：{language}\n"
            f"近期会话：\n{history_block}\n"
            f"检索上下文：\n{context_block}\n"
            f"术语表：\n{glossary_block}\n"
            "请基于上下文作答，并在回答中体现术语规范。"
        )

    @staticmethod
    def _build_fallback_answer(
        payload: ChatQueryRequest,
        hits: list[RetrievalHit],
        glossary_terms: list[TermEntry],
    ) -> str:
        if hits:
            lead = hits[0].chunk.text[:140]
        else:
            lead = (
                f"当前未检索到与“{payload.question}”完全匹配的切片，"
                "建议继续扩充语料或优化问题描述。"
            )

        if payload.language == "en-US":
            answer = (
                f"Based on the retrieved context, {lead} "
                "This answer is generated by the local fallback pipeline because the Qwen API is not available."
            )
        elif payload.language == "bilingual":
            answer = (
                f"中文：根据检索到的上下文，{lead}\n"
                "English: Based on the retrieved context, the answer highlights the most relevant work, terminology, and background."
            )
        else:
            answer = (
                f"根据检索到的上下文，{lead}"
                " 当前回答由本地回退模板生成；如配置 Qwen API，可自动升级为真实大模型生成。"
            )

        if glossary_terms:
            answer += f" 本轮重点术语包括：{', '.join(term.name_cn for term in glossary_terms[:3])}。"
        return answer

    def _persist_turn(
        self,
        *,
        session_id: str,
        payload: ChatQueryRequest,
        answer: str,
        rewritten_query: str,
        citations: list[Citation],
        recommendations: RecommendationBlock,
        trace: dict[str, str],
    ) -> list[ChatMessageView]:
        if self.chat_repository is not None:
            prior_history = self._get_recent_history(session_id)
            session = self.chat_repository.get_or_create_session(
                session_id=session_id,
                preferred_language=payload.language,
                external_user_id=payload.external_user_id,
                title=self.runtime._build_session_title(payload.question),
            )
            user_message = self.chat_repository.add_message(
                session_id=session.id,
                role="user",
                language=payload.language,
                content=payload.question,
                rewritten_query=rewritten_query,
            )
            assistant_message = self.chat_repository.add_message(
                session_id=session.id,
                role="assistant",
                language=payload.language,
                content=answer,
                citations_json=[citation.model_dump() for citation in citations],
                recommendations_json=recommendations.model_dump(),
                trace_json=trace,
            )
            stored_messages = [
                StoredMessage(
                    id=user_message.id,
                    role="user",
                    language=user_message.language.value,
                    content=user_message.content,
                    created_at=user_message.created_at,
                    citations=[],
                    rewritten_query=user_message.rewritten_query,
                ),
                StoredMessage(
                    id=assistant_message.id,
                    role="assistant",
                    language=assistant_message.language.value,
                    content=assistant_message.content,
                    created_at=assistant_message.created_at,
                    citations=citations,
                ),
            ]
            self.chat_repository.update_session_state(
                session,
                preferred_language=payload.language,
                context_summary=self.runtime._build_context_summary(prior_history + stored_messages),
            )
            self.chat_repository.commit()
            return [
                ChatMessageView(
                    id=message.id,
                    role=message.role,
                    language=message.language,
                    content=message.content,
                    created_at=message.created_at,
                    citations=message.citations,
                )
                for message in stored_messages
            ]

        user_message, assistant_message = self.runtime.append_session_turn(
            session_id=session_id,
            question=payload.question,
            answer=answer,
            language=payload.language,
            citations=citations,
            rewritten_query=rewritten_query,
        )
        return [
            ChatMessageView(
                id=user_message.id,
                role=user_message.role,
                language=user_message.language,
                content=user_message.content,
                created_at=user_message.created_at,
                citations=user_message.citations,
            ),
            ChatMessageView(
                id=assistant_message.id,
                role=assistant_message.role,
                language=assistant_message.language,
                content=assistant_message.content,
                created_at=assistant_message.created_at,
                citations=assistant_message.citations,
            ),
        ]

    def _get_recent_history(self, session_id: str) -> list[StoredMessage]:
        if self.chat_repository is not None:
            return [
                StoredMessage(
                    id=message.id,
                    role=message.role.value,
                    language=message.language.value,
                    content=message.content,
                    created_at=message.created_at,
                    citations=[Citation.model_validate(item) for item in message.citations_json or []],
                    rewritten_query=message.rewritten_query,
                )
                for message in self.chat_repository.get_recent_messages(session_id)
            ]
        return self.runtime.get_recent_history(session_id)

    def _build_recommendations(
        self,
        question: str,
        hits: list[RetrievalHit],
        glossary_terms: list[TermEntry],
    ) -> RecommendationBlock:
        if self.catalog_service is None:
            return self.runtime.build_recommendations(hits, question)

        recommendations = RecommendationBlock(
            terms=[term.as_entity_reference() for term in glossary_terms[:3]]
        )
        combined_text = f"{question} {' '.join(hit.chunk.text for hit in hits)}".lower()
        for entity in self.catalog_service.search_entities():
            entity_text = f"{entity.name} {entity.summary or ''}".lower()
            if not entity_text or not any(token in entity_text for token in combined_text.split()):
                continue
            if entity.entity_type == "work" and len(recommendations.works) < 3:
                recommendations.works.append(entity)
            if entity.entity_type == "calligrapher" and len(recommendations.calligraphers) < 3:
                recommendations.calligraphers.append(entity)
        return recommendations

    @staticmethod
    def _build_demo_session(session_id: str) -> ChatSessionDetailResponse:
        demo_answer = f"可先关注《{WORK_LANTINGJI.title_cn}》等代表作。"
        now = datetime.now(timezone.utc)
        return ChatSessionDetailResponse(
            session_id=session_id,
            title="MVP 示例会话",
            preferred_language="zh-CN",
            context_summary="当前返回的是用于前后端联调的会话结构示例。",
            messages=[
                ChatMessageView(
                    id=f"msg-{uuid4()}",
                    role="user",
                    language="zh-CN",
                    content="王羲之代表作有哪些？",
                    created_at=now,
                    citations=[],
                ),
                ChatMessageView(
                    id=f"msg-{uuid4()}",
                    role="assistant",
                    language="zh-CN",
                    content=demo_answer,
                    created_at=now,
                    citations=[],
                ),
            ],
        )
