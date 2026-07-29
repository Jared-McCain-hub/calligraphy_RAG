# 中国书法跨语言问答后端架构

## 1. 目标

本架构用于支撑以下 MVP 能力：

- 跨语言智能问答
- 多轮对话
- 作品与知识检索
- 知识图谱子图查询
- 语料导入与索引重建

技术基线固定为：

- API 与编排层：`FastAPI`
- 结构化主存储：`MySQL`
- 向量检索：`Qdrant`
- 关系图查询：`Neo4j`
- 缓存与会话加速：`Redis`

## 2. 总体架构

```mermaid
flowchart LR
client[Frontend / Admin] --> api[FastAPI API Layer]
api --> chat[Chat Service]
api --> search[Search Service]
api --> graph[Graph Service]
api --> ingest[Ingest Service]

chat --> mysql[(MySQL)]
chat --> qdrant[(Qdrant)]
chat --> redis[(Redis)]
search --> mysql
search --> qdrant
graph --> neo4j[(Neo4j)]
ingest --> mysql
ingest --> qdrant
ingest --> neo4j
```

## 3. 服务边界

### 3.1 FastAPI

`FastAPI` 只承担四类职责：

- 对外暴露 HTTP API
- 请求校验、鉴权、限流、异常映射
- 组装应用服务并协调调用顺序
- 返回统一响应结构

`FastAPI` 不直接承载以下业务：

- 不在路由层拼接复杂检索逻辑
- 不在路由层直接写 Cypher 或向量检索语句
- 不在路由层维护会话窗口与术语规范化

### 3.2 MySQL

`MySQL` 是业务主数据的权威来源，负责：

- 书法家、作品、术语、朝代、风格等结构化实体
- 语料文档元数据与导入任务记录
- 聊天会话与消息持久化
- 检索前置过滤需要的结构化字段

`MySQL` 不负责：

- 存储高维向量
- 承载图谱遍历查询
- 作为短期上下文缓存

### 3.3 Qdrant

`Qdrant` 仅负责语义召回，存储：

- `knowledge_chunk` 对应的向量
- 与召回有关的最小元数据，例如 `chunk_id`、`doc_id`、`lang`、`source_type`

`Qdrant` 不负责：

- 保存完整业务实体主数据
- 保存对话消息
- 承担图关系分析

### 3.4 Neo4j

`Neo4j` 仅负责知识关系查询与子图返回，存储：

- `Calligrapher`
- `Work`
- `Style`
- `Era`
- `Term`
- 节点之间的业务关系

`Neo4j` 不负责：

- 作为主数据唯一来源
- 作为全文或向量检索引擎
- 保存聊天上下文

### 3.5 Redis

`Redis` 负责易失性和高频访问数据：

- 最近多轮对话窗口
- 热门查询缓存
- 幂等键、短时任务状态、分布式锁

`Redis` 不负责：

- 作为长期消息归档库
- 保存需要强一致的业务实体

## 4. 应用服务拆分

后端采用单体应用、分层模块的实现方式。`FastAPI` 进程内包含多个服务模块，而不是一开始拆成多个独立微服务。

### 4.1 Chat Service

职责：

- 接收问题与会话上下文
- 进行查询改写、术语规范化、检索编排
- 聚合 `MySQL`、`Qdrant`、`Redis` 数据
- 生成问答结果、引用与推荐项

依赖边界：

- 从 `Redis` 读取最近上下文
- 从 `Qdrant` 召回片段
- 从 `MySQL` 补全实体与引用信息
- 不直接访问 `Neo4j`，除非推荐能力明确依赖图关系

### 4.2 Search Service

职责：

- 统一处理术语、书法家、作品、时代、风格检索
- 优先执行结构化过滤
- 必要时结合向量召回做结果补充

依赖边界：

- 主依赖 `MySQL`
- 可选依赖 `Qdrant`
- 不负责对话状态管理

### 4.3 Graph Service

职责：

- 根据关键词、实体 ID 或类型返回标准子图 JSON
- 屏蔽前端对 `Neo4j` 的直接访问

依赖边界：

- 主依赖 `Neo4j`
- 需要补充展示字段时可回查 `MySQL`
- 不负责问答生成

### 4.4 Ingest Service

职责：

- 上传资料后的解析、清洗、切片、向量化、入库、建图
- 管理重建索引和导入任务状态

依赖边界：

- 文档元数据写入 `MySQL`
- 向量写入 `Qdrant`
- 图关系写入 `Neo4j`
- 任务状态和去重锁可借助 `Redis`

## 5. 分层约定

建议目录结构如下：

```text
backend/
  app/
    api/
      v1/
    core/
    schemas/
    services/
    repositories/
    models/
    tasks/
    main.py
  scripts/
  tests/
```

各层职责如下：

- `api/`：路由与依赖注入，不写核心业务逻辑
- `schemas/`：请求响应模型
- `services/`：业务编排层，负责跨仓储组合
- `repositories/`：针对单一存储的访问封装
- `models/`：ORM 模型或领域实体
- `core/`：配置、日志、异常、基础设施初始化
- `tasks/`：异步导入、重建索引等后台任务

## 6. 仓储边界

为了避免存储职责混乱，所有外部依赖都通过仓储或网关封装：

- `MySQL repositories`：实体查询、会话持久化、导入任务记录
- `Qdrant repository`：向量 upsert、检索、删除、重建 collection
- `Neo4j repository`：节点关系写入、子图查询
- `Redis repository`：上下文缓存、热点缓存、锁、短期状态

约束如下：

- `service` 可以组合多个 `repository`
- `repository` 只能面向单一存储
- 路由层不能越过 `service` 直接调用多个存储

## 7. 关键请求流

### 7.1 问答

1. `API` 接收问题、语言和可选会话 ID
2. `Chat Service` 从 `Redis` 获取最近上下文
3. `Chat Service` 生成检索查询
4. `Qdrant` 返回相关语料片段
5. `MySQL` 返回片段关联实体、术语标准名、来源信息
6. `Chat Service` 组装答案、引用和推荐项
7. 会话结果写入 `MySQL`，短期窗口更新到 `Redis`

### 7.2 综合搜索

1. `API` 接收关键词和筛选条件
2. `Search Service` 优先查 `MySQL`
3. 必要时追加 `Qdrant` 语义补召回
4. 聚合为统一结果结构返回

### 7.3 图谱子图

1. `API` 接收关键词或实体 ID
2. `Graph Service` 查询 `Neo4j`
3. 必要时回查 `MySQL` 补全展示字段
4. 返回标准 `nodes + edges` JSON

### 7.4 语料导入

1. 上传文件后创建导入任务
2. 原文与元数据登记到 `MySQL`
3. 切片并写入 `Qdrant`
4. 实体和关系写入 `Neo4j`
5. 任务状态更新到 `MySQL`，过程状态可同步写入 `Redis`

## 8. 数据所有权

| 数据类型 | 权威存储 | 用途 |
| --- | --- | --- |
| 书法家/作品/术语/时代/风格 | MySQL | 结构化业务数据 |
| 语料向量 | Qdrant | 语义召回 |
| 图谱节点关系 | Neo4j | 子图与关系探索 |
| 会话长期历史 | MySQL | 会话回溯 |
| 会话短期窗口/热点缓存/锁 | Redis | 性能与状态协调 |

## 9. MVP 落地原则

- 先做单体分层，不急着拆微服务
- 所有答案必须返回引用来源
- 向量、图谱、结构化数据各自只做自己最擅长的事情
- 前端永远只调用后端 API，不直接访问 `Qdrant`、`Neo4j`、`Redis`
- 后续若接入异步任务框架，优先把导入和重建索引迁出主请求链路

## 10. 后续实现优先级

建议按以下顺序继续落地：

1. `backend/app/main.py` 与基础配置
2. `schemas/`、`repositories/`、`services/` 骨架
3. `chat`、`search`、`graph` 三组 MVP 路由
4. `MySQL`、`Qdrant`、`Neo4j`、`Redis` 基础连接封装
5. `ingest` 与异步任务
