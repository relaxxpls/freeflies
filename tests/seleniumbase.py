from seleniumbase import SB
from .config import BROWSER_PATH, EMAIL, GOOGLE_URL, PASSWORD, MEET_URL


def xpath_button_text(text: str | list[str]):
    if isinstance(text, str):
        return f'//button[span[contains(text(), "{text}")]]'
    contains = " or ".join([f'contains(text(), "{t}")' for t in text])
    return f"//button[span[{contains}]]"


xpath_button_aria_label = lambda label: f'//button[@aria-label="{label}"]'


def test():
    with SB(
        # test=True,
        # headless=True,
        chromium_arg="--auto-accept-camera-and-microphone-capture",
        disable_features="VizDisplayCompositor",
        undetectable=True,
        binary_location=BROWSER_PATH,
    ) as sb:
        sb.activate_cdp_mode(GOOGLE_URL)
        sb.cdp.grant_permissions(["audioCapture"])

        # sb.open(GOOGLE_URL)
        sb.sleep(5)

        sb.type("#identifierId", EMAIL, timeout=30)
        sb.click("#identifierNext", delay=2)
        sb.sleep(5)

        sb.type('#password input[type="password"]', PASSWORD, timeout=30)
        sb.click("#passwordNext", delay=2)
        sb.sleep(5)

        sb.open(MEET_URL)
        sb.sleep(5)

        sb.click(
            xpath_button_text(
                [
                    "Continue without microphone and camera",
                    "Continue without camera",
                    "Continue without microphone",
                ]
            ),
            timeout=30,
        )

        sb.click(xpath_button_text(["Ask to join", "Join now"]), timeout=30)

        sb.wait_for_element(xpath_button_aria_label("Leave call"))

        print("Successfully joined meeting")
        sb.sleep(40)
