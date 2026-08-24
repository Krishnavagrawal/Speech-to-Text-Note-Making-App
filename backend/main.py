import asyncio
from fastapi import Body, Depends, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import Base, engine, get_db
from models import Note
from schemas import NoteCreate, NoteResponse, NoteUpdate
from services.language_detection import detect_languages
from services.text_processing import clean_transcript, correct_transcript
from services.ai_service import clean_notes, generate_key_points, generate_title, summarize_text
from services.mixed_language_processor import convert_segments_to_english
from services.multilingual_transcriber import MultilingualTranscriber
from services.english_converter import translate_hindi_to_english
from ai_notes import convert_to_bullets, process_note
import os
import shutil
import tempfile
import uuid

app = FastAPI(
    title="Speech-to-Text Note Making API",
    description="Backend API for the Speech-to-Text Note Making App",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

with engine.begin() as connection:
    existing_columns = {column[1] for column in connection.execute(text("PRAGMA table_info(notes)"))}
    for column_name, definition in (("tag", "VARCHAR(50) NOT NULL DEFAULT ''"), ("category", "VARCHAR(50) NOT NULL DEFAULT 'General'"), ("is_favorite", "BOOLEAN NOT NULL DEFAULT 0")):
        if column_name not in existing_columns:
            connection.execute(text(f"ALTER TABLE notes ADD COLUMN {column_name} {definition}"))

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
    return {
        "original_transcription": original_text,
        "english_transcription": english_text,
        "detected_languages": language_names,
        "segments": converted,
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
def ai_summarize(request: AIRequest):
    return run_ai_operation(request, summarize_text)


@app.post("/ai/clean")
def ai_clean(request: AIRequest):
    return run_ai_operation(request, clean_notes)


@app.post("/ai/key-points")
def ai_key_points(request: AIRequest):
    return run_ai_operation(request, generate_key_points)


@app.post("/ai/title")
def ai_title(request: AIRequest):
    return run_ai_operation(request, generate_title)


@app.post("/ai/process-note")
async def process_ai_note(request: AIRequest):
    if not request.text.strip():
        return {"success": False, "message": "No text provided"}
    return {"success": True, "data": await asyncio.to_thread(process_note, request.text)}


@app.post("/ai/bullets")
def ai_bullets(request: AIRequest):
    if not request.text.strip():
        return {"success": False, "error": "Text is required."}
    return {"success": True, "result": convert_to_bullets(request.text)}


@app.post("/translate-hindi")
def translate_hindi(request: AIRequest):
    try:
        return {"success": True, "english_text": translate_hindi_to_english(request.text)}
    except Exception as error:
        return {"success": False, "error": str(error)}


@app.post("/transcribe-hindi")
async def transcribe_hindi(file: UploadFile = File(...)):
    file_path = os.path.join(tempfile.gettempdir(), f"hindi-{uuid.uuid4()}-{file.filename}")
    try:
        with open(file_path, "wb") as audio_file:
            shutil.copyfileobj(file.file, audio_file)
        transcription = await asyncio.to_thread(multilingual_transcriber.transcribe, file_path, "hi")
        original_text = clean_transcript(" ".join(segment["text"] for segment in transcription["segments"]))
        if not original_text:
            raise RuntimeError("No speech was detected in the Hindi recording.")
        english_text = await asyncio.to_thread(translate_hindi_to_english, original_text)
        return {
            "success": True,
            "original_transcription": original_text,
            "english_transcription": english_text,
            "detected_languages": ["Hindi"],
        }
    except Exception as error:
        return {"success": False, "error": str(error)}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = Note(
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
def search_notes(q: str, db: Session = Depends(get_db)):
    search = f"%{q.strip()}%"
    statement = (
        select(Note)
        .where(
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
def get_notes(favorite: bool = False, category: str | None = None, sort: str = "newest", db: Session = Depends(get_db)):
    statement = select(Note)
    if favorite:
        statement = statement.where(Note.is_favorite.is_(True))
    if category:
        statement = statement.where(Note.category == category)
    order_by = {"oldest": Note.created_at.asc(), "updated": Note.updated_at.desc(), "title": Note.title.asc()}.get(sort, Note.created_at.desc())
    statement = statement.order_by(order_by)
    return db.scalars(statement).all()


@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, updated_note: NoteUpdate, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    for field, value in updated_note.model_dump(exclude_unset=True).items():
        setattr(note, field, value.strip() if field == "title" else value)

    db.commit()
    db.refresh(note)
    return note


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"success": True, "message": "Note deleted successfully"}


@app.patch("/notes/{note_id}/favorite")
def patch_note_favorite(
    note_id: int,
    payload: dict | None = Body(default=None),
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)
    if note is None:
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
