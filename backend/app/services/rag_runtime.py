from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import sqrt
from threading import RLock
from uuid import uuid4

from app.core.config import Settings
from app.schemas.common import Citation, EntityReference, RecommendationBlock
from app.services.catalog_service import CALLIGRAPHER_WANG, WORK_LANTINGJI

TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]")


@dataclass(slots=True)
class TermEntry:
    id: str
    name_cn: str
    name_en: str
    summary: str
    aliases: tuple[str, ...] = ()

    def as_entity_reference(self) -> EntityReference:
        return EntityReference(
            id=self.id,
            entity_type="term",
            name=f"{self.name_cn} / {self.name_en}",
            summary=self.summary,
        )


@dataclass(slots=True)
class StoredChunk:
    id: str
    document_id: str
    document_title: str
    chunk_index: int
    language: str
    source_type: str
    source_ref: str | None
    citation_label: str
    text: str
    normalized_text: str
    tokens: tuple[str, ...]
    vector: tuple[float, ...]
    matched_terms: tuple[str, ...] = ()


@dataclass(slots=True)
class StoredDocument:
    id: str
    title: str
    language: str
    source_type: str
    source_ref: str | None
    parsed_text: str
    summary: str
    created_at: datetime
    chunk_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StoredMessage:
    id: str
    role: str
    language: str
    content: str
    created_at: datetime
    citations: list[Citation] = field(default_factory=list)
    rewritten_query: str | None = None


@dataclass(slots=True)
class SessionState:
    session_id: str
    title: str
    preferred_language: str
    context_summary: str | None
    last_message_at: datetime
    messages: list[StoredMessage] = field(default_factory=list)


@dataclass(slots=True)
class RetrievalHit:
    chunk: StoredChunk
    score: float
    lexical_overlap: float
    matched_terms: list[TermEntry]


@dataclass(slots=True)
class IngestResult:
    job_id: str
    document_id: str
    updated_at: datetime
    chunk_count: int
    matched_terms: list[TermEntry]


DEFAULT_TERM_ENTRIES = (
    TermEntry(
        id="term-running-script",
        name_cn="行书",
        name_en="Running Script",
        summary="介于楷书与草书之间，兼具速度与辨识度的书体。",
        aliases=("running script", "xingshu", "semi-cursive"),
    ),
    TermEntry(
        id="term-regular-script",
        name_cn="楷书",
        name_en="Regular Script",
        summary="结构规整、笔画清晰，是学习书法时常见的基础书体。",
        aliases=("regular script", "kaishu", "standard script"),
    ),
    TermEntry(
        id="term-yan-style",
        name_cn="颜体",
        name_en="Yan Style",
        summary="以颜真卿书风为代表的楷书风格，强调雄浑厚重。",
        aliases=("yan style", "yan zhenqing style", "颜真卿书风"),
    ),
    TermEntry(
        id="term-clerical-script",
        name_cn="隶书",
        name_en="Clerical Script",
        summary="起源较早、蚕头燕尾特征明显的书体。",
        aliases=("clerical script", "lishu"),
    ),
)


class RAGRuntime:
    """In-memory runtime that mirrors the planned RAG pipeline shape."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = RLock()
        self._documents: dict[str, StoredDocument] = {}
        self._chunks: dict[str, StoredChunk] = {}
        self._sessions: dict[str, SessionState] = {}
        self._term_entries = {entry.id: entry for entry in DEFAULT_TERM_ENTRIES}
        self._term_lookup = self._build_term_lookup(DEFAULT_TERM_ENTRIES)
        self._ensure_seed_data()

    def ingest_document(
        self,
        *,
        title: str,
        raw_text: str,
        language: str,
        source_type: str,
        source_ref: str | None,
    ) -> IngestResult:
        now = datetime.now(timezone.utc)
        normalized_text = self._normalize_text(raw_text)
        document_id = f"doc-{uuid4()}"
        job_id = f"ingest-{uuid4()}"
        summary = self._summarize_text(normalized_text)
        chunk_texts = self._chunk_text(normalized_text)
        matched_term_ids: set[str] = set()

        with self._lock:
            document = StoredDocument(
                id=document_id,
                title=title,
                language=self._normalize_language(language),
                source_type=source_type,
                source_ref=source_ref,
                parsed_text=normalized_text,
                summary=summary,
                created_at=now,
            )
            self._documents[document_id] = document

            for chunk_index, chunk_text in enumerate(chunk_texts):
                chunk_id = f"chunk-{uuid4()}"
                terms = self.collect_terms(chunk_text)
                matched_term_ids.update(term.id for term in terms)
                normalized_chunk = chunk_text.lower()
                tokens = tuple(self._tokenize(chunk_text))
                chunk = StoredChunk(
                    id=chunk_id,
                    document_id=document_id,
                    document_title=title,
                    chunk_index=chunk_index,
                    language=document.language,
                    source_type=source_type,
                    source_ref=source_ref,
                    citation_label=f"{title} 第 {chunk_index + 1} 段",
                    text=chunk_text,
                    normalized_text=normalized_chunk,
                    tokens=tokens,
                    vector=self._embed(chunk_text),
                    matched_terms=tuple(term.id for term in terms),
                )
                self._chunks[chunk_id] = chunk
                document.chunk_ids.append(chunk_id)

        return IngestResult(
            job_id=job_id,
            document_id=document_id,
            updated_at=now,
            chunk_count=len(chunk_texts),
            matched_terms=[self._term_entries[term_id] for term_id in sorted(matched_term_ids)],
        )

    def reindex_chunks(self) -> int:
        processed = 0
        with self._lock:
            for chunk_id, chunk in list(self._chunks.items()):
                refreshed = StoredChunk(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    chunk_index=chunk.chunk_index,
                    language=chunk.language,
                    source_type=chunk.source_type,
                    source_ref=chunk.source_ref,
                    citation_label=chunk.citation_label,
                    text=chunk.text,
                    normalized_text=chunk.text.lower(),
                    tokens=tuple(self._tokenize(chunk.text)),
                    vector=self._embed(chunk.text),
                    matched_terms=tuple(term.id for term in self.collect_terms(chunk.text)),
                )
                self._chunks[chunk_id] = refreshed
                processed += 1
        return processed

    def rewrite_query(self, question: str) -> str:
        normalized = self._normalize_text(question).replace("？", "").replace("?", "")
        rewrite_parts = [normalized]

        if "什么是" in normalized or "定义" in normalized:
            rewrite_parts.append("术语 定义 标准英文翻译")
        if "代表作" in normalized:
            rewrite_parts.append("代表作 作品介绍 书法风格")
        if "王羲之" in normalized:
            rewrite_parts.append("王羲之 兰亭集序 行书")

        for term in self.collect_terms(normalized):
            rewrite_parts.append(term.name_cn)
            rewrite_parts.append(term.name_en)

        unique_parts = []
        for part in rewrite_parts:
            if part and part not in unique_parts:
                unique_parts.append(part)
        return " ".join(unique_parts)

    def retrieve(self, query: str, *, language: str, limit: int) -> list[RetrievalHit]:
        normalized_language = self._normalize_language(language)
        query_vector = self._embed(query)
        query_tokens = set(self._tokenize(query))
        query_term_ids = {term.id for term in self.collect_terms(query)}

        hits: list[RetrievalHit] = []
        with self._lock:
            for chunk in self._chunks.values():
                if normalized_language != "bilingual" and chunk.language not in {normalized_language, "bilingual"}:
                    continue

                lexical_overlap = self._lexical_overlap(query_tokens, set(chunk.tokens))
                vector_score = self._dot_product(query_vector, chunk.vector)
                exact_bonus = 0.12 if query.lower() in chunk.normalized_text else 0.0
                term_bonus = 0.08 if query_term_ids.intersection(chunk.matched_terms) else 0.0
                score = (0.7 * vector_score) + (0.3 * lexical_overlap) + exact_bonus + term_bonus

                if score <= 0:
                    continue

                hits.append(
                    RetrievalHit(
                        chunk=chunk,
                        score=round(score, 4),
                        lexical_overlap=round(lexical_overlap, 4),
                        matched_terms=[self._term_entries[term_id] for term_id in chunk.matched_terms],
                    )
                )

        hits.sort(key=lambda item: (item.score, item.lexical_overlap, -item.chunk.chunk_index), reverse=True)
        return hits[:limit]

    def search_chunks(self, query: str, *, language: str, limit: int) -> list[RetrievalHit]:
        rewritten_query = self.rewrite_query(query)
        return self.retrieve(rewritten_query, language=language, limit=limit)

    def collect_terms(self, text: str) -> list[TermEntry]:
        normalized = text.lower()
        matched: list[TermEntry] = []
        seen: set[str] = set()
        for needle, term_id in self._term_lookup.items():
            if needle in normalized and term_id not in seen:
                matched.append(self._term_entries[term_id])
                seen.add(term_id)
        return matched

    def build_glossary(self, texts: list[str]) -> list[TermEntry]:
        matched: dict[str, TermEntry] = {}
        for text in texts:
            for term in self.collect_terms(text):
                matched[term.id] = term
        return sorted(matched.values(), key=lambda item: item.name_cn)

    def build_citations(self, hits: list[RetrievalHit], limit: int = 3) -> list[Citation]:
        citations: list[Citation] = []
        for hit in hits[:limit]:
            citations.append(
                Citation(
                    chunk_id=hit.chunk.id,
                    quote=hit.chunk.text[:220],
                    source_label=hit.chunk.citation_label,
                    document_title=hit.chunk.document_title,
                    source_ref=hit.chunk.source_ref,
                )
            )
        return citations

    def build_recommendations(self, hits: list[RetrievalHit], question: str) -> RecommendationBlock:
        term_map = {term.id: term for term in self.build_glossary([question, *[hit.chunk.text for hit in hits]])}
        recommendations = RecommendationBlock()

        lowered = question.lower()
        if "王羲之" in question or "wang xizhi" in lowered:
            recommendations.calligraphers.append(
                EntityReference(
                    id=CALLIGRAPHER_WANG.id,
                    entity_type="calligrapher",
                    name=f"{CALLIGRAPHER_WANG.name_cn} / {CALLIGRAPHER_WANG.name_en}",
                    summary=CALLIGRAPHER_WANG.biography,
                )
            )

        if "兰亭" in question or "lanting" in lowered or any("兰亭" in hit.chunk.text for hit in hits):
            recommendations.works.append(
                EntityReference(
                    id=WORK_LANTINGJI.id,
                    entity_type="work",
                    name=f"{WORK_LANTINGJI.title_cn} / {WORK_LANTINGJI.title_en}",
                    summary=WORK_LANTINGJI.description,
                )
            )

        recommendations.terms = [term.as_entity_reference() for term in term_map.values()][:3]
        return recommendations

    def append_session_turn(
        self,
        *,
        session_id: str,
        question: str,
        answer: str,
        language: str,
        citations: list[Citation],
        rewritten_query: str,
    ) -> tuple[StoredMessage, StoredMessage]:
        now = datetime.now(timezone.utc)
        normalized_language = self._normalize_language(language)
        user_message = StoredMessage(
            id=f"msg-{uuid4()}",
            role="user",
            language=normalized_language,
            content=question,
            created_at=now,
            rewritten_query=rewritten_query,
        )
        assistant_message = StoredMessage(
            id=f"msg-{uuid4()}",
            role="assistant",
            language=normalized_language,
            content=answer,
            created_at=now,
            citations=citations,
        )

        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = SessionState(
                    session_id=session_id,
                    title=self._build_session_title(question),
                    preferred_language=normalized_language,
                    context_summary=None,
                    last_message_at=now,
                )
                self._sessions[session_id] = session

            session.messages.extend([user_message, assistant_message])
            session.preferred_language = normalized_language
            session.last_message_at = now
            session.context_summary = self._build_context_summary(session.messages)

        return user_message, assistant_message

    def get_session(self, session_id: str) -> SessionState | None:
        with self._lock:
            return self._sessions.get(session_id)

    def get_recent_history(self, session_id: str, limit: int = 4) -> list[StoredMessage]:
        session = self.get_session(session_id)
        if session is None:
            return []
        return session.messages[-limit:]

    def list_documents(self) -> list[StoredDocument]:
        with self._lock:
            return list(self._documents.values())

    def _ensure_seed_data(self) -> None:
        if self._documents:
            return

        self.ingest_document(
            title="王羲之与《兰亭集序》导读",
            raw_text=(
                "王羲之被后世尊为书圣，东晋时期的《兰亭集序》被视为行书典范。"
                " 这件作品不仅体现了行书在速度与节奏上的优势，也展示了文人雅集的文化背景。"
                " 在跨语言介绍中，行书应优先规范翻译为 Running Script，避免随意表述。"
                " 当用户询问代表作时，可以结合《兰亭集序》、书风特点和时代背景进行回答。"
            ),
            language="zh-CN",
            source_type="document",
            source_ref="seed/wang-xizhi-guide",
        )
        self.ingest_document(
            title="颜体术语说明",
            raw_text=(
                "颜体通常指颜真卿书风体系，英文宜规范为 Yan Style。"
                " 它建立在楷书基础上，但强调厚重、雄浑与骨力。"
                " 当用户提问什么是颜体时，回答应同时给出定义、代表性审美特征与标准英文译法。"
            ),
            language="zh-CN",
            source_type="manual",
            source_ref="seed/yan-style-term",
        )

    @staticmethod
    def _build_term_lookup(entries: tuple[TermEntry, ...]) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for entry in entries:
            for needle in (entry.name_cn, entry.name_en, *entry.aliases):
                lookup[needle.lower()] = entry.id
        return lookup

    @staticmethod
    def _normalize_language(language: str) -> str:
        supported = {"zh-CN", "en-US", "bilingual"}
        return language if language in supported else "zh-CN"

    @staticmethod
    def _normalize_text(text: str) -> str:
        compact = " ".join(text.split())
        return compact.strip()

    @staticmethod
    def _summarize_text(text: str) -> str:
        if len(text) <= 120:
            return text
        return f"{text[:117]}..."

    def _chunk_text(self, text: str) -> list[str]:
        if not text:
            return ["待补充语料内容。"]

        size = max(self.settings.rag_chunk_size, 80)
        overlap = min(self.settings.rag_chunk_overlap, size // 2)
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunks.append(text[start:end].strip())
            if end >= len(text):
                break
            start = max(end - overlap, start + 1)
        return [chunk for chunk in chunks if chunk]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return TOKEN_PATTERN.findall(text.lower())

    def _embed(self, text: str) -> tuple[float, ...]:
        dimensions = self.settings.embedding_dimensions
        vector = [0.0] * dimensions
        token_counts = Counter(self._tokenize(text))

        if not token_counts:
            return tuple(vector)

        for token, count in token_counts.items():
            digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % dimensions
            sign = 1.0 if int(digest[-1], 16) % 2 == 0 else -1.0
            vector[index] += sign * float(count)

        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return tuple(value / norm for value in vector)

    @staticmethod
    def _dot_product(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        return sum(left_value * right_value for left_value, right_value in zip(left, right))

    @staticmethod
    def _lexical_overlap(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left.intersection(right)) / max(len(left), 1)

    @staticmethod
    def _build_session_title(question: str) -> str:
        return question[:24] or "新会话"

    @staticmethod
    def _build_context_summary(messages: list[StoredMessage]) -> str | None:
        if not messages:
            return None
        latest_question = next((msg.content for msg in reversed(messages) if msg.role == "user"), None)
        latest_answer = next((msg.content for msg in reversed(messages) if msg.role == "assistant"), None)
        if latest_question and latest_answer:
            return f"最近围绕“{latest_question[:20]}”进行了问答，系统已生成带引用的回答。"
        return None
