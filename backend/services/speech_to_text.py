from collections.abc import Iterator
from typing import Any


def collect_segments(segments: Iterator[Any]) -> str:
    return " ".join(segment.text.strip() for segment in segments).strip()


def transcribe_audio(model: Any, file_path: str) -> tuple[str, Any]:
    segments, info = model.transcribe(
        file_path,
        task="transcribe",
        beam_size=5,
    )
    return collect_segments(segments), info
