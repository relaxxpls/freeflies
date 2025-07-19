import os
from dotenv import load_dotenv

load_dotenv()

BROWSER_PATH = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

EMAIL = os.getenv("GOOGLE_EMAIL") or "test@test.com"
PASSWORD = os.getenv("GOOGLE_PASSWORD") or "test"
