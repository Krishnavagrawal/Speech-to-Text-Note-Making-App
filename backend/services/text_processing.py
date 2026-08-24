import re


COMMON_SPEECH_CORRECTIONS = {
    "jappur": "Jaipur",
    "japur": "Jaipur",
    "jaypur": "Jaipur",
    "jaipore": "Jaipur",
    "jaffa": "Jaipur",
    "manifal": "Manipal",
    "hatras": "Hathras",
    "manipal university jappur": "Manipal University Jaipur",
    "manipal university japur": "Manipal University Jaipur",
    "manipal university jaffa": "Manipal University Jaipur",
    "manifal university jaffa": "Manipal University Jaipur",
    "manipal university, jaffa": "Manipal University, Jaipur",
    "manifal university, jaffa": "Manipal University, Jaipur",
    "krishna o guru val": "Krishna Vagraval",
}


def clean_transcript(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def correct_transcript(text: str) -> str:
    corrected = text
    for incorrect, replacement in sorted(COMMON_SPEECH_CORRECTIONS.items(), key=lambda item: -len(item[0])):
        corrected = re.sub(rf"\b{re.escape(incorrect)}\b", replacement, corrected, flags=re.IGNORECASE)
    return corrected
