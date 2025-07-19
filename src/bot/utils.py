import asyncio
from random import randint


def xpath_button_text(text: str | list[str]):
    if isinstance(text, str):
        return f'//button[span[contains(text(), "{text}")]]'
    contains = " or ".join([f'contains(text(), "{t}")' for t in text])
    return f"//button[span[{contains}]]"


xpath_button_aria_label = lambda label: f'//button[@aria-label="{label}"]'


async def sleep(seconds: int = 5):
    return await asyncio.sleep(seconds + randint(0, 1))
