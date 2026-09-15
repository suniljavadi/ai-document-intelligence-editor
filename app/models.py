from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    versions: Mapped[list["DocumentVersion"]] = relationship(cascade="all, delete-orphan", order_by="DocumentVersion.version_number")
    chunks: Mapped[list["DocumentChunk"]] = relationship(cascade="all, delete-orphan")
    analysis: Mapped["DocumentAnalysis"] = relationship(cascade="all, delete-orphan", uselist=False)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    change_summary: Mapped[str] = mapped_column(String(500), default="Initial version")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    section: Mapped[str] = mapped_column(String(255), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=True)


class DocumentAnalysis(Base):
    __tablename__ = "document_analysis"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), unique=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
