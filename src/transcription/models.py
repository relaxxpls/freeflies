from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class DiarizationResult(BaseModel):
    """Model for diarization result"""

    text: str = Field(description="The transcribed text")
    speaker: str = Field(description="Speaker of the transcription")
    start: float = Field(description="Start time of the transcription in seconds", ge=0)
    end: float = Field(description="End time of the transcription in seconds", ge=0)


class MeetingSummary(BaseModel):
    """Model for meeting summary output"""

    summary: str = Field(description="Comprehensive summary of the meeting")
    action_items: List[str] = Field(default=[], description="Action items")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="When the summary was generated",
    )
    word_count: int = Field(default=0, description="Original transcription word count")
