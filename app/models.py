from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
	return datetime.now(timezone.utc)


class StoredFile(Base):
	__tablename__ = "stored_files"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	owner_user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
	original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
	stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
	content_type: Mapped[str] = mapped_column(String(255), nullable=False)
	size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
	upload_path: Mapped[str] = mapped_column(String(1024), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

	link_audits: Mapped[list["LinkAudit"]] = relationship(back_populates="file")


class LinkAudit(Base):
	__tablename__ = "link_audits"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"), nullable=False, index=True)
	requester_user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
	ttl_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

	file: Mapped[StoredFile] = relationship(back_populates="link_audits")
