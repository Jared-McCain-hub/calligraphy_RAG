# 中国书法跨语言问答系统（Calligraphy RAG）

面向中国书法知识场景的 RAG 后端项目，提供问答、检索、知识图谱子图查询、语料导入与索引重建能力。项目当前以 `FastAPI + MySQL` 为主线落地，方便本地联调与后续扩展到 `Qdrant / Neo4j / Redis`。

## 项目特性

- 跨语言问答接口（支持多轮会话）
- 综合搜索（术语、人物、作品等）
- 图谱子图查询接口
- 语料导入、切片、向量化与重建索引流程
- Docker 一键启动（含数据库初始化与示例知识导入）

## 技术栈

- API：`FastAPI`
- 数据库：`MySQL 8`
- ORM：`SQLAlchemy`
- 服务运行：`Uvicorn`
- 可扩展组件（架构预留）：`Qdrant`、`Neo4j`、`Redis`

## 目录结构

```text
.
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ models/
│  │  ├─ repositories/
│  │  ├─ schemas/
│  │  └─ services/
│  ├─ alembic/
│  ├─ data/
│  ├─ scripts/
│  ├─ requirements.txt
│  └─ README.md
├─ docs/
│  ├─ ARCHITECTURE.md
│  └─ FRONTEND_HANDOFF.md
├─ docker-compose.yml
└─ .dockerignore
```

## 快速开始

### 方式一：Docker（推荐）

> 适合快速联调，默认会启动 `mysql + backend`。

在仓库根目录执行：

```bash
docker compose up --build
```

启动成功后访问：

- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`

默认端口：

- Backend：`8000`
- MySQL（宿主机）：`3307`（容器内仍是 `3306`）

### 方式二：本地 Python 运行

1) 进入后端目录并安装依赖

```bash
cd backend
pip install -r requirements.txt
```

2) 配置环境变量

```bash
cp .env.example .env
```

编辑 `backend/.env`，至少补全：

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

3) 初始化数据库（可选带演示数据）

```bash
python scripts/bootstrap_mysql.py --with-seed
alembic upgrade head
```

如需导入参考数据并生成初始 RAG 语料：

```bash
python scripts/bootstrap_mysql.py --with-reference-data --with-rag-knowledge
```

4) 启动服务

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 主要接口

基础前缀：`/api/v1`

- `GET /health`：健康检查
- `POST /chat/query`：发起问答（支持连续对话）
- `GET /chat/sessions/{session_id}`：获取会话历史
- `POST /search`：综合搜索（术语/人物/作品/知识片段）
- `GET /graph/subgraph`：查询知识图谱子图
- `GET /works/{work_id}`：作品详情
- `GET /calligraphers/{calligrapher_id}`：书法家详情
- `POST /admin/ingest`：创建语料导入任务
- `POST /admin/reindex`：创建索引重建任务

## 示例请求

### 1) 问答

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your_api_key>" \
  -d "{\"question\":\"什么是颜体？\",\"language\":\"zh-CN\"}"
```

### 2) 综合搜索

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -H "x-api-key: <your_api_key>" \
  -d "{\"query\":\"颜体\",\"entity_types\":[\"term\",\"knowledge_chunk\"],\"limit\":5}"
```

## 环境变量说明（核心）

参考文件：`backend/.env.example`

- 应用：`APP_NAME`、`APP_VERSION`、`API_PREFIX`、`APP_DEBUG`
- 数据库：`DB_DRIVER`、`DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`
- RAG：`RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP`、`RETRIEVAL_TOP_K`
- Embedding：`EMBEDDING_PROVIDER`、`EMBEDDING_MODEL`、`EMBEDDING_DIMENSIONS`
- Qwen：`QWEN_API_BASE`、`QWEN_API_KEY`、`QWEN_MODEL`
- 安全：`API_AUTH_ENABLED`、`API_AUTH_HEADER_NAME`、`API_AUTH_KEY`
- 限流：`RATE_LIMIT_ENABLED`、`RATE_LIMIT_REQUESTS`、`RATE_LIMIT_WINDOW_SECONDS`

## 安全默认策略

- API Key 鉴权：默认开启，除 `/docs`、`/openapi.json`、`/redoc`、`/api/v1/health` 外都需要 `x-api-key`
- IP 限流：默认 `60` 次 / `60` 秒（按 IP + 路径）
- 慢请求告警：请求耗时超过 `SECURITY_ALERT_SLOW_REQUEST_MS` 会输出告警日志
- 关键审计日志：`/api/v1/chat/query`、`/api/v1/admin/ingest`、`/api/v1/admin/reindex` 会输出请求审计日志

## 开发建议

- 先用 Docker 跑通全链路，再按需切到本地 Python 调试。
- 提交前建议至少验证：`/api/v1/health`、`/api/v1/chat/query`、`/api/v1/search`。
- 详细架构与模块边界见 `docs/ARCHITECTURE.md`。
- 前端联调说明见 `docs/FRONTEND_HANDOFF.md`。

## Roadmap（建议）

- 接入真实向量库（Qdrant）与图数据库（Neo4j）生产化链路
- 增加鉴权、限流、审计日志与可观测性
- 完善测试（单元测试 / 集成测试）与 CI 流程
- 增强语料治理（质量评估、重复检测、版本化）

## License

当前仓库未声明开源许可证。若计划公开到 GitHub，建议补充 `LICENSE`（例如 MIT / Apache-2.0）。
