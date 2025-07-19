import torch
from dotenv import load_dotenv
from os import path, getenv

load_dotenv()

# Bot settings
BROWSER_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
GOOGLE_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"

GOOGLE_EMAIL = getenv("GOOGLE_EMAIL") or "test@test.com"
GOOGLE_PASSWORD = getenv("GOOGLE_PASSWORD") or "test"

# Transcription settings
DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available() else "cpu"
)

SAMPLE_RATE = 16000  # Whisper expects 16kHz

DOWNLOADS_DIRECTORY = path.join(path.dirname(__file__), "../.temp/audio")
