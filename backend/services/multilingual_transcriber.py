from typing import Any
import os


class MultilingualTranscriber:
    def __init__(self, model: Any):
        self.model = model

    def transcribe(self, audio_path: str, language: str | None = None) -> dict[str, Any]:
        """Transcribe browser recordings robustly.

        VAD can occasionally discard an entire short/quiet MediaRecorder WebM file.
        If that happens, retry the exact same audio without VAD instead of returning
        an empty transcript.
        """
        common_options = {
            "task": "transcribe",
            "language": language,
            "beam_size": int(os.getenv("WHISPER_BEAM_SIZE", "5")),
            "condition_on_previous_text": False,
            "word_timestamps": False,
            "temperature": 0.0,
        }

        def run_transcription(use_vad: bool):
            options = dict(common_options)
            options["vad_filter"] = use_vad
            if use_vad:
                options["vad_parameters"] = {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400,
                }
            return self.model.transcribe(audio_path, **options)

        segments, info = run_transcription(use_vad=True)
        results = self._collect_segments(segments)

        if not results:
            segments, info = run_transcription(use_vad=False)
            results = self._collect_segments(segments)

        return {"detected_language": info.language, "segments": results}

    @staticmethod
    def _collect_segments(segments) -> list[dict[str, Any]]:
        results = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                avg_logprob = getattr(segment, "avg_logprob", None)
                confidence = 0.85
                if avg_logprob is not None:
                    confidence = max(0.0, min(1.0, 1.0 + float(avg_logprob) / 5.0))
                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": text,
                    "language": MultilingualTranscriber.detect_segment_language(text),
                    "confidence": confidence,
                })
        return results

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
