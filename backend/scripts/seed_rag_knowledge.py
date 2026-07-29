from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.models  # noqa: F401
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import create_all_tables, create_database_if_not_exists, get_session_factory
from app.models import (
    ChunkLinkType,
    EntityType,
    Calligrapher,
    Term,
    Work,
)
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.term_repository import TermRepository
from app.schemas.ingest import IngestRequest
from app.services.ingest_service import IngestService
from app.services.rag_runtime import RAGRuntime


def seed_reference_rag_knowledge(session: Session) -> dict[str, int]:
    runtime = RAGRuntime(settings=settings)
    knowledge_repository = KnowledgeRepository(session)
    term_repository = TermRepository(session)
    ingest_service = IngestService(
        runtime=runtime,
        knowledge_repository=knowledge_repository,
        term_repository=term_repository,
    )

    counts = {"documents": 0, "chunks": 0, "chunk_entity_links": 0}

    for term in session.scalars(select(Term).options(selectinload(Term.works))).all():
        response = ingest_service.create_job(
            IngestRequest(
                title=f"术语：{term.name_cn}",
                source_type="manual",
                source_ref=f"seed/reference/term/{term.slug}",
                requested_by="system-reference-seed",
                language="zh-CN",
                raw_text=_build_term_text(term),
            )
        )
        counts["documents"] += 1
        counts["chunks"] += response.processed_chunks
        counts["chunk_entity_links"] += _link_document_entities(
            knowledge_repository=knowledge_repository,
            document_id=response.document_id,
            primary_entity_type=EntityType.TERM,
            primary_entity_id=term.id,
            mentioned_terms=[term.id],
        )

    calligraphers = session.scalars(
        select(Calligrapher).options(
            selectinload(Calligrapher.era),
            selectinload(Calligrapher.primary_style),
            selectinload(Calligrapher.works),
        )
    ).all()
    for calligrapher in calligraphers:
        response = ingest_service.create_job(
            IngestRequest(
                title=f"书法家：{calligrapher.name_cn}",
                source_type="manual",
                source_ref=f"seed/reference/calligrapher/{calligrapher.slug}",
                requested_by="system-reference-seed",
                language="zh-CN",
                raw_text=_build_calligrapher_text(calligrapher),
            )
        )
        counts["documents"] += 1
        counts["chunks"] += response.processed_chunks
        counts["chunk_entity_links"] += _link_document_entities(
            knowledge_repository=knowledge_repository,
            document_id=response.document_id,
            primary_entity_type=EntityType.CALLIGRAPHER,
            primary_entity_id=calligrapher.id,
            mentioned_terms=[],
        )

    works = session.scalars(
        select(Work).options(
            selectinload(Work.calligrapher),
            selectinload(Work.era),
            selectinload(Work.style),
            selectinload(Work.terms),
        )
    ).all()
    for work in works:
        response = ingest_service.create_job(
            IngestRequest(
                title=f"作品：{work.title_cn}",
                source_type="manual",
                source_ref=f"seed/reference/work/{work.slug}",
                requested_by="system-reference-seed",
                language="zh-CN",
                raw_text=_build_work_text(work),
            )
        )
        counts["documents"] += 1
        counts["chunks"] += response.processed_chunks
        counts["chunk_entity_links"] += _link_document_entities(
            knowledge_repository=knowledge_repository,
            document_id=response.document_id,
            primary_entity_type=EntityType.WORK,
            primary_entity_id=work.id,
            mentioned_terms=[term.id for term in work.terms],
        )

    return counts


def _link_document_entities(
    *,
    knowledge_repository: KnowledgeRepository,
    document_id: str | None,
    primary_entity_type: EntityType,
    primary_entity_id: str,
    mentioned_terms: list[str],
) -> int:
    if not document_id:
        return 0

    document = knowledge_repository.get_document_with_chunks(document_id)
    if document is None:
        return 0

    created = 0
    for chunk in document.chunks:
        if knowledge_repository.link_chunk_entity(
            chunk_id=chunk.id,
            entity_type=primary_entity_type,
            entity_id=primary_entity_id,
            link_type=ChunkLinkType.PRIMARY_SUBJECT,
            confidence=100,
        ):
            created += 1
        for term_id in mentioned_terms:
            if knowledge_repository.link_chunk_term(chunk_id=chunk.id, term_id=term_id):
                created += 1
    knowledge_repository.commit()
    return created


def _build_term_text(term: Term) -> str:
    related_works = "、".join(work.title_cn for work in term.works[:5]) or "暂无"
    aliases = "、".join(term.aliases_json or []) or "无"
    parts = [
        f"{term.name_cn}（{term.name_en or '暂无英文名'}）是中国书法知识库中的术语条目。",
        f"分类：{term.category or '未分类'}。",
        f"定义：{term.definition or '暂无定义说明'}。",
        f"使用说明：{term.usage_notes or '暂无补充说明'}。",
        f"常见别名：{aliases}。",
        f"相关作品：{related_works}。",
    ]
    return " ".join(parts)


def _build_calligrapher_text(calligrapher: Calligrapher) -> str:
    representative_works = "、".join(work.title_cn for work in calligrapher.works[:5]) or "暂无"
    period = " - ".join(str(value) for value in [calligrapher.birth_year, calligrapher.death_year] if value)
    aliases = "、".join(calligrapher.aliases_json or []) or "无"
    parts = [
        f"{calligrapher.name_cn}（{calligrapher.name_en or '暂无英文名'}）是中国书法知识库中的书法家条目。",
        f"所属时代：{calligrapher.era.name_cn if calligrapher.era else '待补充'}。",
        f"主要书体或风格：{calligrapher.primary_style.name_cn if calligrapher.primary_style else '待补充'}。",
        f"生卒信息：{period or '待补充'}。",
        f"籍贯：{calligrapher.hometown or '待补充'}。",
        f"别名：{aliases}。",
        f"生平简介：{calligrapher.biography or '暂无简介'}。",
        f"成就说明：{calligrapher.achievements or '暂无成就说明'}。",
        f"代表作品：{representative_works}。",
    ]
    return " ".join(parts)


def _build_work_text(work: Work) -> str:
    related_terms = "、".join(term.name_cn for term in work.terms[:6]) or "暂无"
    parts = [
        f"{work.title_cn}（{work.title_en or '暂无英文名'}）是中国书法知识库中的作品条目。",
        f"作者：{work.calligrapher.name_cn if work.calligrapher else '待补充'}。",
        f"时代：{work.era.name_cn if work.era else '待补充'}。",
        f"书体风格：{work.style.name_cn if work.style else '待补充'}。",
        f"真伪属性：{work.authenticity.value}。",
        f"创作时期：{work.creation_period or '待补充'}。",
        f"材质：{work.material or '待补充'}。",
        f"尺幅：{work.dimensions or '待补充'}。",
        f"收藏信息：{work.current_collection or '待补充'}。",
        f"作品说明：{work.description or '暂无说明'}。",
        f"作品摘录：{work.excerpt_text or '暂无摘录'}。",
        f"关联术语：{related_terms}。",
    ]
    return " ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed initial RAG knowledge from reference entities.")
    parser.add_argument(
        "--ensure-db",
        action="store_true",
        help="Create the MySQL database and tables before seeding RAG knowledge.",
    )
    args = parser.parse_args()

    if args.ensure_db:
        create_database_if_not_exists()
        create_all_tables()

    session = get_session_factory()()
    try:
        counts = seed_reference_rag_knowledge(session)
    finally:
        session.close()

    print("Reference RAG knowledge seeded.")
    for key, value in counts.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
