"""Test Qdrant implementation without database dependencies."""

import sys
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import json
from uuid import uuid4

# Import only the components we need
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)


def load_json_data(filename: str) -> list[dict]:
    """Load JSON data from data directory."""
    filepath = BACKEND_ROOT / "data" / filename
    if not filepath.exists():
        print(f"Warning: {filepath} not found")
        return []
    
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def build_knowledge_chunks() -> tuple[list[dict], list[str]]:
    """Build knowledge chunks from reference data."""
    chunks = []
    texts = []
    
    # 1. Load calligraphers
    calligraphers = load_json_data("calligraphers.json")
    for c in calligraphers:
        text = f"{c['name_cn']}（{c.get('name_en', '')}），{c.get('era', '')}书法家。"
        if c.get('biography'):
            text += f" {c['biography']}"
        if c.get('achievements'):
            text += f" {c['achievements']}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_title": f"{c['name_cn']}简介",
            "source_type": "calligrapher",
            "entity_name": c["name_cn"],
        })
        texts.append(text)
        
        if c.get('representative_works'):
            works_text = f"{c['name_cn']}的代表作包括：{', '.join(c['representative_works'])}。"
            chunks.append({
                "id": str(uuid4()),
                "text": works_text,
                "document_title": f"{c['name_cn']}代表作",
                "source_type": "calligrapher",
                "entity_name": c["name_cn"],
            })
            texts.append(works_text)
    
    # 2. Load terms
    terms = load_json_data("terms.json")
    for t in terms:
        text = f"{t['name_cn']}（{t.get('name_en', '')}）：{t.get('definition', '')}"
        if t.get('usage_notes'):
            text += f" {t['usage_notes']}"
        
        chunks.append({
            "id": str(uuid4()),
            "text": text,
            "document_title": f"{t['name_cn']}术语解释",
            "source_type": "term",
            "entity_name": t["name_cn"],
        })
        texts.append(text)
    
    # 3. Load works
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
            "document_title": w["title_cn"],
            "source_type": "work",
            "entity_name": w["title_cn"],
        })
        texts.append(text)
    
    return chunks, texts


def test_qdrant_retrieval():
    """Test Qdrant retrieval pipeline."""
    print("=" * 60)
    print("Testing Qdrant Vector Retrieval")
    print("=" * 60)
    
    # 1. Load data
    print("\n[1/5] Loading reference data...")
    chunks, texts = build_knowledge_chunks()
    print(f"  Loaded {len(chunks)} knowledge chunks")
    
    # 2. Initialize embedding model
    print("\n[2/5] Initializing embedding model...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print(f"  Model loaded (dimension: {model.get_sentence_embedding_dimension()})")
    
    # 3. Generate embeddings
    print("\n[3/5] Generating embeddings...")
    vectors = model.encode(texts, show_progress_bar=True)
    print(f"  Generated {len(vectors)} vectors")
    
    # 4. Initialize Qdrant
    print("\n[4/5] Initializing Qdrant...")
    client = QdrantClient(":memory:")
    
    collection_name = "calligraphy_test"
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=model.get_sentence_embedding_dimension(),
            distance=Distance.COSINE,
        ),
    )
    print(f"  Collection '{collection_name}' created")
    
    # 5. Upsert vectors
    print("\n[5/5] Upserting vectors...")
    points = [
        PointStruct(
            id=chunk["id"],
            vector=vector.tolist(),
            payload={
                "text": chunk["text"],
                "document_title": chunk["document_title"],
                "source_type": chunk["source_type"],
                "entity_name": chunk["entity_name"],
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]
    client.upsert(collection_name=collection_name, points=points)
    print(f"  Upserted {len(points)} points")
    
    # 6. Test retrieval
    print("\n" + "=" * 60)
    print("Testing Retrieval")
    print("=" * 60)
    
    test_queries = [
        "什么是颜体？",
        "颜真卿有哪些代表作？",
        "楷书是什么？",
        "兰亭集序是谁写的？",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        query_vector = model.encode(query)
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector.tolist(),
            limit=3,
        )
        
        print(f"  Top {len(results)} results:")
        for i, result in enumerate(results, 1):
            payload = result.payload
            print(f"  [{i}] Score: {result.score:.4f}")
            print(f"      文本: {payload['text'][:80]}...")
            print(f"      来源: {payload['document_title']}")
    
    print("\n" + "=" * 60)
    print("✅ Qdrant retrieval test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_qdrant_retrieval()
