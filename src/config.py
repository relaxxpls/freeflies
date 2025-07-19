import torch
from dotenv import load_dotenv
from os import path, getenv

load_dotenv()

# Bot settings
BROWSER_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
GOOGLE_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"

GOOGLE_EMAIL = getenv("GOOGLE_EMAIL", "test@test.com")
GOOGLE_PASSWORD = getenv("GOOGLE_PASSWORD", "test")

# Transcription settings
DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)

SAMPLE_RATE = 16000  # Whisper expects 16kHz

# Voice Activity Detection (VAD) settings
VAD_ENERGY_THRESHOLD = 0.01  # Minimum energy for speech
VAD_SILENCE_THRESHOLD = 0.5  # Max silence percentage
VAD_MIN_SPEECH_DURATION = 0.5  # Min speech duration in seconds
VAD_MAX_REPETITION_RATIO = 0.3  # Max word repetition ratio
VAD_MIN_AUDIO_LENGTH = 2.0

DOWNLOADS_DIRECTORY = path.join(path.dirname(__file__), "../.temp/audio")
