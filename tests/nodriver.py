import asyncio
import nodriver as uc
from .config import BROWSER_PATH, EMAIL, GOOGLE_URL, PASSWORD


async def _test():
    browser = await uc.start(
        headless=False,
        browser_executable_path=BROWSER_PATH,
        browser_args=[
            "--auto-accept-camera-and-microphone-capture"
            "--use-fake-ui-for-media-stream",  # Allow microphone access
            "--use-fake-device-for-media-stream",  # Use fake camera/mic
            "--disable-web-security",  # Disable some security features
            "--allow-running-insecure-content",  # Allow mixed content
            "--disable-features=VizDisplayCompositor",  # Improve performance
            "--no-sandbox",  # Needed for some environments
            "--disable-dev-shm-usage",  # Overcome limited resource problems
            "--disable-setuid-sandbox",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--noerrdialogs",
            "--disable-gpu",
        ],
    )

    page = await browser.get(GOOGLE_URL)
    await page.sleep(10)

    email_input = await page.select("#identifierId")
    await email_input.send_keys(EMAIL)

    next_input = await page.select("#identifierNext button")
    await next_input.click()
    await page.sleep(10)

    password_input = await page.select('input[name="Passwd"]')

    await password_input.send_keys(PASSWORD)

    next_input = await page.select("#passwordNext button")
    await next_input.click()

    await page.sleep(10)


def test():
    asyncio.run(_test())
