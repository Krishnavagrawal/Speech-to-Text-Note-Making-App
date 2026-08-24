# Speech-to-Text Note Making App

An AI-powered multilingual speech-to-text note making application that converts spoken audio into structured notes, supports Hindi/English processing, and helps users organize notes with AI-generated summaries, key points, and tags.

## Features

- Speech-to-text transcription using Whisper
- Mixed-language and multilingual audio processing
- Hindi-to-English conversion support
- AI-generated titles, summaries, and key points
- Note creation, editing, deletion, and search
- Favorite notes and filtered views
- SQLite database persistence
- React frontend with Vite
- FastAPI backend

## Tech Stack

- Frontend: React, Vite, JavaScript
- Backend: Python, FastAPI
- AI/ML: Whisper, Ollama, language processing utilities
- Database: SQLite
- Storage: Local file uploads

## Project Structure

```text
speech-to-text-notes/
├── backend/
│   ├── services/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── database/
├── uploads/
├── .gitignore
├── requirements.txt
├── main.py
├── Phase7A-Functional-Testing.md
├── README.md
└── ...
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Optional: Ollama running locally for AI features

## Local Setup

### 1. Create and activate virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### 5. Open app

- Frontend: http://127.0.0.1:5173/
- Backend API: http://127.0.0.1:8001/
- Swagger docs: http://127.0.0.1:8001/docs

## Notes

This application is designed for local project/demo use and includes multilingual transcription and AI note processing pipelines suitable for academic or prototype deployments.

## License

This project is for academic and portfolio use.
