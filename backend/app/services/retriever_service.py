from __future__ import annotations

from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.term_repository import TermRepository
from app.services.rag_runtime import RAGRuntime, RetrievalHit, StoredChunk


class RetrieverService:
    """Retrieval service backed by persisted knowledge chunks."""

    def __init__(
        self,
        runtime: RAGRuntime,
        knowledge_repository: KnowledgeRepository | None = None,
        term_repository: TermRepository | None = None,
    ) -> None:
        self.runtime = runtime
        self.knowledge_repository = knowledge_repository
        self.term_repository = term_repository

    def rewrite_query(self, question: str) -> str:
        return self.runtime.rewrite_query(question)

    def retrieve(self, query: str, *, language: str, limit: int) -> list[RetrievalHit]:
        return self._retrieve_internal(query, language=language, limit=limit, original_query=None)

    def search_chunks(self, query: str, *, language: str, limit: int) -> list[RetrievalHit]:
        rewritten_query = self.rewrite_query(query)
        return self._retrieve_internal(rewritten_query, language=language, limit=limit, original_query=query)

    def _retrieve_internal(
        self,
        query: str,
        *,
        language: str,
        limit: int,
        original_query: str | None,
    ) -> list[RetrievalHit]:
        if self.knowledge_repository is None:
            return self.runtime.retrieve(query, language=language, limit=limit)

        scoring_query = original_query or query
        query_tokens = list(dict.fromkeys(self.runtime._tokenize(scoring_query)))
        rewritten_tokens = list(dict.fromkeys(self.runtime._tokenize(query)))
        query_vector = self.runtime._embed(query)
        query_term_ids = {term.id for term in self._collect_terms(scoring_query, query)}
        candidate_chunks = self.knowledge_repository.search_candidate_chunks(
            query_tokens=rewritten_tokens or query_tokens,
            language=language,
            limit=limit,
        )

        hits: list[RetrievalHit] = []
        normalized_language = self.runtime._normalize_language(language)
        for chunk in candidate_chunks:
            if normalized_language != "bilingual" and chunk.language.value not in {normalized_language, "bilingual"}:
                continue

            chunk_text = chunk.text or ""
            token_sequence = tuple(self.runtime._tokenize(chunk_text))
            chunk_tokens = set(token_sequence)
            chunk_vector = self.runtime._embed(chunk_text)
            lexical_overlap = self.runtime._lexical_overlap(set(query_tokens), chunk_tokens)
            vector_score = self.runtime._dot_product(query_vector, chunk_vector)
            chunk_term_ids = {
                link.entity_id
                for link in chunk.entity_links
                if link.entity_type.value == "term"
            }
            normalized_chunk = chunk.normalized_text or chunk_text.lower()
            citation_label = (chunk.citation_label or "").lower()
            original_lower = scoring_query.lower()
            exact_bonus = 0.14 if original_lower and original_lower in normalized_chunk else 0.0
            title_bonus = 0.16 if original_lower and original_lower in citation_label else 0.0
            coverage_bonus = self._coverage_bonus(query_tokens, chunk_tokens)
            title_term_bonus = self._title_term_bonus(query_tokens, citation_label)
            term_bonus = 0.1 if query_term_ids.intersection(chunk_term_ids) else 0.0
            primary_entity_bonus = self._primary_entity_bonus(
                query_terms=query_term_ids,
                query_tokens=query_tokens,
                chunk=chunk,
                chunk_text=chunk_text,
                citation_label=citation_label,
            )
            score = (
                (0.45 * vector_score)
                + (0.2 * lexical_overlap)
                + coverage_bonus
                + title_bonus
                + title_term_bonus
                + term_bonus
                + primary_entity_bonus
                + exact_bonus
            )
            if score <= 0:
                continue

            document = chunk.document
            document_title = document.title if document else "未命名文档"
            stored_chunk = StoredChunk(
                id=chunk.id,
                document_id=chunk.document_id,
                document_title=document_title,
                chunk_index=chunk.chunk_index,
                language=chunk.language.value,
                source_type=chunk.source_type.value,
                source_ref=chunk.source_ref,
                citation_label=chunk.citation_label or f"{document_title} 第 {chunk.chunk_index + 1} 段",
                text=chunk_text,
                normalized_text=chunk.normalized_text or chunk_text.lower(),
                tokens=token_sequence,
                vector=chunk_vector,
                matched_terms=tuple(chunk_term_ids),
            )
            hits.append(
                RetrievalHit(
                    chunk=stored_chunk,
                    score=round(score, 4),
                    lexical_overlap=round(lexical_overlap, 4),
                    matched_terms=self._collect_terms(query, chunk_text),
                )
            )

        hits.sort(
            key=lambda item: (
                item.score,
                item.lexical_overlap,
                self._stable_title_overlap(item.chunk.citation_label, query_tokens),
                -item.chunk.chunk_index,
            ),
            reverse=True,
        )
        return hits[:limit]

    def _collect_terms(self, *texts: str):
        if self.term_repository is not None:
            return self.term_repository.collect_terms(*texts)
        return self.runtime.build_glossary([text for text in texts if text])

    @staticmethod
    def _coverage_bonus(query_tokens: list[str], chunk_tokens: set[str]) -> float:
        if not query_tokens:
            return 0.0
        matched = sum(1 for token in query_tokens if token in chunk_tokens)
        return 0.22 * (matched / max(len(query_tokens), 1))

    @staticmethod
    def _title_term_bonus(query_tokens: list[str], citation_label: str) -> float:
        if not citation_label or not query_tokens:
            return 0.0
        title_hits = sum(1 for token in query_tokens if token in citation_label)
        return min(0.18, 0.06 * title_hits)

    @staticmethod
    def _stable_title_overlap(citation_label: str, query_tokens: list[str]) -> int:
        label = citation_label.lower()
        return sum(1 for token in query_tokens if token in label)

    def _primary_entity_bonus(self, *, query_terms: set[str], query_tokens: list[str], chunk, chunk_text: str, citation_label: str) -> float:
        primary_subject_bonus = 0.0
        for link in chunk.entity_links:
            if link.link_type.value != "primary_subject":
                continue
            if link.entity_type.value == "term" and link.entity_id in query_terms:
                primary_subject_bonus += 0.12
            elif any(token in chunk_text.lower() or token in citation_label for token in query_tokens):
                primary_subject_bonus += 0.05
        return min(primary_subject_bonus, 0.18)
