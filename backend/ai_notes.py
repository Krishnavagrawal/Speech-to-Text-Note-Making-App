from services.ai_service import generate_title as ai_generate_title
from services.ai_service import summarize_text


def generate_key_points(text: str) -> list[str]:
    sentences = []
    for sentence in text.replace("!", ".").replace("?", ".").split("."):
        sentence = sentence.strip()
        if len(sentence.split()) >= 5:
            sentences.append(sentence)
    return sentences[:8]


def convert_to_bullets(text: str) -> str:
    sentences = []
    for sentence in text.replace("!", ".").replace("?", ".").split("."):
        sentence = sentence.strip()
        if sentence:
            sentences.append(f"- {sentence}")
    return "\n".join(sentences)


def generate_title(text: str) -> str:
    if not text.strip():
        return "Untitled Note"
    try:
        return ai_generate_title(text)
    except Exception:
        first_sentence = next((sentence.strip() for sentence in text.split(".") if sentence.strip()), "Untitled Note")
        return " ".join(first_sentence.split()[:8]).title()


def process_note(text: str) -> dict[str, str | list[str]]:
    text = text.strip()
    if not text:
        return {"title": "Untitled Note", "summary": "", "key_points": [], "bullets": ""}
    try:
        summary = summarize_text(text)
    except Exception:
        summary = text if len(text.split()) < 30 else " ".join(text.split()[:30]) + "..."
    return {
        "title": generate_title(text),
        "summary": summary,
        "key_points": generate_key_points(text),
        "bullets": convert_to_bullets(text),
    }
