import os

import requests


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")


def translate_hindi_to_english(text: str) -> str:
    prompt = (
        "Translate the following Hindi, Urdu, or Hindi-English sentence into natural English. "
        "Return only English. Preserve the meaning and technical English terms. "
        "Do not explain or add information.\n\nText:\n" + text
    )
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    translated = response.json().get("response", "").strip()
    if not translated:
        raise RuntimeError("Ollama returned an empty translation.")
    return translated


def translate_segments_to_english(texts: list[str]) -> dict[int, str]:
    if not texts:
        return {}
    numbered_text = "\n".join(f"{index}: {text}" for index, text in enumerate(texts))
    prompt = (
        "Translate the Hindi or Urdu portions in each numbered line into natural English. "
        "Keep existing English technical terms and meaning. Return exactly one line "
        "for each input using the same number, with no extra text.\n\n" + numbered_text
    )
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
        timeout=120,
    )
    response.raise_for_status()
    translations = {}
    for line in response.json().get("response", "").splitlines():
        number, separator, translation = line.partition(":")
        if separator and number.strip().isdigit() and translation.strip():
            translations[int(number.strip())] = translation.strip()
    if len(translations) != len(texts):
        raise RuntimeError("Ollama returned an incomplete batch translation.")
    return translations
