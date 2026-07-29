from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from functools import lru_cache
from uuid import uuid4

from sqlalchemy import JSON, DateTime, MetaData, String, create_engine, func, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def generate_uuid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class MetadataMixin:
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_pre_ping=settings.db_pool_pre_ping,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def create_database_if_not_exists() -> None:
    bootstrap_engine = create_engine(
        settings.server_database_url,
        echo=settings.db_echo,
        pool_pre_ping=settings.db_pool_pre_ping,
    )
    create_stmt = text(
        f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` "
        f"CHARACTER SET {settings.db_charset} COLLATE {settings.db_collation}"
    )
    with bootstrap_engine.begin() as connection:
        connection.execute(create_stmt)
    bootstrap_engine.dispose()


def create_all_tables() -> None:
    Base.metadata.create_all(bind=get_engine())
