from __future__ import annotations

import re

from app.schemas.search import SearchHit, SearchRequest, SearchResponse
from app.services.catalog_service import CatalogService
from app.services.retriever_service import RetrieverService


class SearchService:
    """Unified search across curated entities and ingested knowledge chunks."""

    def __init__(self, catalog_service: CatalogService, retriever_service: RetrieverService) -> None:
        self.catalog_service = catalog_service
        self.retriever_service = retriever_service

    def search(self, payload: SearchRequest) -> SearchResponse:
        normalized_query = payload.query.strip()
        allowed_types = set(payload.entity_types)
        needle = normalized_query.lower()
        query_terms = self._extract_query_terms(normalized_query)

        entity_hits: list[SearchHit] = []
        for entity in self.catalog_service.search_entities():
            if allowed_types and entity.entity_type not in allowed_types:
                continue
            score = self._score_entity_hit(entity_name=entity.name, entity_summary=entity.summary, needle=needle, query_terms=query_terms)
            if score <= 0:
                continue

            highlights = self._build_entity_highlights(entity.name, entity.summary, query_terms)
            entity_hits.append(
                SearchHit(
                    id=entity.id,
                    entity_type=entity.entity_type,
                    name=entity.name,
                    summary=entity.summary,
                    score=score,
                    highlights=highlights[:2],
                )
            )

        chunk_hits_for_response: list[SearchHit] = []
        if not allowed_types or "knowledge_chunk" in allowed_types:
            chunk_hits = self.retriever_service.search_chunks(
                normalized_query,
                language="bilingual",
                limit=payload.limit,
            )
            for chunk_hit in chunk_hits:
                term_highlights = [f"{term.name_cn} / {term.name_en}" for term in chunk_hit.matched_terms[:2]]
                chunk_hits_for_response.append(
                    SearchHit(
                        id=chunk_hit.chunk.id,
                        entity_type="knowledge_chunk",
                        name=chunk_hit.chunk.citation_label,
                        summary=chunk_hit.chunk.text[:140],
                        score=chunk_hit.score,
                        highlights=[chunk_hit.chunk.document_title, *term_highlights][:2],
                    )
                )

        entity_hits.sort(
            key=lambda item: (
                item.score,
                self._entity_type_priority(item.entity_type),
                self._query_term_overlap(item.name, item.summary, query_terms),
                item.name,
            ),
            reverse=True,
        )
        chunk_hits_for_response.sort(
            key=lambda item: (
                item.score,
                self._query_term_overlap(item.name, item.summary, query_terms),
                item.name,
            ),
            reverse=True,
        )
        limited_hits = self._blend_hits(
            entity_hits=entity_hits,
            chunk_hits=chunk_hits_for_response,
            limit=payload.limit,
            allowed_types=allowed_types,
        )
        return SearchResponse(
            query=payload.query,
            normalized_query=normalized_query,
            total=len(limited_hits),
            items=limited_hits,
        )

    @staticmethod
    def _extract_query_terms(query: str) -> list[str]:
        terms = [term.strip().lower() for term in re.split(r"\s+", query) if term.strip()]
        if not terms and query.strip():
            terms = [query.strip().lower()]
        return terms

    def _score_entity_hit(
        self,
        *,
        entity_name: str,
        entity_summary: str | None,
        needle: str,
        query_terms: list[str],
    ) -> float:
        name = entity_name.lower()
        summary = (entity_summary or "").lower()
        haystack = f"{name} {summary}".strip()
        if not haystack:
            return 0.0

        score = 0.0
        if needle and needle in name:
            score += 0.9
        elif needle and needle in haystack:
            score += 0.6

        if query_terms:
            name_hits = sum(1 for term in query_terms if term in name)
            haystack_hits = sum(1 for term in query_terms if term in haystack)
            coverage = haystack_hits / max(len(query_terms), 1)
            score += min(0.3, 0.12 * name_hits)
            score += min(0.2, 0.06 * max(haystack_hits - name_hits, 0))
            score += 0.25 * coverage

        if score <= 0 and needle and needle not in haystack:
            return 0.0
        return round(max(score, 0.18), 4)

    @staticmethod
    def _build_entity_highlights(
        entity_name: str,
        entity_summary: str | None,
        query_terms: list[str],
    ) -> list[str]:
        highlights: list[str] = [entity_name]
        if entity_summary:
            highlights.append(entity_summary)
        prioritized = [text for text in highlights if any(term in text.lower() for term in query_terms)] or highlights
        return prioritized[:2]

    @staticmethod
    def _query_term_overlap(name: str, summary: str | None, query_terms: list[str]) -> int:
        haystack = f"{name} {summary or ''}".lower()
        return sum(1 for term in query_terms if term in haystack)

    @staticmethod
    def _entity_type_priority(entity_type: str) -> int:
        priorities = {
            "calligrapher": 5,
            "term": 4,
            "work": 3,
            "knowledge_chunk": 2,
            "style": 1,
            "era": 0,
        }
        return priorities.get(entity_type, 0)

    @staticmethod
    def _blend_hits(
        *,
        entity_hits: list[SearchHit],
        chunk_hits: list[SearchHit],
        limit: int,
        allowed_types: set[str],
    ) -> list[SearchHit]:
        if allowed_types and "knowledge_chunk" not in allowed_types:
            return entity_hits[:limit]
        if allowed_types == {"knowledge_chunk"}:
            return chunk_hits[:limit]
        if not entity_hits:
            return chunk_hits[:limit]
        if not chunk_hits:
            return entity_hits[:limit]

        entity_quota = min(len(entity_hits), max(2, limit // 3))
        blended: list[SearchHit] = []
        blended.extend(entity_hits[:entity_quota])

        chunk_slots = max(limit - len(blended), 0)
        blended.extend(chunk_hits[:chunk_slots])

        overflow = entity_hits[entity_quota:]
        if len(blended) < limit and overflow:
            blended.extend(overflow[: limit - len(blended)])

        blended.sort(
            key=lambda item: (
                item.score,
                SearchService._entity_type_priority(item.entity_type),
                item.name,
            ),
            reverse=True,
        )
        return blended[:limit]
