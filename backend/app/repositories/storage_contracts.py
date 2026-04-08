from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from app.models.entities import EntityType, KnowledgeChunk


MYSQL_AUTHORITY_TABLES = (
    "eras",
    "styles",
    "calligraphers",
    "works",
    "terms",
    "knowledge_documents",
    "knowledge_chunks",
    "knowledge_chunk_entity_links",
    "chat_sessions",
    "chat_messages",
    "ingest_jobs",
)

QDRANT_COLLECTION_KNOWLEDGE_CHUNKS = "knowledge_chunks"
QDRANT_DISTANCE = "Cosine"

NEO4J_NODE_LABELS = {
    EntityType.CALLIGRAPHER: "Calligrapher",
    EntityType.WORK: "Work",
    EntityType.TERM: "Term",
    EntityType.ERA: "Era",
    EntityType.STYLE: "Style",
}


class GraphRelation(str, Enum):
    CREATED = "CREATED"
    BELONGS_TO_ERA = "BELONGS_TO_ERA"
    HAS_STYLE = "HAS_STYLE"
    MENTIONS_TERM = "MENTIONS_TERM"
    INFLUENCED_BY = "INFLUENCED_BY"


@dataclass(slots=True)
class QdrantChunkPayload:
    chunk_id: str
    document_id: str
    chunk_index: int
    language: str
    source_type: str
    source_ref: str | None
    citation_label: str | None
    entity_refs: list[dict[str, str]]


def build_qdrant_payload(chunk: KnowledgeChunk) -> dict:
    payload = QdrantChunkPayload(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        language=chunk.language.value,
        source_type=chunk.source_type.value,
        source_ref=chunk.source_ref,
        citation_label=chunk.citation_label,
        entity_refs=[
            {
                "entity_type": link.entity_type.value,
                "entity_id": link.entity_id,
                "link_type": link.link_type.value,
            }
            for link in chunk.entity_links
        ],
    )
    return asdict(payload)


def graph_node_key(entity_type: EntityType, entity_id: str) -> str:
    label = NEO4J_NODE_LABELS[entity_type]
    return f"{label}:{entity_id}"


def redis_chat_window_key(session_id: str) -> str:
    return f"chat:session:{session_id}:window"


def redis_chat_summary_key(session_id: str) -> str:
    return f"chat:session:{session_id}:summary"


def redis_hot_query_cache_key(query_hash: str) -> str:
    return f"search:hot:{query_hash}"


def redis_ingest_lock_key(document_checksum: str) -> str:
    return f"ingest:lock:{document_checksum}"
