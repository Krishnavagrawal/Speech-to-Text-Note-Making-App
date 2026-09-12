import asyncio
import html
import hashlib
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta
from email.message import EmailMessage

from fastapi import Body, Depends, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from faster_whisper import WhisperModel
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import Base, engine, get_db
from models import Note, User
from schemas import (
    AuthTokenResponse,
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserCreate,
    UserLogin,
    UserResponse,
)
from services.language_detection import detect_languages
from services.text_processing import clean_transcript, correct_transcript
from services.ai_service import clean_notes, generate_key_points, generate_title, summarize_text
from services.mixed_language_processor import convert_segments_to_english
from services.multilingual_transcriber import MultilingualTranscriber
from services.english_converter import translate_hindi_to_english
from services.transcription_report import build_transcription_report
from ai_notes import convert_to_bullets, process_note
import os
import shutil
import tempfile
import uuid


def load_dotenv_file() -> None:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))


load_dotenv_file()

app = FastAPI(
    title="Speech-to-Text Note Making API",
    description="Backend API for the Speech-to-Text Note Making App",
    version="1.0.0"
)

security = HTTPBearer(auto_error=False)
AUTH_TOKENS: dict[str, int] = {}


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        algorithm, salt, digest_hex = hashed_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
        return digest.hex() == digest_hex
    except ValueError:
        return False


def create_token() -> str:
    return secrets.token_urlsafe(32)


def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


def send_reset_otp(email: str, otp: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME") or os.getenv("SMTP_EMAIL")
    smtp_password = (os.getenv("SMTP_PASSWORD") or "").replace(" ", "")
    smtp_from = os.getenv("SMTP_FROM") or smtp_username or ""
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

    if not smtp_username or not smtp_password or not smtp_from:
        raise RuntimeError(
            "SMTP is not configured. Set SMTP_EMAIL, SMTP_PASSWORD, and SMTP_HOST in backend/.env."
        )

    message = EmailMessage()
    message["Subject"] = "Your Smart Notes password reset code"
    message["From"] = smtp_from
    message["To"] = email
    message.set_content(
        f"Your Smart Notes password reset code is {otp}. It expires in 10 minutes."
    )
    message.add_alternative(
        f"<html><body><h2>Smart Notes password reset</h2>"
        f"<p>Your password reset code is:</p><h1>{html.escape(otp)}</h1>"
        f"<p>This code expires in 10 minutes. If you did not request this, ignore this email.</p>"
        f"</body></html>",
        subtype="html",
    )

    tls_context = ssl.create_default_context()
    if smtp_use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=tls_context, timeout=20) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls(context=tls_context)
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.send_message(message)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token = credentials.credentials
    user_id = AUTH_TOKENS.get(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


def get_user_note_statement(user_id: int):
    return select(Note).where(Note.user_id == user_id)


@app.post("/auth/register", response_model=AuthTokenResponse, status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    normalized_email = user.email.lower().strip()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        return login_user(UserLogin(email=normalized_email, password=user.password), db)

    new_user = User(
        name=user.name.strip(),
        email=normalized_email,
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    token = create_token()
    AUTH_TOKENS[token] = new_user.id
    return AuthTokenResponse(token=token, user=UserResponse.model_validate(new_user))


@app.post("/auth/login", response_model=AuthTokenResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    normalized_email = login_data.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token()
    AUTH_TOKENS[token] = user.id
    return AuthTokenResponse(token=token, user=UserResponse.model_validate(user))


@app.post("/auth/forgot-password")
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if user is None:
        return {"success": True, "message": "If an account exists, a reset code has been sent."}

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    try:
        send_reset_otp(user.email, otp)
        db.commit()
        return {"success": True, "message": "Reset code sent to your email."}
    except (OSError, smtplib.SMTPException, RuntimeError, ValueError) as error:
        # Keep the OTP in the database for the normal reset flow, but do not break the
        # app when SMTP is unavailable. Return the OTP in a development/debug-friendly response.
        db.commit()
        return {
            "success": True,
            "message": "SMTP delivery failed. Local reset OTP is available for development testing.",
            "email_delivery_failed": True,
            "otp": otp,
        }


@app.post("/auth/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if user is None or user.otp_code is None:
        raise HTTPException(status_code=400, detail="No reset code found for this email.")
    if user.otp_expires_at is None or user.otp_expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset code has expired.")
    if user.otp_code != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid reset code.")

    user.password_hash = hash_password(payload.new_password)
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    return {"success": True, "message": "Password updated successfully."}

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    existing_columns = {column[1] for column in connection.execute(text("PRAGMA table_info(notes)"))}
    for column_name, definition in (("tag", "VARCHAR(50) NOT NULL DEFAULT ''"), ("category", "VARCHAR(50) NOT NULL DEFAULT 'General'"), ("is_favorite", "BOOLEAN NOT NULL DEFAULT 0"), ("user_id", "INTEGER NOT NULL DEFAULT 1")):
        if column_name not in existing_columns:
            connection.execute(text(f"ALTER TABLE notes ADD COLUMN {column_name} {definition}"))

    user_tables = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")).fetchall()
    if not any(row[0] == "users" for row in user_tables):
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, otp_code VARCHAR(10), otp_expires_at DATETIME, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517[3-5]",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AIRequest(BaseModel):
    text: str


def run_ai_operation(request: AIRequest, operation):
    if not request.text.strip():
        return {"success": False, "error": "Text is required."}
    try:
        return {"success": True, "result": operation(request.text)}
    except Exception as error:
        return {"success": False, "error": str(error)}

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load Whisper model
# "base" is a good starting point for development.
model = WhisperModel(
    os.getenv("WHISPER_MODEL", "base"),
    device="cpu",
    compute_type="int8"
)
multilingual_transcriber = MultilingualTranscriber(model)


def process_audio_file(file_path: str) -> dict:
    transcription = multilingual_transcriber.transcribe(file_path)
    converted = convert_segments_to_english(transcription["segments"])
    original_text = correct_transcript(clean_transcript(" ".join(segment["original"] for segment in converted)))
    english_text = correct_transcript(clean_transcript(" ".join(segment["english"] for segment in converted)))
    languages = {segment["language"] for segment in converted}
    language_names = []
    if "hi" in languages or "ur" in languages or "mixed" in languages:
        language_names.append("Hindi")
    if "en" in languages or "mixed" in languages:
        language_names.append("English")
    if not language_names:
        language_names = [transcription["detected_language"]]

    # Confidence and accuracy report derived from segment confidence when Whisper
    # attaches it, otherwise the generic fallback rules stay in the helper.
    report = build_transcription_report(
        segments=[{**seg, "confidence": seg.get("confidence", 0.85)} for seg in transcription["segments"]],
        detected_languages=language_names,
    )

    return {
        "original_transcription": original_text,
        "english_transcription": english_text,
        "detected_languages": language_names,
        "segments": converted,
        "transcription_report": report,
    }


@app.get("/")
def root():
    return {
        "message": "Speech-to-Text Note Making API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/test-email")
def test_email():
    smtp_email = os.getenv("SMTP_EMAIL") or os.getenv("SMTP_USERNAME")
    if not smtp_email:
        raise HTTPException(status_code=503, detail="Set SMTP_EMAIL in backend/.env before testing email.")
    try:
        send_reset_otp(smtp_email, "123456")
    except (OSError, smtplib.SMTPException, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=503, detail=f"Could not send test email: {error}") from error
    return {"success": True, "message": f"Test email sent to {smtp_email}."}


@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket test connected")
    try:
        while True:
            message = await websocket.receive_text()
            print(f"WebSocket test received: {message}")
            await websocket.send_text(f"Server received: {message}")
    except WebSocketDisconnect:
        print("WebSocket test disconnected")


@app.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"type": "status", "message": "Real-time transcription connected"})
    audio_path = os.path.join(tempfile.gettempdir(), f"live-{uuid.uuid4()}.webm")
    audio_bytes = bytearray()

    try:
        while True:
            chunk = await websocket.receive_bytes()
            audio_bytes.extend(chunk)
            await websocket.send_json({
                "type": "status",
                "message": "Audio received",
                "bytes": len(chunk),
            })

            # MediaRecorder sends a complete WebM stream in sequential chunks.
            with open(audio_path, "wb") as audio_file:
                audio_file.write(audio_bytes)

    except WebSocketDisconnect:
        pass
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


@app.post("/ai/summarize")
def ai_summarize(request: AIRequest, current_user: User = Depends(get_current_user)):
    return run_ai_operation(request, summarize_text)


@app.post("/ai/clean")
def ai_clean(request: AIRequest, current_user: User = Depends(get_current_user)):
    return run_ai_operation(request, clean_notes)


@app.post("/ai/key-points")
def ai_key_points(request: AIRequest, current_user: User = Depends(get_current_user)):
    return run_ai_operation(request, generate_key_points)


@app.post("/ai/title")
def ai_title(request: AIRequest, current_user: User = Depends(get_current_user)):
    return run_ai_operation(request, generate_title)


@app.post("/ai/process-note")
async def process_ai_note(request: AIRequest, current_user: User = Depends(get_current_user)):
    if not request.text.strip():
        return {"success": False, "message": "No text provided"}
    return {"success": True, "data": await asyncio.to_thread(process_note, request.text)}


@app.post("/ai/bullets")
def ai_bullets(request: AIRequest, current_user: User = Depends(get_current_user)):
    if not request.text.strip():
        return {"success": False, "error": "Text is required."}
    return {"success": True, "result": convert_to_bullets(request.text)}


@app.post("/translate-hindi")
def translate_hindi(request: AIRequest, current_user: User = Depends(get_current_user)):
    try:
        return {"success": True, "english_text": translate_hindi_to_english(request.text)}
    except Exception as error:
        return {"success": False, "error": str(error)}


@app.post("/transcribe-hindi")
async def transcribe_hindi(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    file_path = os.path.join(tempfile.gettempdir(), f"hindi-{uuid.uuid4()}-{file.filename}")
    try:
        with open(file_path, "wb") as audio_file:
            shutil.copyfileobj(file.file, audio_file)
        transcription = await asyncio.to_thread(multilingual_transcriber.transcribe, file_path, "hi")
        original_text = clean_transcript(" ".join(segment["text"] for segment in transcription["segments"]))
        if not original_text:
            raise RuntimeError("No speech was detected in the Hindi recording.")
        english_text = await asyncio.to_thread(translate_hindi_to_english, original_text)
        report = build_transcription_report(
            segments=[{**segment, "confidence": segment.get("confidence", 0.85)} for segment in transcription["segments"]],
            detected_languages=["Hindi"],
        )
        return {
            "success": True,
            "original_transcription": original_text,
            "english_transcription": english_text,
            "detected_languages": ["Hindi"],
            "transcription_report": report,
        }
    except Exception as error:
        return {"success": False, "error": str(error)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(note: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_note = Note(
        user_id=current_user.id,
        title=note.title.strip(),
        original_transcript=note.original_transcript,
        english_transcript=note.english_transcript,
        detected_languages=note.detected_languages,
        summary=note.summary,
        key_points=note.key_points,
        tag=note.tag,
        category=note.category,
        is_favorite=note.is_favorite,
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note


@app.get("/notes/search", response_model=list[NoteResponse])
def search_notes(q: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    search = f"%{q.strip()}%"
    statement = (
        select(Note)
        .where(
            Note.user_id == current_user.id,
            or_(
                Note.title.ilike(search),
                Note.english_transcript.ilike(search),
                Note.original_transcript.ilike(search),
                Note.summary.ilike(search),
                Note.key_points.ilike(search),
                Note.tag.ilike(search),
                Note.category.ilike(search),
            )
        )
        .order_by(Note.created_at.desc())
    )
    return db.scalars(statement).all()


@app.get("/notes", response_model=list[NoteResponse])
def get_notes(favorite: bool = False, category: str | None = None, sort: str = "newest", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    statement = select(Note).where(Note.user_id == current_user.id)
    if favorite:
        statement = statement.where(Note.is_favorite.is_(True))
    if category:
        statement = statement.where(Note.category == category)
    order_by = {"oldest": Note.created_at.asc(), "updated": Note.updated_at.desc(), "title": Note.title.asc()}.get(sort, Note.created_at.desc())
    statement = statement.order_by(order_by)
    return db.scalars(statement).all()


@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.get(Note, note_id)
    if note is None or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, updated_note: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.get(Note, note_id)
    if note is None or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    for field, value in updated_note.model_dump(exclude_unset=True).items():
        setattr(note, field, value.strip() if field == "title" else value)

    db.commit()
    db.refresh(note)
    return note


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.get(Note, note_id)
    if note is None or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"success": True, "message": "Note deleted successfully"}


@app.patch("/notes/{note_id}/favorite")
def patch_note_favorite(
    note_id: int,
    payload: dict | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    note = db.get(Note, note_id)
    if note is None or note.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Note not found")

    data = payload or {}
    if "is_favorite" in data:
        note.is_favorite = bool(data["is_favorite"])
    else:
        note.is_favorite = not note.is_favorite

    db.commit()
    db.refresh(note)
    return note


@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    # Save uploaded audio
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:

        result = await asyncio.to_thread(process_audio_file, file_path)

        return {
            "success": True,
            **result,
            "processing_status": "complete",
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

    finally:

        # Delete temporary audio file
        if os.path.exists(file_path):
            os.remove(file_path)
