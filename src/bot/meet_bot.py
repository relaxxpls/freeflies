import asyncio
from typing import Optional
import mycdp
from seleniumbase import cdp_driver
import logging

from seleniumbase.undetected.cdp_driver.browser import Browser
from seleniumbase.undetected.cdp_driver.tab import Tab
from .config import BROWSER_PATH, EMAIL, PASSWORD
from .utils import xpath_button_aria_label, xpath_button_text, sleep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetBot:
    """MeetBot class for interacting with Google Meet"""

    is_joined = False
    browser: Optional[Browser] = None
    page: Optional[Tab] = None

    def join_meeting(self, meet_url: str) -> bool:
        """Join a meeting synchronously"""
        try:
            logger.info(f"Joining meeting at {meet_url}")
            asyncio.run(self._join_meeting_async(meet_url))
            self.is_joined = True
            logger.info("Successfully joined meeting")

            return True
        except Exception as e:
            logger.error(f"Error joining meeting:", e)
            asyncio.run(self.cleanup())
            return False

    def leave_meeting(self) -> bool:
        """Leave a meeting"""
        try:
            logger.info("Leaving meeting")
            asyncio.run(self._leave_meeting_async())
            self.is_joined = False
            logger.info("Successfully left meeting")

            return True
        except Exception as e:
            logger.error(f"Error leaving meeting:", e)
            return False

    async def _setup_browser(self):
        """Setup browser and context and logs in if needed"""

        self.browser = await cdp_driver.start_async(
            headless=False,
            browser_executable_path=BROWSER_PATH,
            browser_args=[
                "--user-data-dir=./.temp/user_data",
                "--auto-accept-camera-and-microphone-capture",
            ],
        )
        await self.browser.grant_permissions(["audioCapture"])

        GOOGLE_URL = "https://accounts.google.com/ServiceLogin?ltmpl=meet&continue=https://meet.google.com?hs=193&ec=wgc-meet-hero-signin"
        self.page = await self.browser.get(GOOGLE_URL)
        await sleep(5)

        if not self._is_logged_in():
            await self._login()

        assert self._is_logged_in()

    async def _login(self):
        """Login to Google"""

        assert self.page is not None

        email_input = await self.page.select("#identifierId")
        await email_input.send_keys_async(EMAIL)
        await sleep(2)
        next_input = await self.page.select("#identifierNext button")
        await next_input.click_async()
        await sleep(5)

        password_input = await self.page.select('input[name="Passwd"]')
        await password_input.send_keys_async(PASSWORD)
        await sleep(2)
        next_input = await self.page.select("#passwordNext button")
        await next_input.click_async()
        await sleep(10)

        logger.info("Google login activity: Done")

    def _is_logged_in(self) -> bool:
        """Check if user is logged in"""
        is_logged_in = (
            self.page is not None
            and isinstance(self.page.url, str)
            and "https://meet.google.com" in self.page.url
        )
        print("self.page.url", self.page.url)
        # assert self.page
        # print("self.page.url", self.page.target)
        # print("self.", self.page.target.url)
        # print("IS LOGGED IN", is_logged_in)
        # is_logged_in = True

        return is_logged_in

    async def _join_meeting_async(self, meet_url: str):
        """Login and join a meeting asynchronously"""

        if self.page is None:
            await self._setup_browser()
            assert self.page is not None

        self.page = await self.page.get(meet_url)
        await sleep(5)

        continue_button = await self.page.find_element_by_text(
            xpath_button_text(
                [
                    "Continue without microphone and camera",
                    "Continue without camera",
                    "Continue without microphone",
                ]
            ),
            # timeout=30,
        )
        print("CONTINUE BUTTON", continue_button)
        if continue_button:
            await continue_button.click_async()

        await sleep(5)

        button = await self.page.select(xpath_button_text(["Ask to join", "Join now"]))
        await button.click_async()

        logger.info("Waiting to join meeting...")

        # ? wait till leave button is visible
        await self.page.wait_for(xpath_button_aria_label("Leave call"), timeout=180)

        logger.info("Successfully joined meeting")

    async def _leave_meeting_async(self):
        """Leave a meeting asynchronously"""

        assert self.page is not None
        # aria-label="Leave call"
        leave_button = await self.page.select('button:has(aria-label="Leave call")')
        await leave_button.click_async()

        await self.cleanup()

    async def cleanup(self):
        """Cleanup"""

        if self.page:
            await self.page.close()
            self.page = None

        if self.browser:
            self.browser.stop()
            self.browser = None

        logger.info("Cleanup completed")
