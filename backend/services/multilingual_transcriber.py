from typing import Any
import os
import re


class MultilingualTranscriber:
    def __init__(self, model: Any):
        self.model = model

    def transcribe(self, audio_path: str, language: str | None = None) -> dict[str, Any]:
        """Transcribe browser recordings while rejecting Whisper hallucinations.

        Browser WebM recordings can contain silence or very low-volume audio. Whisper
        may otherwise turn that into repeated nonsense such as "Yn yw'n ...". We use
        Whisper's speech/no-speech and compression filters, then apply a small safety
        check for obviously repetitive output. If VAD rejects everything, the same
        audio is retried without VAD.
        """
        common_options = {
            "task": "transcribe",
            "language": language,
            "beam_size": int(os.getenv("WHISPER_BEAM_SIZE", "5")),
            "condition_on_previous_text": False,
            "word_timestamps": False,
            "temperature": 0.0,
            "compression_ratio_threshold": 2.0,
            "log_prob_threshold": -0.8,
            "no_speech_threshold": 0.55,
        }

        def run_transcription(use_vad: bool):
            options = dict(common_options)
            options["vad_filter"] = use_vad
            if use_vad:
                options["vad_parameters"] = {
                    "min_silence_duration_ms": 500,
                    "speech_pad_ms": 400,
                    "min_speech_duration_ms": 250,
                }
            return self.model.transcribe(audio_path, **options)

        segments, info = run_transcription(use_vad=True)
        results = self._collect_segments(segments)

        # A quiet browser recording may be incorrectly removed by VAD. Retry the
        # exact same file without VAD before declaring that no speech was detected.
        if not results:
            segments, info = run_transcription(use_vad=False)
            results = self._collect_segments(segments)

        # Do not allow a successful API response containing Whisper hallucinations.
        if results and self._looks_like_hallucination(results):
            segments, info = run_transcription(use_vad=False)
            results = self._collect_segments(segments, reject_repetition=True)

        if not results:
            raise RuntimeError(
                "No reliable speech was detected in the recording. "
                "Please record again, keep the microphone close, and speak clearly for at least 2 seconds."
            )

        return {"detected_language": info.language, "segments": results}

    @staticmethod
    def _collect_segments(segments, reject_repetition: bool = True) -> list[dict[str, Any]]:
        results = []
        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue

            # Reject decoder output that is dominated by repeated words/short phrases.
            # This is a common failure mode on silence/noise in short recordings.
            if reject_repetition and MultilingualTranscriber._is_repetitive(text):
                continue

            avg_logprob = getattr(segment, "avg_logprob", None)
            no_speech_prob = getattr(segment, "no_speech_prob", None)

            if avg_logprob is not None:
                confidence = max(0.0, min(1.0, 1.0 + float(avg_logprob) / 5.0))
            elif no_speech_prob is not None:
                confidence = max(0.0, min(1.0, 1.0 - float(no_speech_prob)))
            else:
                # Do not pretend this is measured accuracy; this is only a neutral
                # fallback for model versions that omit both metadata fields.
                confidence = 0.0

            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": text,
                "language": MultilingualTranscriber.detect_segment_language(text),
                "confidence": confidence,
            })
        return results

    @staticmethod
    def _is_repetitive(text: str) -> bool:
        words = re.findall(r"[A-Za-zÀ-ÿĀ-ž']+", text.lower())
        if len(words) < 8:
            return False

        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.30:
            return True

        # Detect the same 1-3 word phrase repeated many times.
        for size in (1, 2, 3):
            if len(words) < size * 4:
                continue
            chunks = [tuple(words[i:i + size]) for i in range(0, len(words) - size + 1, size)]
            if chunks and max(chunks.count(chunk) for chunk in set(chunks)) >= 4:
                return True
        return False

    @staticmethod
    def _looks_like_hallucination(results: list[dict[str, Any]]) -> bool:
        text = " ".join(item["text"] for item in results).strip()
        return MultilingualTranscriber._is_repetitive(text)

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
