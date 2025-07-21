from contextlib import _GeneratorContextManager
from time import time
from typing import Optional
from seleniumbase import SB, BaseCase
import logging

from ..config import GOOGLE_EMAIL, GOOGLE_URL, GOOGLE_PASSWORD
from .utils import xpath_button_aria_label, xpath_button_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeetBot:
    """MeetBot class for interacting with Google Meet"""

    is_joined = False
    sb: Optional[BaseCase] = None
    context: Optional[_GeneratorContextManager[BaseCase]] = None

    def join_meeting(self, meet_url: str) -> bool:
        """Join a meeting synchronously"""
        try:
            logger.info(f"Joining meeting at {meet_url}")
            self._join_meeting(meet_url)
            self.is_joined = True
            logger.info("Successfully joined meeting")

            return True
        except Exception as e:
            if self.sb:
                self.sb.save_screenshot(f".temp/screenshots/join - {time()}.png")
            logger.error(f"Error joining meeting:", e)
            self.cleanup()
            return False

    def leave_meeting(self) -> bool:
        """Leave a meeting"""
        try:
            logger.info("Leaving meeting")
            assert self.sb is not None
            self.sb.click(xpath_button_aria_label("Leave call"), timeout=180, delay=2)
            self.cleanup()
            self.is_joined = False
            logger.info("Successfully left meeting")

            return True
        except Exception as e:
            logger.error(f"Error leaving meeting:", e)
            return False

    def _setup_browser(self) -> bool:
        """Setup browser and context and logs in if needed"""

        self.context = SB(
            # test=True,
            # headless=True,
            xvfb=True,
            chromium_arg="--auto-accept-camera-and-microphone-capture",
            disable_features="VizDisplayCompositor",
            undetectable=True,
            # user_data_dir="./.temp/user_data",
        )
        self.sb = self.context.__enter__()

        self.sb.activate_cdp_mode(GOOGLE_URL)
        # self.sb.cdp.grant_permissions(["audioCapture"])
        self.sb.sleep(5)

        requires_login = not self._is_logged_in()
        if requires_login:
            self._login()
        else:
            logger.info("Already logged in")

        assert self._is_logged_in()

        return requires_login

    def _login(self):
        """Login to Google"""

        logger.info("Logging in...")
        assert self.sb is not None

        self.sb.type("#identifierId", GOOGLE_EMAIL, timeout=30)
        self.sb.click("#identifierNext", delay=2)
        self.sb.sleep(5)

        self.sb.type('#password input[type="password"]', GOOGLE_PASSWORD, timeout=30)
        self.sb.click("#passwordNext", delay=2)
        self.sb.sleep(5)

        logger.info("Google login activity: Done")

    def _is_logged_in(self) -> bool:
        """Check if user is logged in"""
        if self.sb is None:
            return False

        try:
            self.sb.wait_for_element('//span[text()="Sign in"]', timeout=5)
            return False
        except:
            pass
        title = self.sb.get_title()
        return isinstance(title, str) and "Google Workspace" not in title

    def _join_meeting(self, meet_url: str):
        """Login and join a meeting asynchronously"""

        if self.sb is None:
            self._setup_browser()
            assert self.sb is not None

        self.sb.open(meet_url)
        self.sb.sleep(5)

        try:
            continue_xpath = xpath_button_text(
                ["Continue without camera", "Continue without camera and microphone"]
            )
            self.sb.click(continue_xpath, delay=2)
        except:
            pass

        join_xpath = xpath_button_text(["Ask to join", "Join now"])
        self.sb.click(join_xpath, timeout=30, delay=2)

        logger.info("Waiting to join meeting...")

        # ? wait till leave button is visible
        self.sb.wait_for_element(xpath_button_aria_label("Leave call"), timeout=180)

        logger.info("Successfully joined meeting")

    def cleanup(self):
        """Cleanup"""

        if self.context:
            self.context.__exit__(None, None, None)
            self.context = None
            self.sb = None

        logger.info("Cleanup completed")

    def __del__(self):
        self.cleanup()
