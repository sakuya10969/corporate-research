"""SQLAlchemy async engine / session 設定"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.shared.config import get_settings

_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url, echo=False, pool_pre_ping=True
        )
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _session_factory


def get_async_session() -> AsyncSession:
    """BackgroundTask 等、FastAPI Depends 外でセッションを取得する。

    Usage::

        async with get_async_session() as session:
            ...
    """
    return _get_session_factory()()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends 用セッションジェネレーター"""
    async with _get_session_factory()() as session:
        yield session
