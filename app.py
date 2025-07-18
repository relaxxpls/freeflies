import streamlit as st
import threading
import time
from datetime import datetime
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
    if "transcription_text" not in st.session_state:
        st.session_state.transcription_text = ""
    if "meet_bot" not in st.session_state:
        st.session_state.meet_bot = None
    if "audio_recorder" not in st.session_state:
        st.session_state.audio_recorder = None
    if "transcriber" not in st.session_state:
        st.session_state.transcriber = None
    if "meeting_history" not in st.session_state:
        st.session_state.meeting_history = []


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
        # Initialize components
        st.session_state.meet_bot = MeetBot()
        st.session_state.audio_recorder = AudioRecorder()
        st.session_state.transcriber = Transcriber()

        # Join the meeting
        with st.spinner("Joining Google Meet..."):
            if st.session_state.meet_bot.join_meeting(meet_url):
                display_status("✅ Successfully joined the meeting!", "success")

                # Start recording
                if st.session_state.audio_recorder.start_recording():
                    st.session_state.recording_active = True
                    display_status("🎙️ Recording started!", "success")

                    # Start transcription in background
                    threading.Thread(
                        target=background_transcription, daemon=True
                    ).start()

                    return True
                else:
                    display_status("❌ Failed to start recording", "error")
                    return False
            else:
                display_status("❌ Failed to join the meeting", "error")
                return False

    except Exception as e:
        display_status(f"❌ Error: {str(e)}", "error")
        return False


def background_transcription():
    """Background function for real-time transcription"""
    try:
        while st.session_state.recording_active:
            if st.session_state.audio_recorder and st.session_state.transcriber:
                # Get audio chunk
                audio_chunk = st.session_state.audio_recorder.get_audio_chunk()

                if audio_chunk:
                    # Transcribe audio chunk
                    transcription = st.session_state.transcriber.transcribe_chunk(
                        audio_chunk
                    )

                    if transcription:
                        # Update transcription text
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        new_text = f"[{timestamp}] {transcription}\n"
                        st.session_state.transcription_text += new_text

                        # Force Streamlit to update
                        st.rerun()

                time.sleep(2)  # Process every 2 seconds

    except Exception as e:
        st.error(f"Transcription error: {str(e)}")


def stop_recording():
    """Stop the recording process"""
    try:
        st.session_state.recording_active = False

        if st.session_state.audio_recorder:
            audio_file = st.session_state.audio_recorder.stop_recording()

        if st.session_state.meet_bot:
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

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "▶️ Start Recording",
                disabled=not url_valid or st.session_state.recording_active,
                type="primary",
            ):
                if start_recording(meet_url):
                    st.rerun()

        with col2:
            if st.button(
                "⏹️ Stop Recording",
                disabled=not st.session_state.recording_active,
                type="secondary",
            ):
                if stop_recording():
                    st.rerun()

        # Status indicator
        if st.session_state.recording_active:
            st.success("🔴 Recording Active")
        else:
            st.info("⚪ Recording Inactive")

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

        if st.session_state.recording_active:
            # Mock stats for demonstration
            st.metric("Recording Duration", "05:23")
            st.metric("Words Transcribed", "342")
        else:
            st.info("Start recording to see stats")


def start_streamlit():
    """Entry point for poetry start command"""
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()
