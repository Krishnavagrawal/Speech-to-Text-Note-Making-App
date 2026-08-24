from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    original_transcript: str = Field(min_length=1)
    english_transcript: str = Field(min_length=1)
    detected_languages: str = Field(min_length=1, max_length=100)
    summary: str = ""
    key_points: str = ""
    tag: str = ""
    category: str = "General"
    is_favorite: bool = False


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    original_transcript: str | None = Field(default=None, min_length=1)
    english_transcript: str | None = Field(default=None, min_length=1)
    summary: str | None = None
    key_points: str | None = None
    tag: str | None = None
    category: str | None = None
    is_favorite: bool | None = None


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    original_transcript: str
    english_transcript: str
    detected_languages: str
    summary: str | None = None
    key_points: str | None = None
    tag: str = ""
    category: str = "General"
    is_favorite: bool = False
    created_at: datetime
    updated_at: datetime
