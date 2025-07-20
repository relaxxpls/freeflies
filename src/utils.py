import re
from typing import List
from src.transcription.models import TranscriptionEntry


def validate_meet_url(url: str) -> bool:
    """Validate if the provided URL is a valid Google Meet URL"""
    if not url:
        return False

    format = r"https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}\??.*"
    match = re.fullmatch(format, url)

    return bool(match)


def get_transcription_text(
    transcription: List[TranscriptionEntry], timestamp: bool = False
):
    if timestamp:
        return "\n".join([f"[{t.timestamp}] {t.text}" for t in transcription]).strip()
    return " ".join([t.text for t in transcription]).strip()
