from seleniumbase import SB
from .config import BROWSER_PATH, EMAIL, GOOGLE_URL, PASSWORD


def test():
    with SB(
        test=True,
        undetectable=True,
        binary_location=BROWSER_PATH,
    ) as sb:
        sb.open(GOOGLE_URL)
        sb.sleep(10)

        sb.type("#identifierId", EMAIL)
        sb.click("#identifierNext")
        sb.sleep(10)

        sb.type('#password input[type="password"]', PASSWORD)
        sb.click("#passwordNext")
        sb.sleep(10)
