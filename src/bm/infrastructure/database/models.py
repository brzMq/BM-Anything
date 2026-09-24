"""SQLAlchemy declarative Base + P0 placeholder models.

Domain semantics land in P2+. P0 only needs:
- A ``Base`` for Alembic autogenerate.
- A minimal ``schema_meta`` table so the first migration is non-empty and
  the DB round-trip is verifiable from an empty database.

IMPORTANT: This module is Infrastructure. Domain code MUST NOT import it
directly; go through Repository interfaces.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all BM business tables."""


class SchemaMeta(Base):
    """Bookkeeping table: records BM schema identity + migration watermark.

    Not a domain entity. Used by health/readiness checks and by future
    migration tooling to assert the DB was created by BM.
    """

    __tablename__ = "schema_meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )
