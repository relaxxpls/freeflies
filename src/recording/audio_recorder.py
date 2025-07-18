import numpy as np
import time
import logging
from typing import Optional, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioRecorder:
    """Audio recorder"""

    def __init__(
        self, sample_rate: int = 44100, channels: int = 2, chunk_duration: float = 2.0
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.is_recording = False
        self.start_time = None
        self.output_file = None

    def start_recording(self, output_file: Optional[str] = None) -> bool:
        """Simulate starting recording"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"dummy_recording_{timestamp}.wav"

        self.output_file = output_file
        self.is_recording = True
        self.start_time = time.time()
        logger.info(f"Recording started - {output_file}")
        return True

    def stop_recording(self) -> Optional[str]:
        """Simulate stopping recording"""
        if not self.is_recording:
            return None

        self.is_recording = False
        duration = time.time() - self.start_time if self.start_time else 0
        logger.info(
            f"Recording stopped - {self.output_file} (duration: {duration:.2f}s)"
        )
        return self.output_file

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Return dummy audio chunk"""
        if self.is_recording:
            # Return dummy audio data
            chunk_size = int(self.sample_rate * self.chunk_duration)
            dummy_audio = np.random.normal(0, 0.1, (chunk_size, self.channels))
            return dummy_audio
        return None

    def get_recording_duration(self) -> float:
        """Get dummy recording duration"""
        if self.start_time and self.is_recording:
            return time.time() - self.start_time
        return 0.0

    def get_audio_level(self) -> float:
        """Return dummy audio level"""
        if self.is_recording:
            return np.random.uniform(10, 80)  # Random level between 10-80%
        return 0.0

    def list_audio_devices(self) -> List[Tuple[int, str, int]]:
        """Return dummy device list"""
        return [
            (0, "Dummy Microphone", 2),
            (1, "Dummy System Audio", 2),
            (2, "Dummy Headset", 1),
        ]

    def set_input_device(self, device_id: int) -> bool:
        """Dummy device setting"""
        logger.info(f"Set input device to {device_id}")
        return True

    def cleanup(self):
        """Dummy cleanup"""
        logger.info("Audio recorder cleanup completed")
