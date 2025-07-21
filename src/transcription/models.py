from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, field_validator


class TranscriptionEntry(BaseModel):
    """Model for individual transcription entries"""

    text: str = Field(min_length=1, description="The transcribed text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%H:%M:%S"),
        description="Timestamp of the transcription",
    )

    @field_validator("text")
    def text_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("Text cannot be empty or only whitespace")
        return v.strip()


class MeetingSummary(BaseModel):
    """Model for meeting summary output"""

    summary: str = Field(description="Comprehensive summary of the meeting")
    action_items: List[str] = Field(default=[], description="Action items")
    generated_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="When the summary was generated",
    )
    word_count: int = Field(default=0, description="Original transcription word count")
