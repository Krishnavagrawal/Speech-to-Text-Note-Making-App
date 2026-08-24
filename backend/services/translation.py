from typing import Any

from .speech_to_text import collect_segments


def translate_audio(model: Any, file_path: str) -> str:
    segments, _ = model.transcribe(
        file_path,
        task="translate",
        beam_size=5,
    )
    return collect_segments(segments)
