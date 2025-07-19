from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"
BROWSER_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

EMAIL = os.getenv("GOOGLE_EMAIL") or "test@test.com"
PASSWORD = os.getenv("GOOGLE_PASSWORD") or "test"
