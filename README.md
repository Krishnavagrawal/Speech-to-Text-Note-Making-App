# 🛠️ Speech-to-Text Note Making App

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-61dafb)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/status-working%20prototype-success)](https://github.com/Krishnavagrawal/Speech-to-Text-Note-Making-App)

### AI-powered multilingual speech-to-text note making application
*Convert spoken audio into structured, searchable notes with AI summaries, key points, and bilingual support.*

---

## 📖 Overview

This project helps users turn voice recordings into organized notes. It supports transcription, multilingual handling, Hindi/English conversion, AI-generated summaries, and note management through a modern frontend and FastAPI backend.

The application is designed for local academic and prototype use, with a SQLite database and a local AI processing pipeline that works on top of open-source transcription and generation utilities.

---

## ✅ Status

This is a working prototype with the core features implemented and validated.

| Component | Status | Notes |
| --- | --- | --- |
| Frontend | ✅ Working | React + Vite dashboard for notes and voice actions |
| Backend API | ✅ Working | FastAPI endpoints for notes, AI, and transcription |
| Transcription | ✅ Working | Whisper-based speech-to-text flow |
| Hindi/English processing | ✅ Working | Mixed-language handling and conversion pipeline |
| Note CRUD | ✅ Working | Create, read, update, delete, search, filter, favorite |
| AI summaries / titles | ✅ Working | Local generation flow for summaries and titles |
| Validation | ✅ Working | Functional, AI, database, security, and performance checks completed |

---

## 🚀 Quick Start

### 1. Set up the environment

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### 4. Open the app

- Frontend: http://127.0.0.1:5173/
- Backend: http://127.0.0.1:8001/
- API docs: http://127.0.0.1:8001/docs

---

## 🏗️ Architecture

The application follows a simple client-server workflow:

- Frontend: React app for note creation, editing, search, and voice upload
- Backend: FastAPI service for transcription and AI operations
- Database: SQLite for persistent note storage
- AI layer: Local generation and processing utilities for summaries, notes, key points, and titles
- Audio pipeline: Speech-to-text + language processing + translation integration

---

## 📁 Project Layout

```text
speech-to-text-notes/
├── backend/
│   ├── services/
│   ├── ai_notes.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── migrate_phase3.py
│   └── test_ai.py
├── frontend/
│   ├── public/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── database/
├── uploads/
├── .gitignore
├── requirements.txt
├── main.py
├── Phase7A-Functional-Testing.md
├── README.md
└── screenshots/
```

---

## ✨ Features

- Voice/audio transcription into text notes
- Mixed-language speech support
- Hindi-to-English conversion
- AI-generated note titles
- AI summary generation
- Key-point extraction
- Text cleaning and normalization
- Note search and favorites
- Note editing and deletion
- Local persistence using SQLite

---

## 🧪 Validation

The project includes a live Phase 7 testing report covering:

- Functional testing
- AI accuracy testing
- Database validation
- Performance testing
- Error handling and security testing
- Final UI compatibility testing

See [Phase7A-Functional-Testing.md](Phase7A-Functional-Testing.md) for the complete report.

---

## 🗺️ Next Milestones

- Improve real microphone recording quality and accuracy
- Add stronger authentication and profile management
- Optimize AI latency for faster responses
- Expand multilingual support and transcript refinement
- Add deployment-ready hosting configuration for production use

---

Built for academic project/demo use and local AI note processing.
