import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_user_domain", "user_id", "company_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    company_name: Mapped[str] = mapped_column(String(500))
    company_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    draft_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="drafted")
    attempt_count: Mapped[int] = mapped_column(Integer, default=1)
    eval_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    VALID_STATUSES = {"drafted", "sent", "replied", "no_reply", "abandoned"}


class ProceduralMemory(Base):
    __tablename__ = "procedural_memory"
    __table_args__ = (UniqueConstraint("user_id", name="uq_procedural_user"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    current_doc: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ProceduralMemoryHistory(Base):
    __tablename__ = "procedural_memory_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    doc: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    change_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class SemanticProfile(Base):
    __tablename__ = "semantic_profile"
    __table_args__ = (UniqueConstraint("user_id", name="uq_semantic_user"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255))
    profile_doc: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class ProxycurlCache(Base):
    __tablename__ = "proxycurl_cache"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    response_json: Mapped[dict] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class FirecrawlCache(Base):
    __tablename__ = "firecrawl_cache"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    response_markdown: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
