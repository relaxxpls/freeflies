from datetime import timedelta
import re
from src.transcription import DiarizationResult


def validate_meet_url(url: str) -> bool:
    """Validate if the provided URL is a valid Google Meet URL"""
    if not url:
        return False

    format = r"https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}\??.*"
    match = re.fullmatch(format, url)

    return bool(match)


def transcription_to_markdown(result: list[DiarizationResult]) -> str:
    """
    Format the transcription to markdown.

    Example output:
    ### Speaker 00 (0:08)
    - `0:08` I said she could stay with us, Marge, until she feels better.

    ### Speaker 01 (0:11)
    - `0:11` Of course she can.
    - `0:12` No, things won't be for long.
    """
    speaker_name = lambda speaker: speaker.title().replace("_", " ")
    format_time = lambda seconds: str(timedelta(seconds=int(seconds)))

    output = []
    current_speaker = None
    current_lines = []
    start_time = None

    for segment in result:
        speaker = segment.speaker
        timestamp = format_time(segment.start)
        text = segment.text.strip()

        if speaker != current_speaker:
            # Write previous speaker's block
            if current_speaker is not None:
                output.append(
                    f"### {speaker_name(current_speaker)} ({format_time(start_time)})"
                )
                output.extend([f"- `{ts}` {line}" for ts, line in current_lines])
                output.append("")  # Add space between speakers

            # Start new speaker block
            current_speaker = speaker
            start_time = segment.start
            current_lines = [(timestamp, text)]
        else:
            current_lines.append((timestamp, text))

    # Write final speaker block
    if current_speaker:
        output.append(
            f"### {speaker_name(current_speaker)} ({format_time(start_time)})"
        )
        output.extend([f"- `{ts}` {line}" for ts, line in current_lines])

    return "\n".join(output)
