# 中国书法跨语言问答系统（Calligraphy RAG）

面向中国书法知识场景的 RAG 后端项目，提供基于向量检索的问答、知识图谱子图查询、综合搜索与语料治理能力。项目以 `FastAPI + MySQL + Qdrant` 为主链路落地，支持多轮对话与 Embedding 微调。

---

## 项目特性

- **双路检索 RAG**：支持基于 Qdrant 向量检索 + Qwen LLM 生成的问答链路
- **多轮会话**：连续对话上下文保留，支持追问与澄清
- **综合搜索**：术语、书法家、作品、知识片段混合检索
- **知识图谱子图查询**：Neo4j 架构预留，可扩展实体关系探索
- **语料导入与向量化**：JSON 数据自动切片、Embedding、入库
- **Embedding 微调**：基于领域语料自动生成训练数据，支持 Mac MPS 本地微调
- **Docker 一键启动**：含 MySQL 初始化、Qdrant 向量库、示例知识导入

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| API 框架 | FastAPI | 异步高性能，自动生成 OpenAPI 文档 |
| 关系数据库 | MySQL 8 | 结构化数据存储（书法家、作品、术语等） |
| ORM | SQLAlchemy + Alembic | 数据建模与迁移 |
| 向量数据库 | **Qdrant（内存模式）** | 384 维向量检索，Cosine 距离 |
| 嵌入模型 | paraphrase-multilingual-MiniLM-L12-v2 | 384 维，多语言支持 |
| 大语言模型 | Qwen3.7-max（阿里云百炼） | 生成回复 + reasoning |
| 图数据库 | Neo4j（架构预留） | 知识图谱扩展 |
| 缓存 | Redis（架构预留） | 高频查询缓存 |
| 部署 | Docker + Uvicorn | 容器化一键启动 |

---

## 数据规模

| 类别 | 数量 | 来源 |
|------|------|------|
| 书法家 | 19 位 | 王羲之、颜真卿、柳公权、苏轼等 |
| 书法术语 | 39 个 | 永字八法、中锋、屋漏痕等 |
| 代表作品 | 37 件 | 兰亭序、祭侄文稿、寒食帖等 |
| 历史朝代 | 7 个 | 晋、唐、宋、元、明、清、南北朝 |
| 书体类型 | 8 种 | 行书、草书、楷书、隶书、篆书等 |
| **知识库总计** | **129 条** | 结构化 JSON 数据 |
| 微调训练数据 | 380 条 | 从知识库自动生成（问答对 + 正/负样本） |

---

## 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST API 路由
│   │   │   ├── chat.py         # 多轮问答（MySQL 检索）
│   │   │   ├── qdrant_chat.py  # 向量检索问答（Qdrant）
│   │   │   ├── search.py       # 综合搜索
│   │   │   ├── graph.py        # 知识图谱子图查询
│   │   │   ├── admin_ingest.py # 语料导入
│   │   │   └── ...
│   │   ├── core/             # 配置、数据库连接、安全
│   │   ├── models/           # SQLAlchemy 实体模型
│   │   ├── repositories/     # 数据访问层
│   │   │   ├── qdrant_repository.py      # Qdrant 向量库封装
│   │   │   ├── knowledge_repository.py   # MySQL 知识库
│   │   │   └── ...
│   │   ├── schemas/          # Pydantic 数据校验
│   │   └── services/         # 业务逻辑层
│   │       ├── embedding_service.py         # 文本向量化
│   │       ├── qdrant_retriever_service.py  # 向量检索
│   │       ├── qdrant_rag_service.py        # Qdrant RAG 完整链路
│   │       └── qwen_service.py              # LLM 调用封装
│   ├── data/                 # 结构化 JSON 数据
│   │   ├── calligraphers.json
│   │   ├── terms.json
│   │   ├── works.json
│   │   ├── eras.json
│   │   └── styles.json
│   ├── scripts/              # 运维与数据脚本
│   │   ├── seed_qdrant.py           # 数据导入 Qdrant
│   │   ├── generate_training_data.py # 自动生成微调数据
│   │   ├── finetune_embedding_mps.py # Mac MPS 微调脚本
│   │   ├── run_finetune_mac.sh      # 微调一键运行
│   │   └── ...
│   ├── training_data/        # 自动生成的微调数据
│   ├── tests/                # 测试脚本
│   │   ├── test_qdrant.py
│   │   ├── test_qdrant_offline.py
│   │   └── test_full_rag.py
│   └── requirements.txt
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FRONTEND_HANDOFF.md
│   └── CALLIGRAPHY_CORPUS_CATALOG.md
├── docker-compose.yml
├── .env.qdrant              # Qdrant / Qwen API 配置模板
└── README_QDRANT.md         # Qdrant 模块详细文档
```

---

## 快速开始

### 方式一：Docker（推荐）

适合快速联调，默认启动 `MySQL + Backend + Qdrant`。

```bash
docker compose up --build
```

启动后访问：

- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`

默认端口：

- Backend：`8000`
- MySQL（宿主机）：`3307`

### 方式二：本地 Python 运行

```bash
cd backend
pip install -r requirements.txt
```

配置环境变量（Qdrant + Qwen 模式）：

```bash
cp .env.qdrant .env
# 编辑 .env，填入 QWEN_API_KEY
```

初始化数据库并导入 Qdrant：

```bash
# 1. MySQL 初始化
python scripts/bootstrap_mysql.py --with-seed

# 2. 导入书法知识到 Qdrant 向量库
python scripts/seed_qdrant.py
```

启动服务：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 主要接口

基础前缀：`/api/v1`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/chat/query` | MySQL 检索问答 |
| POST | `/chat/qdrant` | **Qdrant 向量检索问答** |
| POST | `/search` | 综合搜索 |
| GET | `/graph/subgraph` | 知识图谱子图 |
| GET | `/works/{id}` | 作品详情 |
| GET | `/calligraphers/{id}` | 书法家详情 |
| POST | `/admin/ingest` | 语料导入 |
| POST | `/admin/reindex` | 索引重建 |

### 示例：Qdrant 向量问答

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat/qdrant" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your_api_key>" \
  -d '{"question": "什么是颜体？", "language": "zh-CN", "top_k": 5}'
```

---

## Embedding 微调

项目支持基于书法语料自动生成训练数据并进行 Embedding 微调。

### 1. 生成训练数据

```bash
cd backend
python scripts/generate_training_data.py
```

输出到 `backend/training_data/`：
- `training_data.txt` — 问答对文本
- `embedding_training_data.json` — 正/负样本三元组
- `hf_format_data.json` — HuggingFace 格式

### 2. 执行微调（MacBook Air MPS 加速）

```bash
chmod +x scripts/run_finetune_mac.sh
./scripts/run_finetune_mac.sh
```

或直接用 Python：

```bash
python scripts/finetune_embedding_mps.py \
  --train_data training_data/hf_format_data.json \
  --output_dir models/finetuned_embedding \
  --epochs 5 --batch_size 16
```

---

## 环境变量说明

参考文件：`backend/.env.qdrant`

| 类别 | 变量 | 说明 |
|------|------|------|
| 数据库 | `DB_HOST`, `DB_PORT`, `DB_NAME` | MySQL 连接 |
| 向量库 | `QDRANT_HOST`, `QDRANT_PORT` | Qdrant 连接（默认 localhost:6333） |
| RAG | `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP` | 文本切片参数 |
| Embedding | `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS` | 默认 384 维 |
| LLM | `QWEN_API_KEY`, `QWEN_API_BASE`, `QWEN_MODEL` | 阿里云百炼 API |
| 安全 | `API_AUTH_ENABLED`, `API_AUTH_KEY` | API Key 鉴权 |
| 限流 | `RATE_LIMIT_ENABLED` | IP 限流开关 |

---

## 版本与演进

| 版本 | 说明 | 对应 Tag |
|------|------|---------|
| **v1.0** | 基础架构：FastAPI + MySQL + SQLAlchemy，预留 Qdrant/Neo4j 扩展 | `v1.0` |
| **v2.0** | 完整 RAG：Qdrant 向量检索、Embedding 服务、Qwen LLM 生成、数据扩展至 129 条、Embedding 微调支持 | `v2.0` |

---

## 系统架构

```
┌─────────────────┐
│   用户请求      │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│  FastAPI 路由   │────▶│  MySQL 结构化检索 │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Embedding 服务  │────▶│  Qdrant 向量检索 │
│ (384 维 MiniLM) │     │ (Cosine, Top-K) │
└─────────────────┘     └─────────────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
           ┌─────────────────┐
           │  Qwen LLM 生成  │
           │ (qwen3.7-max)   │
           └─────────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │   多轮对话返回   │
           └─────────────────┘
```

---

## Roadmap

- [x] Qdrant 向量检索与 RAG 完整链路
- [x] Embedding 微调数据生成与训练脚本
- [ ] Neo4j 知识图谱实体关系扩展
- [ ] Redis 高频查询缓存
- [ ] 完善单元测试 / 集成测试与 CI 流程
- [ ] 语料质量评估与版本化治理

---

## License

当前仓库未声明开源许可证。若计划公开到 GitHub，建议补充 `LICENSE`（例如 MIT / Apache-2.0）。
