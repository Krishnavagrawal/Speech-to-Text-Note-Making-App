import re

DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")
LATIN_WORD_PATTERN = re.compile(r"[A-Za-z]")


def detect_languages(transcript: str, primary_language: str | None = None) -> list[str]:
    languages: list[str] = []

    if DEVANAGARI_PATTERN.search(transcript):
        languages.append("hi")
    if LATIN_WORD_PATTERN.search(transcript):
        languages.append("en")

    if not languages and primary_language:
        languages.append(primary_language)
    if not languages:
        languages.append("en")

    return languages
