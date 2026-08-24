from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    original_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    english_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    detected_languages: Mapped[str] = mapped_column(String(100), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="General", nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
