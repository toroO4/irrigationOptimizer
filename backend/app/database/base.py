"""
SAR Irrigation Scheduling System — Declarative Base.

Provides the SQLAlchemy declarative base class with common columns
that all ORM models inherit from.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    Provides:
    - ``id``: UUID primary key (auto-generated)
    - ``created_at``: Timestamp set automatically on insert
    - ``updated_at``: Timestamp updated automatically on modification
    """
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps to a model.

    These columns are automatically managed by the database:
    - ``created_at`` is set to the current UTC time on insert
    - ``updated_at`` is updated to the current UTC time on every update
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """
    Mixin that provides a UUID primary key column.

    Generates a new UUID4 for each record automatically.
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        doc="Unique identifier (UUID4)",
    )
