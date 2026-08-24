import os

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")


NOTE_SYSTEM_PROMPT = """You are an AI note-taking assistant. Use only information in the provided text. Do not invent facts. Write clear, concise English and preserve technical terms such as Python, C++, Java, API, SQL, machine learning, database, React, FastAPI, and GitHub."""


def ask_ai(prompt: str, system_prompt: str = NOTE_SYSTEM_PROMPT) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


def summarize_text(text: str) -> str:
    return ask_ai(f"Summarize this lecture or meeting transcript concisely:\n\n{text}")


def clean_notes(text: str) -> str:
    system = NOTE_SYSTEM_PROMPT + " Remove filler words, repetitions, pauses, and obvious transcription noise without changing meaning. Return only cleaned text."
    return ask_ai(f"Clean and organize this speech transcript:\n\n{text}", system)


def generate_key_points(text: str) -> str:
    system = NOTE_SYSTEM_PROMPT + " Extract 5 to 10 concise bullet points."
    return ask_ai(f"Extract the key points from this transcript:\n\n{text}", system)


def generate_title(text: str) -> str:
    system = "Generate one concise, professional note title. Return only the title with no quotation marks."
    return ask_ai(f"Generate a suitable title for this note:\n\n{text}", system)
