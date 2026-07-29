from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Calligraphy RAG Backend")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    
    # Database
    db_driver: str = os.getenv("DB_DRIVER", "pymysql")
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "calligraphy_rag")
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_charset: str = os.getenv("DB_CHARSET", "utf8mb4")
    db_collation: str = os.getenv("DB_COLLATION", "utf8mb4_unicode_ci")
    db_echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"
    db_pool_pre_ping: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    
    # RAG
    rag_chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "260"))
    rag_chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "60"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    
    # Embedding
    embedding_dimensions: int = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    
    # Qdrant
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_use_memory: bool = os.getenv("QDRANT_USE_MEMORY", "true").lower() == "true"
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    
    # Qwen
    qwen_api_base: str = os.getenv("QWEN_API_BASE", "")
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen-plus")
    qwen_temperature: float = float(os.getenv("QWEN_TEMPERATURE", "0.2"))
    qwen_timeout_seconds: int = int(os.getenv("QWEN_TIMEOUT_SECONDS", "20"))
    
    # Security
    api_auth_enabled: bool = os.getenv("API_AUTH_ENABLED", "false").lower() == "true"
    api_auth_header_name: str = os.getenv("API_AUTH_HEADER_NAME", "x-api-key")
    api_auth_key: str = os.getenv("API_AUTH_KEY", "")
    api_auth_exempt_paths: tuple[str, ...] = tuple(
        path.strip()
        for path in os.getenv("API_AUTH_EXEMPT_PATHS", "/docs,/openapi.json,/redoc,/api/v1/health").split(",")
        if path.strip()
    )
    rate_limit_enabled: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    rate_limit_exempt_paths: tuple[str, ...] = tuple(
        path.strip()
        for path in os.getenv("RATE_LIMIT_EXEMPT_PATHS", "/docs,/openapi.json,/redoc,/api/v1/health").split(",")
        if path.strip()
    )
    security_alert_slow_request_ms: int = int(os.getenv("SECURITY_ALERT_SLOW_REQUEST_MS", "2000"))

    @property
    def database_url(self) -> str:
        password = quote_plus(self.db_password)
        return (
            f"mysql+{self.db_driver}://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset={self.db_charset}"
        )

    @property
    def server_database_url(self) -> str:
        password = quote_plus(self.db_password)
        return (
            f"mysql+{self.db_driver}://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/?charset={self.db_charset}"
        )


settings = Settings()
