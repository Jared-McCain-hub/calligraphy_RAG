# Backend 目录约定

该目录用于承载中国书法跨语言问答系统的后端实现。

## 目标分层

```text
backend/
  app/
    api/
      v1/
        chat.py
        search.py
        graph.py
        works.py
        admin_ingest.py
    core/
      config.py
      database.py
      logging.py
    schemas/
    services/
      chat_service.py
      search_service.py
      graph_service.py
      ingest_service.py
      retriever_service.py
      term_guard_service.py
    repositories/
    models/
    tasks/
    main.py
  scripts/
  tests/
```

## 模块职责

- `app/api/v1/`：HTTP 接口层，只做参数接收、依赖注入和响应返回
- `app/services/`：业务编排层，负责跨存储协同
- `app/repositories/`：单一存储访问层，分别面向 MySQL、Qdrant、Neo4j、Redis
- `app/models/`：数据库模型或领域实体
- `app/schemas/`：Pydantic 请求与响应模型
- `app/core/`：配置、连接初始化、日志、错误处理
- `app/tasks/`：导入、重建索引等后台任务

## 服务边界速记

- `FastAPI`：对外 API 与应用编排入口
- `MySQL`：主业务数据、会话持久化、导入任务
- `Qdrant`：语义检索向量
- `Neo4j`：知识图谱关系查询
- `Redis`：短期上下文、缓存、锁、临时状态

详细设计见 `docs/ARCHITECTURE.md`。

## MySQL 落地

后端已补齐 MySQL 的基础建库链路：

- `app/core/config.py`：读取 MySQL 连接配置
- `app/core/database.py`：提供 engine、session、建库和建表函数
- `alembic/`：维护数据库迁移
- `scripts/bootstrap_mysql.py`：本地初始化数据库与表
- `scripts/seed_demo_data.py`：写入示例人物、作品与术语数据

建议命令：

```bash
python scripts/bootstrap_mysql.py --with-seed
alembic upgrade head
```

如果要把 `backend/data/` 下整理好的参考知识数据导入数据库，可使用：

```bash
python scripts/bootstrap_mysql.py --with-reference-data
```

如果希望在建库建表后同时导入 demo 数据和参考知识数据，可使用：

```bash
python scripts/bootstrap_mysql.py --with-seed --with-reference-data
```

如果希望把 `terms / calligraphers / works` 自动转换成首批 RAG 语料，可使用：

```bash
python scripts/seed_rag_knowledge.py
```

也可以在建库后一步完成参考数据导入和初始 RAG 语料生成：

```bash
python scripts/bootstrap_mysql.py --with-reference-data --with-rag-knowledge
```

运行前先参考 `backend/.env.example` 配置数据库连接。

## 本地启动

推荐直接在 `backend/` 目录启动：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Windows 中文终端

MySQL 的 `utf8mb4` 只负责数据库存储编码，不负责 Windows 控制台显示编码。若你在本机终端里看到中文日志乱码，请先把终端切到 UTF-8，再启动 Python 或 `uvicorn`。

`cmd` 推荐命令：

```bat
chcp 65001
set PYTHONUTF8=1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

PowerShell 推荐命令：

```powershell
$env:PYTHONUTF8 = "1"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

如果仍想显式指定标准输出编码，也可以改用：

```powershell
$env:PYTHONIOENCODING = "utf-8"
python scripts/bootstrap_mysql.py --with-reference-data --with-rag-knowledge
```

更省心的做法是优先使用 Windows Terminal 或较新的 PowerShell 终端运行这些命令。

## Docker 联调

仓库根目录已提供最小可交付的容器化方案：

- `backend/Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

默认会启动：

- `mysql`：本地联调用 MySQL
- `backend`：启动时自动建库、建表、导入参考数据并生成初始 RAG 语料

在项目根目录执行：

```bash
docker compose up --build
```

启动成功后：

- 后端地址：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`
- MySQL 地址：`127.0.0.1:3306`

如果要覆盖默认数据库密码或注入 Qwen 配置，可在执行 `docker compose up` 前设置环境变量：

```bash
DB_PASSWORD=YOUR_DB_PASSWORD
QWEN_API_KEY=your_key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```

Docker 方案默认面向本地开发与前后端联调，不会把你当前本地的 `backend/.env` 打进镜像。
