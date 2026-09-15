from __future__ import annotations

from statistics import mean


def build_transcription_report(segments: list[dict], detected_languages: list[str] | None = None) -> dict:
    """Build a report from actual Whisper segment metadata.

    The displayed percentage is an estimated confidence indicator, not a formal
    speech-recognition accuracy/WER measurement. Never invent 85% when metadata is
    unavailable.
    """
    confidence_values = []
    word_count = 0
    for segment in segments:
        text = str(segment.get("text") or "").strip()
        if text:
            word_count += len(text.split())
        confidence = segment.get("confidence")
        if isinstance(confidence, (int, float)):
            confidence_values.append(max(0.0, min(1.0, float(confidence))))

    confidence_score = mean(confidence_values) if confidence_values else 0.0
    accuracy_percent = round(max(0.0, min(100.0, confidence_score * 100.0)), 2)

    return {
        "confidence_score": round(confidence_score, 4),
        "accuracy_percent": accuracy_percent,
        "language_count": len(detected_languages or []),
        "word_count": word_count,
        "segments_processed": len(segments or []),
        "report_generated": True,
        "report_note": "Estimated confidence from Whisper segment metadata; this is not a formal WER-based accuracy score.",
    }
