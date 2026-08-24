from .english_converter import translate_segments_to_english
from .text_processing import correct_transcript


def convert_segments_to_english(segments: list[dict]) -> list[dict]:
    prepared_segments = [{**segment, "text": correct_transcript(segment["text"])} for segment in segments]
    translatable = [segment for segment in prepared_segments if segment["language"] in {"hi", "ur", "mixed"}]
    translations = translate_segments_to_english([segment["text"] for segment in translatable]) if translatable else {}
    converted = []
    translation_index = 0
    for segment in prepared_segments:
        text = segment["text"]
        language = segment["language"]
        english_text = translations[translation_index] if language in {"hi", "ur", "mixed"} else text
        if language in {"hi", "ur", "mixed"}:
            translation_index += 1
        converted.append({
            "start": segment["start"],
            "end": segment["end"],
            "original": text,
            "english": english_text,
            "language": language,
        })
    return converted
