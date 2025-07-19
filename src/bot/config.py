import os
from dotenv import load_dotenv

load_dotenv()

BROWSER_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
GOOGLE_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"

EMAIL = os.getenv("GOOGLE_EMAIL") or "test@test.com"
PASSWORD = os.getenv("GOOGLE_PASSWORD") or "test"
