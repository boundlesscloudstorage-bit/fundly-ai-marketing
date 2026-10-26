"""Database configuration and request-scoped SQLAlchemy sessions."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

API_DIR = Path(__file__).resolve().parents[1]
load_dotenv(API_DIR / ".env")


def get_database_url() -> str:
    """Return the configured URL, defaulting to a local persistent SQLite file."""
    configured = os.getenv("DATABASE_URL")
    if not configured:
        return "sqlite:///./fundly.db"
    if configured.startswith("postgres://"):
        return "postgresql+psycopg://" + configured.removeprefix("postgres://")
    if configured.startswith("postgresql://"):
        return "postgresql+psycopg://" + configured.removeprefix("postgresql://")
    return configured


def create_database_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite:"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 15}
    return create_engine(url, **options)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


engine = create_database_engine()
SessionFactory = create_session_factory(engine)


def get_session(request: Request) -> Iterator[Session]:
    """Provide one session per request, with cleanup on success or failure."""
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session
