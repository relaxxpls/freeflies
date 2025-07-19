import numpy as np
import torch
import logging
import threading
from typing import Optional, Generator, Any
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
from transformers.pipelines import pipeline
from ..config import (
    DEVICE,
    SAMPLE_RATE,
    VAD_ENERGY_THRESHOLD,
    VAD_SILENCE_THRESHOLD,
    VAD_MIN_SPEECH_DURATION,
    VAD_MAX_REPETITION_RATIO,
    VAD_MIN_AUDIO_LENGTH,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Transcriber:
    """
    Transcriber class for converting audio to text using HuggingFace Transformers

    This class handles:
    - Real-time audio transcription using HuggingFace models
    - Voice activity detection to prevent hallucination
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

    def _has_voice_activity(self, audio: np.ndarray) -> bool:
        """
        Detect if audio contains voice activity using energy-based VAD

        Args:
            audio: Audio array to analyze

        Returns:
            bool: True if voice activity is detected, False otherwise
        """
        try:
            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(audio**2))

            # Check if energy exceeds threshold
            if rms_energy < VAD_ENERGY_THRESHOLD:
                logger.debug(
                    f"Low energy detected: {rms_energy:.6f} < {VAD_ENERGY_THRESHOLD}"
                )
                return False

            # Calculate zero crossing rate (indicator of speech vs noise)
            zero_crossings = np.sum(np.diff(np.signbit(audio)))
            zero_crossing_rate = zero_crossings / len(audio)

            # Speech typically has ZCR between 0.01 and 0.35
            if zero_crossing_rate < 0.001 or zero_crossing_rate > 0.5:
                logger.debug(f"Abnormal zero crossing rate: {zero_crossing_rate:.6f}")
                return False

            # Check for silence percentage
            silence_samples = np.sum(np.abs(audio) < VAD_ENERGY_THRESHOLD * 0.1)
            silence_ratio = silence_samples / len(audio)

            if silence_ratio > VAD_SILENCE_THRESHOLD:
                logger.debug(
                    f"Too much silence: {silence_ratio:.2f} > {VAD_SILENCE_THRESHOLD}"
                )
                return False

            # Calculate spectral centroid (frequency distribution indicator)
            # Simple approximation using FFT
            if len(audio) > 256:  # Minimum samples for meaningful FFT
                fft = np.abs(np.fft.rfft(audio))
                freqs = np.fft.rfftfreq(len(audio), 1 / SAMPLE_RATE)

                # Calculate spectral centroid
                if np.sum(fft) > 0:
                    spectral_centroid = np.sum(freqs * fft) / np.sum(fft)
                    # Speech typically has spectral centroid between 500-4000 Hz
                    if spectral_centroid < 200 or spectral_centroid > 8000:
                        logger.debug(
                            f"Unusual spectral centroid: {spectral_centroid:.1f} Hz"
                        )
                        return False

            logger.debug(
                f"Voice activity detected - Energy: {rms_energy:.6f}, ZCR: {zero_crossing_rate:.6f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error in voice activity detection: {str(e)}")
            # On error, be conservative and assume there might be voice activity
            return True

    def _detect_hallucination(self, text: str) -> bool:
        """
        Detect potential hallucination in transcribed text

        Args:
            text: Transcribed text to analyze

        Returns:
            bool: True if hallucination is detected, False otherwise
        """
        try:
            if not text or len(text.strip()) < 3:
                return True

            words = text.lower().split()
            if len(words) < 2:
                return False

            # Check for excessive repetition
            word_count = {}
            for word in words:
                word_count[word] = word_count.get(word, 0) + 1

            # Find most repeated word
            max_repetitions = max(word_count.values())
            repetition_ratio = max_repetitions / len(words)

            if repetition_ratio > VAD_MAX_REPETITION_RATIO:
                logger.debug(f"Excessive repetition detected: {repetition_ratio:.2f}")
                return True

            # Check for suspiciously long sequences of repeated short words
            consecutive_repeats = 0
            max_consecutive = 0
            prev_word = ""

            for word in words:
                if word == prev_word and len(word) <= 4:  # Short words repeated
                    consecutive_repeats += 1
                    max_consecutive = max(max_consecutive, consecutive_repeats)
                else:
                    consecutive_repeats = 0
                prev_word = word

            if max_consecutive > 5:
                logger.debug(f"Long consecutive repetition detected: {max_consecutive}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error in hallucination detection: {str(e)}")
            return False

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
            if duration < VAD_MIN_AUDIO_LENGTH:
                logger.debug(
                    f"Audio chunk too short: {duration:.2f}s < {VAD_MIN_AUDIO_LENGTH}s"
                )
                return None

            # Prepare audio
            audio = self._prepare_audio(audio_chunk)

            # Voice Activity Detection - skip transcription if no voice detected
            if not self._has_voice_activity(audio):
                logger.debug("No voice activity detected, skipping transcription")
                return None

            # Check for minimum speech duration within the chunk
            # Calculate number of samples that should contain speech
            min_speech_samples = int(VAD_MIN_SPEECH_DURATION * SAMPLE_RATE)
            speech_samples = np.sum(np.abs(audio) > VAD_ENERGY_THRESHOLD * 0.5)

            if speech_samples < min_speech_samples:
                logger.debug(
                    f"Insufficient speech content: {speech_samples} < {min_speech_samples}"
                )
                return None

            # Transcribe using HuggingFace pipeline
            result = self.pipeline(
                audio,
                return_timestamps=False,
                generate_kwargs={
                    "language": self.language,
                    "task": "transcribe",
                    "max_new_tokens": 100,  # Limit output length to prevent long hallucinations
                    "num_beams": 1,  # Use greedy decoding for faster, more consistent results
                    "do_sample": False,  # Disable sampling to reduce randomness
                },
            )

            text = result["text"]
            if not isinstance(text, str):
                raise Exception("Transcribed text is not a string")
            text = text.strip()

            # Skip empty or very short results
            if not text or len(text) < 3:
                logger.debug("Transcription result too short or empty")
                return None

            # Detect and filter out hallucinations
            if self._detect_hallucination(text):
                logger.debug(f"Hallucination detected, filtering out: '{text[:50]}...'")
                return None

            if text and len(text) > 0:
                logger.info(f"Transcribed: {text}")
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
