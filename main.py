from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import os
import shutil
import uuid

app = FastAPI(
    title="Speech-to-Text Note Making API",
    description="Backend API for the Speech-to-Text Note Making App",
    version="1.0.0"
)

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load Whisper model
# "base" is a good starting point for development.
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


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

        # Transcribe audio
        segments, info = model.transcribe(
            file_path,
            beam_size=5
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return {
            "success": True,
            "language": info.language,
            "language_probability": info.language_probability,
            "transcription": transcript
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