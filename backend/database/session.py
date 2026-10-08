"""
Centralized SQLAlchemy engine/session configuration.

This module should be imported anywhere a database session is needed.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is missing."
    )

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        # Neon kills idle server-side connections aggressively; a request can
        # hold a pooled connection for 30-60s while SoilGrids/USGS/LLM calls
        # run. Recycle well under that window so a stale socket is never
        # handed out, and fail fast on connect rather than hanging the save.
        pool_recycle=60,
        pool_size=5,
        max_overflow=10,
        future=True,
        echo=False,
        # No hardcoded sslmode: psycopg defaults to "prefer", which works with
        # both local Postgres (no SSL) and remote URLs that carry ?sslmode=require.
        connect_args={"connect_timeout": 10},
    )

except SQLAlchemyError:
    logger.exception("Failed to initialize SQLAlchemy engine.")
    raise

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency.

    Yields a database session and guarantees cleanup.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()