import asyncio
import time
from typing import Optional, Dict, Any
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetBot:
    """MeetBot class for interacting with Google Meet"""

    is_joined = False
    meeting_url = None
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    playwright: Optional[Playwright] = None

    # def __init__(self):
    #     self._setup_browser()

    async def _setup_browser(self):
        """Initialize browser and context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                "--use-fake-ui-for-media-stream",  # Allow microphone access
                "--use-fake-device-for-media-stream",  # Use fake camera/mic
                "--disable-web-security",  # Disable some security features
                "--allow-running-insecure-content",  # Allow mixed content
                "--disable-features=VizDisplayCompositor",  # Improve performance
                "--no-sandbox",  # Needed for some environments
                "--disable-dev-shm-usage",  # Overcome limited resource problems
            ],
        )
        self.context = await self.browser.new_context(
            permissions=["microphone", "camera"],
            # viewport={"width": 1280, "height": 720},
        )
        self.page = await self.context.new_page()

        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        await self.page.set_extra_http_headers({"User-Agent": user_agent})

    async def _login_async(self) -> bool:
        assert self.page is not None
        GMEET_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"
        await self.page.goto(GMEET_URL)
        await self.page.wait_for_selector("input[name='identifier']")
        await self.page.fill("input[name='identifier']", "fijit.club@gmail.com")
        await self.page.click("button[type='submit']")
        await self.page.wait_for_selector("input[name='password']")
        await self.page.fill("input[name='password']", "1234567890")
        await self.page.click("button[type='submit']")

    async def _join_meeting_async(self, meet_url: str) -> bool:
        """Join a meeting"""
        await self.page.goto(meet_url)
        await self.page.wait_for_selector("button:has-text('Join')")
        await self.page.click("button:has-text('Join')")

    def join_meeting(self, meet_url: str) -> bool:
        """Simulate joining a meeting"""
        logger.info(f"Dummy: Joining meeting at {meet_url}")
        time.sleep(2)  # Simulate loading time
        self.meeting_url = meet_url
        self.is_joined = True
        logger.info("Dummy: Successfully joined meeting")
        return True

    def leave_meeting(self) -> bool:
        """Simulate leaving a meeting"""
        logger.info("Dummy: Leaving meeting")
        self.is_joined = False
        logger.info("Dummy: Successfully left meeting")
        return True

    def cleanup(self):
        """Dummy cleanup"""
        logger.info("Dummy: Cleanup completed")
        pass

    def get_meeting_info(self) -> Dict[str, Any]:
        """Get dummy meeting info"""
        return {
            "is_joined": self.is_joined,
            "meeting_url": self.meeting_url,
            "browser_active": False,
            "page_active": False,
        }
