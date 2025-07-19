import numpy as np
import torch
import logging
import threading
from typing import Optional, Generator, Any
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from transformers.pipelines import pipeline
from ..config import DEVICE, SAMPLE_RATE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Transcriber:
    """
    Transcriber class for converting audio to text using HuggingFace Transformers

    This class handles:
    - Real-time audio transcription using HuggingFace models
    - Multiple HuggingFace ASR model options
    - Language detection and translation
    """

    # Model settings
    model_name: str = "openai/whisper-base"  # or "openai/whisper-large-v3"
    language: str = "en"
    pipeline: Optional[Any] = None
    processor: Optional[Any] = None
    model: Optional[Any] = None

    is_loading: bool = False
    is_loaded: bool = False

    # Transcription settings
    chunk_length = 30  # seconds
    min_audio_length = 1.0  # minimum seconds of audio to transcribe

    def __init__(self):
        if self.is_loading or self.is_loaded:
            return

        try:
            self.is_loading = True
            logger.info(
                f"Loading HuggingFace model: {self.model_name} on device: {DEVICE}"
            )

            # Load model in a separate thread to avoid blocking
            def load_worker():
                try:
                    # Initialize HuggingFace ASR pipeline
                    self.pipeline = pipeline(
                        "automatic-speech-recognition",
                        model=self.model_name,
                        device=DEVICE,
                        torch_dtype=torch.float16,
                    )

                    # Also load processor and model separately for more control
                    self.processor = AutoProcessor.from_pretrained(self.model_name)
                    self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        low_cpu_mem_usage=True,
                        use_safetensors=True,
                    )

                    self.model.to(DEVICE)  # type: ignore

                    self.is_loaded = True
                    logger.info(f"HuggingFace model loaded successfully")
                except Exception as e:
                    logger.error(f"Failed to load HuggingFace model: {str(e)}")
                finally:
                    self.is_loading = False

            loading_thread = threading.Thread(target=load_worker, daemon=True)
            loading_thread.start()

        except Exception as e:
            logger.error(f"Error initializing model loading: {str(e)}")
            self.is_loading = False

    def _prepare_audio(self, audio: np.ndarray) -> np.ndarray:
        """Prepare audio (convert to 16kHz mono)"""
        try:
            # Convert to float32 if needed
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)

            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Resample to 16kHz if needed (HuggingFace models expect 16kHz)
            # if SAMPLE_RATE != 16000:
            #     audio = librosa.resample(audio, orig_sr=SAMPLE_RATE, target_sr=16000)

            # Normalize audio
            audio = audio / (np.max(np.abs(audio)) + 1e-8)

            return audio

        except Exception as e:
            logger.error(f"Error preparing audio: {str(e)}")
            return audio

    def transcribe_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        try:
            if not self.pipeline or not self.is_loaded:
                return None

            # Check minimum audio length
            duration = len(audio_chunk) / SAMPLE_RATE
            if duration < self.min_audio_length:
                return None

            # Prepare audio
            audio = self._prepare_audio(audio_chunk)

            # Transcribe using HuggingFace pipeline
            result = self.pipeline(
                audio,
                return_timestamps=False,
                generate_kwargs={
                    "language": self.language,
                    "task": "transcribe",
                },
            )

            text = result["text"]
            print("text", text)  #  remove
            if not isinstance(text, str):
                raise Exception("Transcribed text is not a string")
            text = text.strip()

            if text and len(text) > 0:
                logger.debug(f"Transcribed: {text}")
                return text

            return None

        except Exception as e:
            logger.error(f"Error transcribing chunk: {str(e)}")
            return None

    def transcribe_stream(
        self,
        audio_generator: Generator[np.ndarray, None, None],
    ) -> Generator[str, None, None]:
        """
        Transcribe audio stream in real-time

        Args:
            audio_generator: Generator that yields audio chunks

        Yields:
            str: Transcribed text chunks
        """
        try:
            if not self.model or not self.is_loaded:
                return

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

            if self.model:
                del self.model
                self.model = None

            if self.processor:
                del self.processor
                self.processor = None

            # Clear GPU memory if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.is_loaded = False
            logger.info("Transcriber cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
