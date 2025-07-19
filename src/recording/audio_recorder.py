from os import path
from queue import Queue, Empty
import threading
import numpy as np
import time
import logging
from typing import Optional, List
from datetime import datetime
import sounddevice as sd
import soundfile as sf

from ..config import SAMPLE_RATE, DOWNLOADS_DIRECTORY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioRecorder:
    """Audio recorder"""

    chunk_duration: float = 5.0  # seconds
    chunk_size: int = int(SAMPLE_RATE * chunk_duration)

    is_recording: bool = False
    start_time: Optional[float] = None
    output_file: Optional[str] = None
    audio_queue: Queue[np.ndarray] = Queue()
    recording_thread: Optional[threading.Thread] = None
    audio_data: List[np.ndarray] = []

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback function for audio recording"""
        if status:
            logger.warning(f"Audio callback status: {status}")

        if not self.is_recording:
            return

        # Add audio data to queue for real-time processing
        audio_chunk = indata.copy()
        self.audio_queue.put(audio_chunk)

        # Store audio data for full recording
        self.audio_data.append(audio_chunk)

    def _recording_worker(self):
        """Worker thread for audio recording"""
        try:
            logger.info("Starting audio recording worker")

            # Start recording stream - changed to InputStream for recording
            with sd.InputStream(
                # device=sd.default.device[1],
                channels=1,  # Force mono recording
                samplerate=SAMPLE_RATE,
                callback=self._audio_callback,
                blocksize=self.chunk_size,
                dtype=np.float32,
            ):
                while self.is_recording:
                    time.sleep(0.1)  # Small delay to prevent busy waiting

        except Exception as e:
            logger.error(f"Error in recording worker: {str(e)}")
            self.is_recording = False

    def start_recording(
        self,
        output_file: str = f"dummy_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
    ) -> bool:
        """Simulate starting recording"""
        try:
            if self.is_recording:
                raise Exception("Recording is already active")

            # Reset recording state
            self.output_file = path.join(DOWNLOADS_DIRECTORY, output_file)
            self.is_recording = True
            self.start_time = time.time()

            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._recording_worker, daemon=True
            )
            self.recording_thread.start()

            logger.info(f"Audio recording started - saving to: {self.output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}")
            return False

    def stop_recording(self) -> Optional[str]:
        try:
            """Stop audio recording and save the file"""
            if not self.is_recording:
                raise Exception("No active recording to stop")

            # Stop recording
            self.is_recording = False
            self.start_time = None

            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=5.0)
                self.recording_thread = None

            # Save audio data to file
            if not self.audio_data or not self.output_file:
                raise Exception("No audio data to save")

            # Concatenate all audio chunks
            full_audio = np.concatenate(self.audio_data, axis=0)

            # Save to file
            sf.write(self.output_file, full_audio, SAMPLE_RATE)

            logger.info(
                f"Recording saved: {self.output_file} (duration: {self.get_recording_duration():.2f}s)"
            )

            self.cleanup()

            return self.output_file

        except Exception as e:
            logger.error(f"Error stopping recording: {str(e)}")
            return None

    def is_queue_empty(self) -> bool:
        return self.audio_queue.qsize() == 0

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        try:
            return self.audio_queue.get_nowait()
        except Exception as e:
            if not isinstance(e, Empty):
                logger.error(f"Error getting audio chunk: {str(e)}")
            return None

    def get_recording_duration(self) -> float:
        return time.time() - self.start_time if self.start_time else 0.0

    def cleanup(self):
        """Cleanup"""

        # Clear audio queue
        self.audio_data = []
        while not self.audio_queue.empty():
            self.audio_queue.get_nowait()

        # TODO: maybe clear thread here?

    def __del__(self):
        self.cleanup()
