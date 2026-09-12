from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class AuthTokenResponse(BaseModel):
    token: str
    user: UserResponse


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)


class PasswordResetConfirm(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    otp: str = Field(min_length=4, max_length=10)
    new_password: str = Field(min_length=8, max_length=128)


class NoteCreate(BaseModel):
    user_id: int | None = None
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
    user_id: int
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
