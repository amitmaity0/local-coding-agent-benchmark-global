"""Database setup and session management.

Provides SQLAlchemy engine, session factory, and table creation utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from orchestrator.config import DatabaseConfig


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def create_db_engine(config: DatabaseConfig) -> None:
    """Create database tables based on ORM models.

    Args:
        config: Database configuration.
    """
    from orchestrator.database import _engine  # noqa: F401

    _engine.config = config
    _engine._session_factory = sessionmaker(
        bind=_engine._raw_engine, expire_on_commit=False
    )


class _DBEngine:
    """Lazy database engine singleton."""

    _raw_engine = None
    _session_factory = None
    config: DatabaseConfig | None = None

    @property
    def engine(self):
        if self._raw_engine is None and self.config:
            self._raw_engine = create_engine(
                self.config.url, echo=self.config.echo
            )
            self._session_factory = sessionmaker(
                bind=self._raw_engine, expire_on_commit=False
            )
        return self._raw_engine

    @property
    def session_factory(self):
        if self._session_factory is None and self.config:
            self._raw_engine = create_engine(
                self.config.url, echo=self.config.echo
            )
            self._session_factory = sessionmaker(
                bind=self._raw_engine, expire_on_commit=False
            )
        return self._session_factory


_engine = _DBEngine()


def init_db(config: DatabaseConfig) -> None:
    """Initialize the database engine and create all tables.

    Args:
        config: Database configuration.
    """
    _engine.config = config
    engine = create_engine(config.url, echo=config.echo)
    _engine._raw_engine = engine
    _engine._session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Yields:
        A SQLAlchemy Session that is committed and closed on exit.
    """
    if _engine._session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    session = _engine._session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()