import numpy as np
import logging
import time
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Transcriber:
    """Transcriber class"""

    def __init__(
        self, model_size: str = "base", language: str = "en", device: str = "auto"
    ):
        self.model_size = model_size
        self.language = language
        self.device = device
        self.is_loaded = True
        self.is_loading = False
        self.sample_rate = 16000

        self.dummy_responses = [
            "Hello, welcome to the meeting.",
            "Thank you for joining us today.",
            "Let's start with the agenda.",
            "The first item on our list is...",
            "Does anyone have questions?",
            "Moving on to the next topic.",
            "I think we can conclude this discussion.",
            "Thank you for your time.",
            "See you next time.",
            "Have a great day!",
        ]
        self.response_index = 0

    def transcribe_chunk(
        self, audio_chunk: np.ndarray, sample_rate: int = 44100
    ) -> Optional[str]:
        """Transcribe a chunk of audio"""
        if (
            audio_chunk is not None and len(audio_chunk) > sample_rate
        ):  # At least 1 second
            # Simulate processing time
            time.sleep(0.5)

            # Return dummy response
            text = self.dummy_responses[self.response_index % len(self.dummy_responses)]
            self.response_index += 1

            logger.info(f"Transcription: {text}")
            return text

        return None

    def transcribe_file(self, audio_file: str) -> Optional[Dict[str, Any]]:
        """Transcribe a file"""
        dummy_text = " ".join(self.dummy_responses)

        return {
            "text": dummy_text,
            "language": self.language,
            "segments": [],
            "duration": 60.0,
            "file_path": audio_file,
            "timestamp": datetime.now().isoformat(),
        }

    def transcribe_stream(
        self,
        audio_generator: Generator[np.ndarray, None, None],
        sample_rate: int = 44100,
    ) -> Generator[str, None, None]:
        """Transcribe a stream"""
        for audio_chunk in audio_generator:
            transcription = self.transcribe_chunk(audio_chunk, sample_rate)
            if transcription:
                yield transcription

    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]

    def change_language(self, language: str) -> bool:
        """Change language"""
        self.language = language
        logger.info(f"Changed language to {language}")
        return True

    def get_model_info(self) -> Dict[str, Any]:
        """Get model info"""
        return {
            "model_size": self.model_size,
            "language": self.language,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "is_loading": self.is_loading,
            "sample_rate": self.sample_rate,
        }

    def cleanup(self):
        """Cleanup"""
        logger.info("Transcriber cleanup completed")
