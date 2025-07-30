def xpath_button_text(text: str | list[str]):
    if isinstance(text, str):
        text = [text]
    contains = " or ".join([f'contains(text(), "{t}")' for t in text])
    return f"//button[span[{contains}]]"


def xpath_button_aria_label(label: str):
    return f'//button[@aria-label="{label}"]'
