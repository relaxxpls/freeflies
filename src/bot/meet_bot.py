import asyncio
import os
from typing import Optional
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetBot:
    """MeetBot class for interacting with Google Meet"""

    is_joined = False
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    playwright: Optional[Playwright] = None

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

    async def _login(self):
        """Login to Google"""

        if self.page is None:
            await self._setup_browser()
            assert self.page is not None

        GMEET_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"
        EMAIL = os.getenv("GOOGLE_EMAIL")
        PASSWORD = os.getenv("GOOGLE_PASSWORD")

        if not EMAIL or not PASSWORD:
            raise ValueError(
                "GOOGLE_EMAIL and GOOGLE_PASSWORD environment variables must be set"
            )

        await self.page.goto(GMEET_URL)

        # Enter email
        await self.page.fill("#identifierId", EMAIL)
        await self.page.click("#identifierNext")
        await self.page.wait_for_selector("#password", timeout=10000)

        # Enter password
        await self.page.fill('#password input[type="password"]', PASSWORD)
        await self.page.click("#passwordNext")
        await self.page.wait_for_load_state("networkidle")

        logger.info("Google login activity: Done")

    async def _join_meeting_async(self, meet_url: str):
        """Login and join a meeting asynchronously"""

        if self.page is None:
            await self._setup_browser()
            assert self.page is not None

        await self._login()

        await self.page.goto(meet_url)
        button = await self.page.query_selector('button:has(span:text("Ask to join"))')
        if button:
            await button.wait_for_element_state("visible")
            await button.click()
        else:
            raise Exception("Button not found")

        await self.page.wait_for_load_state("networkidle")
        logger.info("Successfully joined meeting")

    def join_meeting(self, meet_url: str) -> bool:
        """Join a meeting synchronously"""
        try:
            logger.info(f"Joining meeting at {meet_url}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._join_meeting_async(meet_url))
            self.is_joined = True
            logger.info("Successfully joined meeting")

            return True
        except Exception as e:
            logger.error(f"Error joining meeting: {str(e)}")
            return False

    def leave_meeting(self) -> bool:
        """Leave a meeting"""
        logger.info("Leaving meeting")
        self.is_joined = False
        logger.info("Successfully left meeting")
        return True

    def cleanup(self):
        """Cleanup"""
        logger.info("Cleanup completed")
        pass
