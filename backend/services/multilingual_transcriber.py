from typing import Any


class MultilingualTranscriber:
    def __init__(self, model: Any):
        self.model = model

    def transcribe(self, audio_path: str, language: str | None = None) -> dict[str, Any]:
        segments, info = self.model.transcribe(
            audio_path,
            task="transcribe",
            language=language,
            beam_size=int(__import__("os").getenv("WHISPER_BEAM_SIZE", "1")),
            vad_filter=True,
            condition_on_previous_text=False,
            word_timestamps=False,
            temperature=0.0,
        )

        results = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": text,
                    "language": self.detect_segment_language(text),
                })

        return {"detected_language": info.language, "segments": results}

    @staticmethod
    def detect_segment_language(text: str) -> str:
        hindi_chars = sum("\u0900" <= char <= "\u097F" for char in text)
        urdu_chars = sum("\u0600" <= char <= "\u06FF" for char in text)
        latin_chars = sum(char.isascii() and char.isalpha() for char in text)
        script_chars = hindi_chars + urdu_chars
        if script_chars and latin_chars:
            return "mixed"
        if hindi_chars:
            return "hi"
        if urdu_chars:
            return "ur"
        if latin_chars == 0:
            return "unknown"
        return "en"
