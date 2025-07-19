# FreeFlies - Google Meet Recorder & Transcriber

A Streamlit application that automatically joins Google Meet sessions, records audio, and provides real-time transcription using OpenAI Whisper.

## Features

- 🎙️ **Automated Meeting Join**: Uses Playwright to automatically join Google Meet sessions
- 🎵 **Audio Recording**: Records system audio or microphone input during meetings
- 📝 **Real-time Transcription**: Transcribes audio in real-time using OpenAI Whisper
- 🛡️ **Voice Activity Detection**: Prevents hallucination by filtering silence and background noise
- 🌐 **Web Interface**: Beautiful Streamlit dashboard for control and monitoring
- 💾 **Meeting History**: Saves recordings and transcriptions for future reference
- 🔄 **Streaming Display**: Shows transcription as it happens
- 🎯 **Multi-language Support**: Supports 90+ languages through Whisper

## Installation

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- System audio recording capabilities

### Setup

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd freeflies
   ```

2. **Install dependencies using Poetry**:

   ```bash
   poetry install
   ```

3. **Install Playwright browsers**:

   ```bash
   poetry run playwright install
   ```

4. **Activate the virtual environment**:

   ```bash
   poetry shell
   ```

## Usage

### Basic Usage

1. **Start the Streamlit application**:

   ```bash
   streamlit run app.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Enter Google Meet URL** in the sidebar

4. **Click "Start Recording"** to begin the process

5. **Monitor real-time transcription** in the main panel

6. **Stop recording** when finished

### Configuration

You can configure the application using environment variables:

```bash
# Audio settings
export AUDIO_SAMPLE_RATE=44100
export AUDIO_CHANNELS=2
export AUDIO_CHUNK_DURATION=2.0

# Whisper settings
export WHISPER_MODEL_SIZE=base  # tiny, base, small, medium, large
export WHISPER_LANGUAGE=en
export WHISPER_DEVICE=auto      # auto, cpu, cuda, mps

# Voice Activity Detection (VAD) settings - prevents hallucination
export VAD_ENERGY_THRESHOLD=0.01        # Minimum energy for speech detection
export VAD_SILENCE_THRESHOLD=0.5        # Maximum allowed silence percentage
export VAD_MIN_SPEECH_DURATION=0.5      # Minimum speech duration (seconds)
export VAD_MAX_REPETITION_RATIO=0.3     # Maximum word repetition ratio
export VAD_MIN_AUDIO_LENGTH=2.0         # Minimum audio length to process

# Playwright settings
export PLAYWRIGHT_HEADLESS=false
export PLAYWRIGHT_TIMEOUT=30000

# Testing (use dummy implementations)
export USE_DUMMY_IMPLEMENTATIONS=true
```

### Model Sizes

Choose the appropriate Whisper model size based on your needs:

- **tiny**: Fastest, least accurate (~39 MB)
- **base**: Good balance (~74 MB) - **Default**
- **small**: Better accuracy (~244 MB)
- **medium**: High accuracy (~769 MB)
- **large**: Best accuracy (~1550 MB)

## Project Structure

```text
freeflies/
├── app.py                    # Main Streamlit application
├── config.py                 # Configuration management
├── pyproject.toml           # Poetry dependencies
├── bot/
│   ├── __init__.py
│   └── meet_bot.py          # Google Meet automation
├── recording/
│   ├── __init__.py
│   └── audio_recorder.py    # Audio recording functionality
├── transcription/
│   ├── __init__.py
│   └── transcriber.py       # Whisper transcription
├── recordings/              # Saved audio files
└── transcriptions/          # Saved transcription files
```

## How It Works

1. **Meeting Join**: The `MeetBot` class uses Playwright to automate browser interactions and join Google Meet sessions
2. **Audio Recording**: The `AudioRecorder` class captures system audio or microphone input in real-time
3. **Voice Activity Detection**: Audio chunks are analyzed for speech content before transcription
4. **Transcription**: The `Transcriber` class processes audio chunks using OpenAI Whisper and returns text
5. **Streaming**: The Streamlit app displays transcription results in real-time as they're generated

## Voice Activity Detection (VAD)

This application includes advanced voice activity detection to prevent transcription hallucination - a common issue where AI models generate repetitive or nonsensical text when processing silence or background noise.

### How VAD Works

The system analyzes each audio chunk using multiple criteria:

- **Energy Analysis**: Measures the audio's RMS energy to detect sufficient volume
- **Zero Crossing Rate**: Analyzes frequency content to distinguish speech from noise
- **Silence Detection**: Calculates the percentage of silence in the audio chunk
- **Spectral Analysis**: Examines frequency distribution to identify speech patterns
- **Repetition Detection**: Filters out transcriptions with excessive word repetition

### Troubleshooting Transcription Issues

If you experience poor transcription quality, try adjusting these VAD parameters:

**For noisy environments** (too much transcription of background noise):
```bash
export VAD_ENERGY_THRESHOLD=0.02    # Higher threshold
export VAD_SILENCE_THRESHOLD=0.3    # Less silence allowed
```

**For quiet environments** (missing quiet speech):
```bash
export VAD_ENERGY_THRESHOLD=0.005   # Lower threshold
export VAD_MIN_SPEECH_DURATION=0.3  # Shorter speech duration required
```

**For repetitive hallucinations**:
```bash
export VAD_MAX_REPETITION_RATIO=0.2 # Stricter repetition filtering
export VAD_MIN_AUDIO_LENGTH=3.0     # Longer audio chunks
```

### Common Hallucination Patterns Detected

The system automatically detects and filters out common hallucination patterns:
- Excessive repetition (e.g., "Okay okay okay okay...")
- Filler phrases (e.g., "Thank you for watching", "I'm sorry")
- Repeated short words (e.g., "um um um", "uh uh uh")

## Alternatives to Playwright

While Playwright is used in this implementation, here are other approaches you might consider:

### 1. **Browser Extensions**

- More reliable access to browser audio
- Better integration with Google Meet
- Requires extension development and installation

### 2. **WebRTC Direct Connection**

- Direct access to meeting audio streams
- More stable than browser automation
- Requires Google Meet API access (limited availability)

### 3. **System Audio Capture**

- Use virtual audio cables (e.g., VoiceMeeter on Windows, BlackHole on macOS)
- Capture system audio directly
- More reliable but requires additional setup

### 4. **Google Meet API**

- Official API access (when available)
- Most reliable approach
- Currently limited availability

### 5. **Selenium**

- Similar to Playwright but older
- More community support
- Generally slower than Playwright

## Troubleshooting

### Common Issues

1. **Audio Recording Failed**
   - Check microphone permissions
   - Ensure audio device is available
   - Try different audio devices in settings

2. **Meet Join Failed**
   - Verify the Google Meet URL is correct
   - Check if authentication is required
   - Ensure Playwright browsers are installed

3. **Transcription Not Working**
   - Verify Whisper model is loaded
   - Check GPU/CPU availability
   - Try a smaller model size

4. **Permission Errors**
   - Grant microphone access to the browser
   - Allow system audio recording permissions

### Debug Mode

Enable debug logging:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Testing Mode

Use dummy implementations for testing:

```bash
export USE_DUMMY_IMPLEMENTATIONS=true
```

## Privacy & Ethics

⚠️ **Important**: Always ensure you have proper permissions before recording any meeting. Be transparent about recording and transcription activities. Follow your organization's policies and local laws regarding meeting recordings.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for transcription
- [Playwright](https://playwright.dev/) for browser automation
- [Streamlit](https://streamlit.io/) for the web interface
- [SoundDevice](https://python-sounddevice.readthedocs.io/) for audio recording

## Support

If you encounter issues or have questions:

1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information
