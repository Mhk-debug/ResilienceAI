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
        pool_recycle=300,
        pool_size=5,
        max_overflow=10,
        future=True,
        echo=False,
        connect_args={
        "sslmode": "require"
        }
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