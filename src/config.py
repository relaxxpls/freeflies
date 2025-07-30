from os import getenv, path

from dotenv import load_dotenv

load_dotenv()

# Bot settings
GOOGLE_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"

GOOGLE_EMAIL = getenv("GOOGLE_EMAIL", "test@test.com")
GOOGLE_PASSWORD = getenv("GOOGLE_PASSWORD", "test")
TOTP_SECRET = getenv("TOTP_SECRET", "random")

SAMPLE_RATE = 16000  # Whisper expects 16kHz

CACHE_DIR = path.join(path.dirname(__file__), "../.temp")
