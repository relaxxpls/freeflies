import streamlit as st
import threading
import time
from datetime import datetime, timedelta
import re

from src.bot.meet_bot import MeetBot
from src.recording.audio_recorder import AudioRecorder
from src.transcription.transcriber import Transcriber

# Configure Streamlit page
st.set_page_config(
    page_title="FreeFlies - Google Meet Recorder",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize session state variables"""
    if "recording_active" not in st.session_state:
        st.session_state.recording_active = False
    if "transcription_active" not in st.session_state:
        st.session_state.transcription_active = False

    if "transcription_text" not in st.session_state:
        st.session_state.transcription_text = ""
    if "meeting_history" not in st.session_state:
        st.session_state.meeting_history = []

    if "meet_bot" not in st.session_state:
        st.session_state.meet_bot = MeetBot()
    if "audio_recorder" not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()
    if "transcriber" not in st.session_state:
        st.session_state.transcriber = Transcriber()


def validate_meet_url(url: str) -> bool:
    """Validate if the provided URL is a valid Google Meet URL"""
    if not url:
        return False

    format = r"https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}\??.*"
    match = re.fullmatch(format, url)

    return bool(match)


def display_status(message: str, status_type: str = "info"):
    """Display status message with appropriate styling"""
    status_class = f"status-{status_type}"
    st.markdown(
        f'<div class="status-box {status_class}">{message}</div>',
        unsafe_allow_html=True,
    )


def start_recording(meet_url: str):
    """Start the recording process"""
    try:
        with st.spinner("Joining Google Meet..."):
            # Join the meeting
            joined = st.session_state.meet_bot.join_meeting(meet_url)
            if not joined:
                display_status("❌ Failed to join the meeting", "error")
                return False

            display_status("✅ Successfully joined the meeting!", "success")

            # Start recording
            started = st.session_state.audio_recorder.start_recording()
            if not started:
                display_status("❌ Failed to start recording", "error")
                return False

            st.session_state.recording_active = True
            display_status("🎙️ Recording started!", "success")

            # Start transcription in background
            threading.Thread(target=background_transcription, daemon=True).start()
            return True

    except Exception as e:
        display_status(f"❌ Error: {str(e)}", "error")
        return False


def background_transcription():
    """Background function for real-time transcription"""

    try:
        st.session_state.transcription_active = True

        while st.session_state.recording_active:
            if not st.session_state.recording_active:
                break

            time.sleep(2)  # Process every 2 seconds

            # Get audio chunk
            audio_chunk = st.session_state.audio_recorder.get_audio_chunk()
            if not audio_chunk:
                continue

                # Transcribe audio chunk
            transcription = st.session_state.transcriber.transcribe_chunk(audio_chunk)
            if not transcription:
                continue

            # Update transcription text
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_text = f"[{timestamp}] {transcription}\n"
            st.session_state.transcription_text += new_text

            # Force Streamlit to update
            st.rerun()
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
    finally:
        st.session_state.transcription_active = False


def stop_recording():
    """Stop the recording process"""
    try:
        st.session_state.recording_active = False
        audio_file = st.session_state.audio_recorder.stop_recording()
        st.session_state.meet_bot.leave_meeting()

        # Save meeting to history
        meeting_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "transcription": st.session_state.transcription_text,
            "audio_file": audio_file if "audio_file" in locals() else None,
        }
        st.session_state.meeting_history.append(meeting_data)

        display_status("🛑 Recording stopped and saved!", "success")
        return True

    except Exception as e:
        display_status(f"❌ Error stopping recording: {str(e)}", "error")
        return False


def main():
    """Main Streamlit application"""
    initialize_session_state()

    st.header("🎙️ FreeFlies - Google Meet Recorder")

    # Sidebar for controls
    with st.sidebar:
        st.header("📋 Controls")

        # URL Input
        meet_url = st.text_input(
            "Google Meet URL",
            placeholder="https://meet.google.com/abc-defg-hij",
            help="Enter the Google Meet URL you want to record",
            icon="🔗",
        )

        # Validate URL
        url_valid = validate_meet_url(meet_url)
        if meet_url and not url_valid:
            st.error("⚠️ Please enter a valid Google Meet URL")

        # Recording controls
        st.subheader("🎙️ Recording")

        if url_valid:
            if st.session_state.recording_active:
                if st.button(
                    "Stop Recording",
                    disabled=not st.session_state.recording_active,
                    type="secondary",
                    icon="⏹️",
                    use_container_width=True,
                ):
                    if stop_recording():
                        st.rerun()
            else:
                if st.button(
                    "Start Recording",
                    disabled=not url_valid or st.session_state.recording_active,
                    type="primary",
                    icon="▶️",
                    use_container_width=True,
                ):
                    if start_recording(meet_url):
                        st.rerun()

        # Status indicator
        if st.session_state.recording_active:
            st.success("🔴 Recording Active")
        else:
            st.info("⚪ Recording Inactive")

        if st.session_state.transcription_active:
            st.success("🔴 Transcription Active")
        else:
            st.info("⚪ Transcription Inactive")

        # Meeting history
        st.subheader("📚 Meeting History")
        if st.session_state.meeting_history:
            for i, meeting in enumerate(st.session_state.meeting_history):
                with st.expander(f"Meeting {i+1} - {meeting['timestamp']}"):
                    st.text_area(
                        "Transcription",
                        value=meeting["transcription"],
                        height=200,
                        key=f"history_{i}",
                    )
        else:
            st.info("No meetings recorded yet")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📝 Live Transcription")

        # Real-time transcription display
        if st.session_state.transcription_text:
            st.markdown(st.session_state.transcription_text)
        else:
            st.info("Start recording to see live transcription here...")

        # Download transcription
        if st.session_state.transcription_text:
            st.download_button(
                label="Save",
                icon="💾",
                data=st.session_state.transcription_text,
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
            )

    with col2:
        st.header("📊 Stats")

        # Show transcriber loading status
        if st.session_state.transcriber.is_loading:
            st.info("🔄 Loading transcriber model...")
        elif not st.session_state.transcriber.is_loaded:
            st.warning("⚠️ Transcriber not ready")

        if st.session_state.recording_active:
            # Live recording duration
            duration = st.session_state.audio_recorder.get_recording_duration()
            st.metric("Recording Duration", str(timedelta(seconds=duration)))

            # Estimate word count from transcription
            word_count = (
                len(st.session_state.transcription_text.split())
                if st.session_state.transcription_text
                else 0
            )
            st.metric("Words Transcribed", str(word_count))
        else:
            st.info("Start recording to see stats")


def start_streamlit():
    """Entry point for poetry start command"""
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()
