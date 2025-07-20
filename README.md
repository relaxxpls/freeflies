# FreeFlies - Google Meet Recorder & Transcriber

A Streamlit application that summarizes Google Meet sessions

## Features

- 🎙️ **Automated Meeting Join**: Uses state of the art anti bot software (seleniumbase) to automatically join Google Meet sessions
- 🎵 **Audio Recording**: Records system audio or microphone input during meetings
- 📝 **Real-time Transcription**: Transcribes audio in real-time using OpenAI Whisper
- 🤖 **Summary & Action Items Generation**: Uses an LLM to generate Action Items & Summary from meeting transcription
- 🛡️ **Voice Activity Detection**: Prevents hallucination by filtering silence and background noise
- 🌐 **Web Interface**: Beautiful Streamlit dashboard for control and monitoring
- 💾 **Meeting History**: Saves recordings and transcriptions for future reference
- 🔄 **Streaming Display**: Shows transcription as it happens

## Demo

TODO: attach demo link

## Installation

Clone the repo, create a .env file following the .env.example file and install docker.

Next, using docker:

```bash
docker compose up --build -d
```

Or locally (experimental, requires chrome & audiopulse loopback):

```bash
poetry install
poetry env activate
streamlit run app.py
```

## Usage

1. **Start the Streamlit application**:

   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Enter Google Meet URL** in the sidebar

4. **Click "Start Recording"** to begin the process

5. **Monitor real-time transcription** in the main panel

6. **Stop recording** when finished

7. **Recording history** view previous recordings in bottom left

## How It Works

1. **Meeting Join**: The `MeetBot` class uses SeleniumBase to automate browser interactions and join Google Meet sessions.
2. **AudioPulse**: AudioPulse is used to create a loopback of output to input and Xvfb is used as a virtual display
3. **Audio Recording**: The `AudioRecorder` class captures microphone input in real-time
4. **Transcription**: The `Transcriber` class processes audio chunks using OpenAI Whisper and returns a text stream
5. **Summary**: The `Summarize` class uses langchain and chatgpt to summarize the text and generate Action Items

### How VAD (Voice Cleaning) Works

The system analyzes each audio chunk using multiple criteria:

- **Energy Analysis**: Measures the audio's RMS energy to detect sufficient volume
- **Zero Crossing Rate**: Analyzes frequency content to distinguish speech from noise
- **Silence Detection**: Calculates the percentage of silence in the audio chunk
- **Spectral Analysis**: Examines frequency distribution to identify speech patterns
- **Repetition Detection**: Filters out transcriptions with excessive word repetition

## Future Scope

1. Use feature vectors for speaker identification and some hacky ways for labelling speakers (ref [1](https://github.com/openai/whisper/discussions/827), [2](https://github.com/natto-maki/Transcriber))
2. Use [Silero Vad](https://github.com/snakers4/silero-vad) for detecting human text
3. Make meeting bot scalable and use Kafka for streaming the audio
