"""Test full RAG pipeline: Qdrant retrieval + Qwen generation."""

import os
import sys
from pathlib import Path

# Force offline mode for embeddings
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Load environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env.qdrant")

# Add backend to path
BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import json
from uuid import uuid4

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class RAGSystem:
    """Simple RAG system for testing."""
    
    def __init__(self):
        """Initialize RAG system."""
        print("初始化 RAG 系统...")
        
        # 1. Load embedding model
        print("  加载向量模型...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # 2. Initialize Qdrant
        print("  初始化 Qdrant...")
        self.client = QdrantClient(":memory:")
        self.collection_name = "calligraphy_rag"
        
        # 3. Load and index data
        print("  加载知识数据...")
        self._load_and_index_data()
        
        # 4. Qwen config
        self.qwen_api_key = os.getenv("QWEN_API_KEY")
        self.qwen_api_base = os.getenv("QWEN_API_BASE")
        self.qwen_model = os.getenv("QWEN_MODEL", "qwen3.7-max")
        
        print("✅ RAG 系统初始化完成\n")
    
    def _load_and_index_data(self):
        """Load data and create vector index."""
        chunks, texts = self._build_knowledge_chunks()
        
        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.model.get_sentence_embedding_dimension(),
                distance=Distance.COSINE,
            ),
        )
        
        # Generate embeddings
        vectors = self.model.encode(texts, show_progress_bar=False)
        
        # Upsert to Qdrant
        points = [
            PointStruct(
                id=chunk["id"],
                vector=vector.tolist(),
                payload={
                    "text": chunk["text"],
                    "document_title": chunk["document_title"],
                    "source_type": chunk["source_type"],
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        
        print(f"  已索引 {len(points)} 个知识片段")
    
    def _build_knowledge_chunks(self):
        """Build knowledge chunks from JSON data."""
        chunks = []
        texts = []
        
        # Load calligraphers
        calligraphers_path = BACKEND_ROOT / "data" / "calligraphers.json"
        if calligraphers_path.exists():
            with open(calligraphers_path, encoding="utf-8") as f:
                calligraphers = json.load(f)
            for c in calligraphers:
                text = f"{c['name_cn']}（{c.get('name_en', '')}），{c.get('era', '')}书法家。"
                if c.get('biography'):
                    text += f" {c['biography']}"
                
                chunks.append({
                    "id": str(uuid4()),
                    "text": text,
                    "document_title": f"{c['name_cn']}简介",
                    "source_type": "calligrapher",
                })
                texts.append(text)
        
        # Load terms
        terms_path = BACKEND_ROOT / "data" / "terms.json"
        if terms_path.exists():
            with open(terms_path, encoding="utf-8") as f:
                terms = json.load(f)
            for t in terms:
                text = f"{t['name_cn']}（{t.get('name_en', '')}）：{t.get('definition', '')}"
                if t.get('usage_notes'):
                    text += f" {t['usage_notes']}"
                
                chunks.append({
                    "id": str(uuid4()),
                    "text": text,
                    "document_title": f"{t['name_cn']}术语解释",
                    "source_type": "term",
                })
                texts.append(text)
        
        # Load works
        works_path = BACKEND_ROOT / "data" / "works.json"
        if works_path.exists():
            with open(works_path, encoding="utf-8") as f:
                works = json.load(f)
            for w in works:
                text = f"《{w['title_cn']}》"
                if w.get('title_en'):
                    text += f"（{w['title_en']}）"
                text += f"，{w.get('calligrapher', '')}{w.get('era', '')}作品，{w.get('style', '')}。"
                if w.get('description'):
                    text += f" {w['description']}"
                
                chunks.append({
                    "id": str(uuid4()),
                    "text": text,
                    "document_title": w["title_cn"],
                    "source_type": "work",
                })
                texts.append(text)
        
        return chunks, texts
    
    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve relevant chunks."""
        query_vector = self.model.encode(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
        )
        return results
    
    def generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Qwen API."""
        import urllib.request
        import urllib.error
        
        if not self.qwen_api_key:
            return "❌ Qwen API 未配置，请设置 QWEN_API_KEY"
        
        system_prompt = """你是一个专业的中国书法知识助手。你的任务是基于提供的知识片段回答用户问题。

要求：
1. 只使用提供的知识片段中的信息回答
2. 如果知识片段中没有相关信息，如实告知用户
3. 回答要简洁准确，避免冗余
4. 保持客观中立的语气"""

        user_prompt = f"""请基于以下知识片段回答问题：

{context}

问题：{question}

请给出简洁准确的回答。"""
        
        url = self.qwen_api_base.rstrip("/") + "/chat/completions"
        
        payload = json.dumps({
            "model": self.qwen_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        }).encode("utf-8")
        
        headers = {
            "Authorization": f"Bearer {self.qwen_api_key}",
            "Content-Type": "application/json",
        }
        
        req = urllib.request.Request(url=url, data=payload, headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return f"❌ Qwen API 调用失败: {e}"
    
    def chat(self, question: str, top_k: int = 3):
        """Full RAG chat: retrieve + generate."""
        print(f"\n{'=' * 60}")
        print(f"问题: {question}")
        print(f"{'=' * 60}")
        
        # 1. Retrieve
        print(f"\n[1/2] 检索知识片段 (Top-{top_k})...")
        results = self.retrieve(question, top_k=top_k)
        
        # Build context
        context_parts = []
        citations = []
        for i, result in enumerate(results, 1):
            text = result.payload["text"]
            title = result.payload["document_title"]
            score = result.score
            
            print(f"  [{i}] 相似度: {score:.4f} | 来源: {title}")
            print(f"      文本: {text[:60]}...")
            
            context_parts.append(f"[{i}] {text}")
            citations.append({"title": title, "score": score})
        
        context = "\n\n".join(context_parts)
        
        # 2. Generate
        print(f"\n[2/2] 生成回答...")
        answer = self.generate_answer(question, context)
        
        print(f"\n{'=' * 60}")
        print("回答:")
        print(f"{'=' * 60}")
        print(answer)
        
        print(f"\n引用来源:")
        for i, citation in enumerate(citations, 1):
            print(f"  [{i}] {citation['title']} (相似度: {citation['score']:.4f})")
        
        return {
            "question": question,
            "answer": answer,
            "citations": citations,
        }


def main():
    """Test full RAG pipeline."""
    print("\n" + "=" * 60)
    print("测试完整 RAG 流程：向量检索 + Qwen 生成")
    print("=" * 60)
    
    # Initialize RAG system
    rag = RAGSystem()
    
    # Test questions
    test_questions = [
        "什么是颜体？",
        "颜真卿有哪些代表作？",
        "王羲之是谁？",
    ]
    
    for question in test_questions:
        rag.chat(question)
        print("\n" + "-" * 60)
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()
