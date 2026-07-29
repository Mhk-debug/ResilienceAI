"""
database/models.py

SQLAlchemy ORM models for the Earthquake Risk Assessment Platform.
Stores searchable metadata as relational columns while preserving
the complete assessment payload in PostgreSQL JSONB columns.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Float,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import (
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Email Verification ---
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    verification_token: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    verification_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Password Reset ---
    password_reset_token: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    password_reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Email Change ---
    new_email: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    email_change_token: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    email_change_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # --- Audit ---
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    assessments: Mapped[list["Assessment"]] = relationship(back_populates="owner")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class Assessment(Base):
    __tablename__ = "assessments"

    # -------------------------
    # Primary Key
    # -------------------------

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # -------------------------
    # Foreign Key to User
    # -------------------------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    owner: Mapped["User"] = relationship(back_populates="assessments")

    # -------------------------
    # Timestamp
    # -------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # -------------------------
    # Location
    # -------------------------

    place_name: Mapped[str | None] = mapped_column(
        String, 
        nullable=True
    )
    
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # -------------------------
    # Scores
    # -------------------------

    resilience_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    hazard_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
    )

    hazard_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # -------------------------
    # Complete API Outputs
    # -------------------------

    profile: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    building: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    hazard: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    llm: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # -------------------------
    # Metadata
    # -------------------------

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    execution_time_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # -------------------------
    # Convenience
    # -------------------------

    def __repr__(self) -> str:
        return (
            f"<Assessment("
            f"id={self.id}, "
            f"location='{self.place_name}', "
            f"hazard={self.hazard_score:.1f}, "
            f"resilience={self.resilience_score:.1f})>"
        )