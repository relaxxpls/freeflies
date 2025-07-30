import atexit
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

from src.bot import MeetBot
from src.recording import AudioRecorder
from src.transcription import Summarizer, Transcriber
from src.utils import transcription_to_markdown, validate_meet_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="FreeFlies - Google Meet Recorder",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Global thread management
transcription_thread: Optional[threading.Thread] = None


def initialize_session_state():
    """Initialize session state variables"""
    if "recording_active" not in st.session_state:
        st.session_state.recording_active = False
    if "transcription_active" not in st.session_state:
        st.session_state.transcription_active = False

    if "transcription" not in st.session_state:
        st.session_state.transcription = []
    if "meeting_history" not in st.session_state:
        st.session_state.meeting_history = []
    if "current_summary" not in st.session_state:
        st.session_state.current_summary = None

    if "meet_bot" not in st.session_state:
        st.session_state.meet_bot = MeetBot()
        atexit.register(lambda: st.session_state.meet_bot.cleanup())
    if "audio_recorder" not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()
        atexit.register(lambda: st.session_state.audio_recorder.cleanup())
    if "transcriber" not in st.session_state:
        st.session_state.transcriber = Transcriber()
        atexit.register(lambda: st.session_state.transcriber.cleanup())
    if "summarizer" not in st.session_state:
        st.session_state.summarizer = Summarizer()


def display_status(message: str, status_type: str = "info"):
    """Display status message with appropriate styling"""
    status_class = f"status-{status_type}"
    st.markdown(
        f'<div class="status-box {status_class}">{message}</div>',
        unsafe_allow_html=True,
    )


def start_recording(meet_url: str):
    """Start the recording process"""
    global transcription_thread

    try:
        st.session_state.transcription = []
        st.session_state.current_summary = None

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
            transcription_thread = threading.Thread(
                target=background_transcription, daemon=True
            )
            add_script_run_ctx(transcription_thread)
            transcription_thread.start()

            return True

    except Exception as e:
        display_status(f"❌ Error: {str(e)}", "error")
        return False


def background_transcription():
    """Background function for real-time transcription"""
    try:
        st.session_state.transcription_active = True

        while (
            st.session_state.recording_active
            or not st.session_state.audio_recorder.is_queue_empty()
        ):
            # Get & transcribe audio chunk with time offset
            chunk_data = st.session_state.audio_recorder.get_audio_chunk()
            if chunk_data is None:
                time.sleep(2)
                continue

            audio_chunk, time_offset = chunk_data
            transcription_results = st.session_state.transcriber.transcribe_chunk(
                audio_chunk, time_offset
            )
            if not transcription_results:
                continue

            st.session_state.transcription.extend(transcription_results)
            logger.debug("background_transcription: transcribed chunk")
            st.rerun()

    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
    finally:
        st.session_state.transcription_active = False
        st.rerun()


def stop_recording():
    """Stop the recording process"""
    global transcription_thread

    try:
        st.session_state.recording_active = False
        start_time = st.session_state.audio_recorder.start_time

        audio_file = st.session_state.audio_recorder.stop_recording()
        st.session_state.meet_bot.leave_meeting()

        # Wait for transcription thread to finish
        if transcription_thread and transcription_thread.is_alive():
            transcription_thread.join(timeout=15)
            transcription_thread = None

        # Save meeting to history
        meeting_data = {
            "start_time": start_time,
            "end_time": time.time(),
            "transcription": st.session_state.transcription.copy(),
            "audio_file": audio_file,
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
                timestamp = datetime.fromtimestamp(meeting["end_time"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                duration = meeting["end_time"] - meeting["start_time"]
                with st.expander(f"Meeting {i + 1} - {timestamp} ({duration:.2f}s)"):
                    st.markdown(transcription_to_markdown(meeting["transcription"]))
        else:
            st.info("No meetings recorded yet")

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("📝 Live Transcription")

        # Real-time transcription display
        if st.session_state.transcription and len(st.session_state.transcription) > 0:
            st.markdown(transcription_to_markdown(st.session_state.transcription))

            # Summarize transcription
            def generate_summary():
                with st.spinner("🤖 Generating summary with AI..."):
                    st.session_state.current_summary = (
                        st.session_state.summarizer.summarize_transcription(
                            st.session_state.transcription
                        )
                    )

            if st.button(label="Summarize", icon="🤖", use_container_width=True):
                generate_summary()
                st.rerun()

            # Display summary if available
            if st.session_state.current_summary:
                st.subheader("📋 Meeting Summary")

                summary_data = st.session_state.current_summary

                if summary_data.summary:
                    st.markdown("### 📝 Summary")
                    st.markdown(summary_data.summary)

                if summary_data.action_items:
                    st.markdown("### ✅ Action Items")
                    for i, item in enumerate(summary_data.action_items):
                        st.checkbox(item, key=f"action_item_{i}", value=False)

                # Show metadata
                if summary_data.word_count:
                    st.caption(
                        f"📊 Word count: {summary_data.word_count} | Generated: {summary_data.generated_at}"
                    )

                # Add a button to clear the summary
                if st.button("Clear Summary", icon="🗑️", key="clear_summary"):
                    st.session_state.current_summary = None
                    st.rerun()

            # Download transcription and summary
            def get_combined_content():
                content = "# Meeting Transcription\n"
                content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

                # Add transcription
                content += "## Transcription\n"
                content += transcription_to_markdown(st.session_state.transcription)

                # Add summary if available
                if st.session_state.current_summary:
                    content += "\n\n## AI-Generated Summary\n"
                    summary_data = st.session_state.current_summary

                    if summary_data.summary:
                        content += "\n### Summary\n"
                        content += summary_data.summary

                    if summary_data.action_items:
                        content += "\n\n### Action Items\n"
                        for item in summary_data.action_items:
                            content += f"- [ ] {item}\n"

                    # Add metadata
                    if summary_data.word_count:
                        content += f"\n\n---\n*Word count: {summary_data.word_count} | Generated: {summary_data.generated_at}*"

                return content

            st.download_button(
                label="Save Transcription & Summary",
                icon="💾",
                data=get_combined_content(),
                file_name=f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        elif st.session_state.recording_active:
            st.info("🎙️ Recording active... Waiting for transcription to begin...")
            # Auto-refresh every few seconds during active recording
            time.sleep(3)
            st.rerun()
        else:
            st.info("Start recording to see live transcription here...")

    with col2:
        st.header("📊 Stats")

        # # Show transcriber loading status
        # if st.session_state.transcriber.is_loading:
        #     st.info("🔄 Loading transcriber model...")
        #     # Auto-refresh while loading to update status
        #     time.sleep(2)
        #     st.rerun()
        # elif not st.session_state.transcriber.is_loaded:
        #     st.warning("⚠️ Transcriber not ready")

        if st.session_state.recording_active:
            duration = st.session_state.audio_recorder.get_recording_duration()
            st.metric("Recording Duration", str(timedelta(seconds=duration)))

            # Estimate word count from transcription
            word_count = len(
                transcription_to_markdown(st.session_state.transcription).split()
            )
            st.metric("Words Transcribed", word_count)

            # Auto-refresh stats during recording
            time.sleep(2)
            st.rerun()
        else:
            st.info("Start recording to see stats")


if __name__ == "__main__":
    main()
