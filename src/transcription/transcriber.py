import logging
from typing import Generator, List

import numpy as np
import torch
from whisperx.alignment import align, load_align_model
from whisperx.asr import load_model
from whisperx.diarize import DiarizationPipeline, assign_word_speakers

from src.config import CACHE_DIR

from .models import DiarizationResult

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Transcriber class for transcribing audio streams.
    """

    batch_size = 16
    device = "cuda" if torch.cuda.is_available() else "cpu"
    language = "en"

    def __init__(self):
        logger.info(f"Transcriber initializing on {self.device}")
        self.pipeline = load_model(
            "large-v3-turbo",
            device=self.device,
            compute_type="float16",
            language=self.language,
            download_root=f"{CACHE_DIR}/whisper",
        )
        self.align_model, self.align_metadata = load_align_model(
            language_code=self.language, device=self.device
        )
        self.diarize_model = DiarizationPipeline(device=self.device)

    def transcribe_chunk(
        self, audio: np.ndarray, time_offset: float = 0.0
    ) -> List[DiarizationResult]:
        try:
            transcribed_result = self.pipeline.transcribe(
                audio, batch_size=self.batch_size
            )

            aligned_result = align(
                transcribed_result["segments"],
                self.align_model,
                self.align_metadata,
                audio,
                self.device,
            )
            diarize_df = self.diarize_model(audio, self.batch_size)
            diarized_result = assign_word_speakers(diarize_df, aligned_result)

            result_list = [
                DiarizationResult(
                    text=segment["text"],
                    speaker=segment["speaker"],
                    start=segment["start"] + time_offset,  # Add time offset
                    end=segment["end"] + time_offset,  # Add time offset
                )
                for segment in diarized_result["segments"]
            ]

            return result_list
        except Exception as e:
            logger.error(f"Error transcribing chunk: {str(e)}")
            return None

    def transcribe_stream(
        self,
        audio_generator: Generator[np.ndarray, None, None],
    ) -> Generator[List[DiarizationResult], None, None]:
        """
        Transcribe audio stream in real-time

        Args:
            audio_generator: Generator that yields audio chunks

        Yields:
            List[DiarizationResult]: Transcribed and diarized results
        """
        try:
            logger.info("Starting stream transcription")

            for audio_chunk in audio_generator:
                if audio_chunk is not None:
                    transcription = self.transcribe_chunk(audio_chunk)
                    if transcription:
                        yield transcription

        except Exception as e:
            logger.error(f"Error in stream transcription: {str(e)}")

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.pipeline:
                del self.pipeline
                self.pipeline = None

            if self.align_model:
                del self.align_model
                self.align_model = None

            if self.align_metadata:
                del self.align_metadata
                self.align_metadata = None

            if self.diarize_model:
                del self.diarize_model
                self.diarize_model = None

            # Clear GPU memory if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Transcriber cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
