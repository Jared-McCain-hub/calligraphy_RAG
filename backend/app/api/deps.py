from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.knowledge_repository import KnowledgeRepository
from app.repositories.term_repository import TermRepository
from app.services.catalog_service import CatalogService
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService
from app.services.ingest_service import IngestService
from app.services.qwen_service import QwenService
from app.services.rag_runtime import RAGRuntime
from app.services.retriever_service import RetrieverService
from app.services.search_service import SearchService
from app.services.term_guard_service import TermGuardService


def get_catalog_repository(session: Session = Depends(get_db_session)) -> CatalogRepository:
    return CatalogRepository(session)


def get_term_repository(session: Session = Depends(get_db_session)) -> TermRepository:
    return TermRepository(session)


def get_knowledge_repository(session: Session = Depends(get_db_session)) -> KnowledgeRepository:
    return KnowledgeRepository(session)


def get_chat_repository(session: Session = Depends(get_db_session)) -> ChatRepository:
    return ChatRepository(session)


def get_catalog_service(
    repository: CatalogRepository = Depends(get_catalog_repository),
) -> CatalogService:
    return CatalogService(repository=repository)


@lru_cache(maxsize=1)
def get_rag_runtime() -> RAGRuntime:
    return RAGRuntime(settings=settings)


def get_retriever_service(
    knowledge_repository: KnowledgeRepository = Depends(get_knowledge_repository),
    term_repository: TermRepository = Depends(get_term_repository),
) -> RetrieverService:
    return RetrieverService(
        runtime=get_rag_runtime(),
        knowledge_repository=knowledge_repository,
        term_repository=term_repository,
    )


def get_term_guard_service(
    term_repository: TermRepository = Depends(get_term_repository),
) -> TermGuardService:
    return TermGuardService(runtime=get_rag_runtime(), term_repository=term_repository)


@lru_cache(maxsize=1)
def get_qwen_service() -> QwenService:
    return QwenService(settings=settings)


def get_chat_service(
    retriever_service: RetrieverService = Depends(get_retriever_service),
    term_guard_service: TermGuardService = Depends(get_term_guard_service),
    chat_repository: ChatRepository = Depends(get_chat_repository),
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> ChatService:
    return ChatService(
        runtime=get_rag_runtime(),
        retriever_service=retriever_service,
        term_guard_service=term_guard_service,
        qwen_service=get_qwen_service(),
        chat_repository=chat_repository,
        catalog_service=catalog_service,
    )


def get_search_service(
    catalog_service: CatalogService = Depends(get_catalog_service),
    retriever_service: RetrieverService = Depends(get_retriever_service),
) -> SearchService:
    return SearchService(
        catalog_service=catalog_service,
        retriever_service=retriever_service,
    )


@lru_cache(maxsize=1)
def get_graph_service() -> GraphService:
    return GraphService()


def get_ingest_service(
    knowledge_repository: KnowledgeRepository = Depends(get_knowledge_repository),
    term_repository: TermRepository = Depends(get_term_repository),
) -> IngestService:
    return IngestService(
        runtime=get_rag_runtime(),
        knowledge_repository=knowledge_repository,
        term_repository=term_repository,
    )
