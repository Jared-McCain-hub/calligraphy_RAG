"""Seed Qdrant with knowledge chunks from reference data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.repositories.qdrant_repository import QdrantRepository
from app.services.embedding_service import EmbeddingService

DATA_DIR = BACKEND_ROOT / "data"


def load_json_data(filename: str) -> list[dict]:
    """Load JSON data from data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"Warning: {filepath} not found")
        return []
    
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def build_knowledge_chunks() -> tuple[list[dict], list[str]]:
    """Build knowledge chunks from reference data.
    
    Returns:
        Tuple of (chunks_metadata, texts_for_embedding)
    """
    chunks = []
    texts = []
    
    # 1. Load calligraphers
    print("加载书法家数据...")
    calligraphers = load_json_data("calligraphers.json")
    for c in calligraphers:
        # Main biography chunk
        text = f"{c['name_cn']}（{c.get('name_en', '')}），{c.get('era', '')}书法家。"
        if c.get('biography'):
            text += f" {c['biography']}"
        if c.get('achievements'):
            text += f" {c['achievements']}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_id": c["slug"],
            "document_title": f"{c['name_cn']}简介",
            "chunk_index": 0,
            "language": "zh-CN",
            "source_type": "calligrapher",
            "source_ref": c.get("source_url"),
            "entity_type": "calligrapher",
            "entity_id": c.get("slug"),
            "entity_name": c["name_cn"],
        })
        texts.append(text)
        
        # Representative works chunk
        if c.get('representative_works'):
            works_text = f"{c['name_cn']}的代表作包括：{', '.join(c['representative_works'])}。"
            chunks.append({
                "id": str(uuid4()),
                "text": works_text,
                "document_id": c["slug"],
                "document_title": f"{c['name_cn']}代表作",
                "chunk_index": 1,
                "language": "zh-CN",
                "source_type": "calligrapher",
                "source_ref": c.get("source_url"),
                "entity_type": "calligrapher",
                "entity_id": c.get("slug"),
                "entity_name": c["name_cn"],
            })
            texts.append(works_text)
    
    # 2. Load terms
    print("加载术语数据...")
    terms = load_json_data("terms.json")
    for t in terms:
        text = f"{t['name_cn']}（{t.get('name_en', '')}）：{t.get('definition', '')}"
        if t.get('usage_notes'):
            text += f" {t['usage_notes']}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_id": t["slug"],
            "document_title": f"{t['name_cn']}术语解释",
            "chunk_index": 0,
            "language": "zh-CN",
            "source_type": "term",
            "source_ref": t.get("source_url"),
            "entity_type": "term",
            "entity_id": t.get("slug"),
            "entity_name": t["name_cn"],
        })
        texts.append(text)
    
    # 3. Load works
    print("加载作品数据...")
    works = load_json_data("works.json")
    for w in works:
        text = f"《{w['title_cn']}》"
        if w.get('title_en'):
            text += f"（{w['title_en']}）"
        text += f"，{w.get('calligrapher', '')}{w.get('era', '')}作品，{w.get('style', '')}。"
        if w.get('description'):
            text += f" {w['description']}"
        if w.get('significance'):
            text += f" {w['significance']}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_id": w["slug"],
            "document_title": w["title_cn"],
            "chunk_index": 0,
            "language": "zh-CN",
            "source_type": "work",
            "source_ref": w.get("source_url"),
            "entity_type": "work",
            "entity_id": w.get("slug"),
            "entity_name": w["title_cn"],
        })
        texts.append(text)
    
    # 4. Load eras
    print("加载朝代数据...")
    eras = load_json_data("eras.json")
    for e in eras:
        text = f"{e['name_cn']}（{e.get('name_en', '')}）：{e.get('summary', '')}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_id": e["slug"],
            "document_title": f"{e['name_cn']}书法概况",
            "chunk_index": 0,
            "language": "zh-CN",
            "source_type": "era",
            "source_ref": None,
            "entity_type": "era",
            "entity_id": e.get("slug"),
            "entity_name": e["name_cn"],
        })
        texts.append(text)
    
    # 5. Load styles
    print("加载书体数据...")
    styles = load_json_data("styles.json")
    for s in styles:
        text = f"{s['name_cn']}（{s.get('name_en', '')}）：{s.get('description', '')}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_id": s["slug"],
            "document_title": f"{s['name_cn']}书体介绍",
            "chunk_index": 0,
            "language": "zh-CN",
            "source_type": "style",
            "source_ref": None,
            "entity_type": "style",
            "entity_id": s.get("slug"),
            "entity_name": s["name_cn"],
        })
        texts.append(text)
    
    return chunks, texts


def seed_qdrant(
    use_memory: bool = True,
    host: str = "localhost",
    port: int = 6333,
) -> dict:
    """Seed Qdrant with knowledge chunks.
    
    Args:
        use_memory: If True, use in-memory mode
        host: Qdrant server host
        port: Qdrant server port
        
    Returns:
        Summary of seeded data
    """
    print("=" * 60)
    print("开始导入数据到 Qdrant")
    print("=" * 60)
    
    # Load data
    chunks, texts = build_knowledge_chunks()
    
    # Build embeddings
    print(f"\n生成向量（共 {len(texts)} 条）...")
    embedding_service = EmbeddingService()
    vectors = embedding_service.encode_to_list(texts)
    
    # Initialize Qdrant
    print("\n初始化 Qdrant...")
    repo = QdrantRepository(
        use_memory=use_memory,
        host=host,
        port=port,
    )
    
    # Clear existing data
    repo.delete_collection()
    repo._ensure_collection()
    
    # Upsert vectors
    print("\n导入向量数据...")
    count = repo.upsert_chunks(chunks, vectors)
    
    # Build summary
    summary = {
        "total_chunks": count,
        "calligraphers": len([c for c in chunks if c["source_type"] == "calligrapher"]),
        "terms": len([c for c in chunks if c["source_type"] == "term"]),
        "works": len([c for c in chunks if c["source_type"] == "work"]),
        "eras": len([c for c in chunks if c["source_type"] == "era"]),
        "styles": len([c for c in chunks if c["source_type"] == "style"]),
    }
    
    print("\n" + "=" * 60)
    print("数据导入完成！")
    print("=" * 60)
    print(f"  总片段数: {summary['total_chunks']}")
    print(f"  书法家片段: {summary['calligraphers']}")
    print(f"  术语片段: {summary['terms']}")
    print(f"  作品片段: {summary['works']}")
    print(f"  朝代片段: {summary['eras']}")
    print(f"  书体片段: {summary['styles']}")
    
    return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Qdrant with knowledge chunks")
    parser.add_argument(
        "--memory",
        action="store_true",
        default=True,
        help="Use in-memory mode (default: True)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Qdrant server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6333,
        help="Qdrant server port",
    )
    
    args = parser.parse_args()
    seed_qdrant(use_memory=args.memory, host=args.host, port=args.port)
