# 前端联调说明

## 适用场景

本文档用于把当前后端 Docker 联调版交给前端同学使用。前端同学不需要单独安装 Python 或 MySQL，只需在自己的电脑上启动 Docker 环境即可。

## 需要的软件

- Docker Desktop
- 一个终端工具：PowerShell / Windows Terminal / CMD
- 浏览器

## 启动后端

在项目根目录执行：

```bash
docker compose up --build
```

启动成功后：

- 后端地址：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`

## AI 聊天窗口对接

前端聊天窗口主要调用以下接口：

```text
POST http://127.0.0.1:8000/api/v1/chat/query
```

### 首次提问

请求体示例：

```json
{
  "question": "什么是颜体？",
  "language": "zh-CN"
}
```

后端会返回：

- `answer`
- `citations`
- `session_id`
- `messages`

### 连续对话

前端需要保存第一次返回的 `session_id`。后续追问时继续带上该字段：

```json
{
  "session_id": "上一次返回的session_id",
  "question": "那它和欧体有什么区别？",
  "language": "zh-CN"
}
```

## 会话历史回读

如果前端需要恢复聊天记录，可调用：

```text
GET http://127.0.0.1:8000/api/v1/chat/sessions/{session_id}
```

示例：

```text
http://127.0.0.1:8000/api/v1/chat/sessions/45300fc2-8be6-46d6-afe6-e1ce977c4d9a
```

## 搜索接口

如果前端还需要做知识检索，可调用：

```text
POST http://127.0.0.1:8000/api/v1/search
```

请求体示例：

```json
{
  "query": "颜体",
  "entity_types": ["term", "knowledge_chunk"],
  "limit": 5
}
```

## 常见联调流程

1. 启动 Docker Desktop。
2. 在项目根目录执行 `docker compose up --build`。
3. 打开 `http://127.0.0.1:8000/docs` 检查接口是否正常。
4. 前端调用 `/api/v1/chat/query` 发起首次消息。
5. 保存返回的 `session_id`，后续连续对话继续带上。
6. 如需恢复历史记录，调用 `/api/v1/chat/sessions/{session_id}`。

## 注意事项

- 前端调用默认基于本机地址 `http://127.0.0.1:8000`。
- 如果前端页面和后端端口不同，浏览器可能出现跨域问题；如有需要，可在后端补充 CORS 配置。
- Docker 首次启动会较慢，因为需要拉镜像、构建后端镜像、初始化数据库并导入知识数据。
- 如果本机 `3306` 已被占用，需要在 `docker-compose.yml` 中调整 MySQL 的宿主机映射端口。
