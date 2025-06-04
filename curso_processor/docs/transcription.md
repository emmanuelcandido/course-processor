# Transcription Module

The Transcription module provides functionality for transcribing audio files to text.

## Features

- Transcribe audio files using OpenAI Whisper API
- Transcribe audio files using local Whisper model
- Support for multiple languages
- Batch processing of audio files
- Diarization (speaker identification)
- Timestamps generation
- Export to various formats (TXT, JSON, SRT, VTT)

## Usage

### Basic Usage

```python
from modules.transcription import WhisperTranscriber
from rich.console import Console

console = Console()

# Initialize transcriber with OpenAI API
transcriber = WhisperTranscriber(
    api_key="your-openai-api-key",
    method="api",
    console=console
)

# Transcribe audio
success, result = transcriber.transcribe_audio(
    audio_path="/path/to/audio.mp3",
    output_path="/path/to/output.txt",
    language="en"
)

if success:
    print(f"Audio transcribed successfully: {result}")
else:
    print(f"Failed to transcribe audio: {result}")
```

### Using Local Whisper Model

```python
# Initialize transcriber with local Whisper model
transcriber = WhisperTranscriber(
    method="local",
    model_size="base",  # tiny, base, small, medium, large
    console=console
)

# Transcribe audio
success, result = transcriber.transcribe_audio(
    audio_path="/path/to/audio.mp3",
    output_path="/path/to/output.txt",
    language="pt"
)

if success:
    print(f"Audio transcribed successfully: {result}")
else:
    print(f"Failed to transcribe audio: {result}")
```

### Using Docker for Local Transcription

```python
# Initialize transcriber with Docker
transcriber = WhisperTranscriber(
    method="docker",
    docker_image="onerahmet/openai-whisper-asr-webservice:latest",
    console=console
)

# Transcribe audio
success, result = transcriber.transcribe_audio(
    audio_path="/path/to/audio.mp3",
    output_path="/path/to/output.txt",
    language="es"
)

if success:
    print(f"Audio transcribed successfully: {result}")
else:
    print(f"Failed to transcribe audio: {result}")
```

### Batch Processing

```python
# Process multiple audio files
audio_files = [
    "/path/to/audio1.mp3",
    "/path/to/audio2.mp3",
    "/path/to/audio3.mp3"
]

output_dir = "/path/to/output_directory"

success, results = transcriber.batch_transcribe(
    audio_files=audio_files,
    output_dir=output_dir,
    language="en",
    format="txt"
)

if success:
    print(f"Batch transcription completed successfully")
    for audio_file, text_file in results.items():
        print(f"{audio_file} -> {text_file}")
else:
    print(f"Failed to transcribe batch: {results}")
```

### Advanced Options

```python
# Transcribe with advanced options
success, result = transcriber.transcribe_audio(
    audio_path="/path/to/audio.mp3",
    output_path="/path/to/output",
    language="en",
    format="json",           # Output format (txt, json, srt, vtt)
    diarize=True,            # Identify speakers
    timestamps=True,         # Include timestamps
    prompt="Medical lecture", # Initial prompt for context
    temperature=0.2,         # Lower temperature for more deterministic output
    initial_prompt="The following is a medical lecture about cardiology."
)

if success:
    print(f"Audio transcribed successfully with advanced options: {result}")
else:
    print(f"Failed to transcribe audio: {result}")
```

## Class Reference

### WhisperTranscriber

The main class for transcribing audio files.

#### Methods

- `transcribe_audio`: Transcribe an audio file
- `batch_transcribe`: Transcribe multiple audio files
- `process_directory`: Process all audio files in a directory
- `get_audio_info`: Get information about an audio file
- `set_api_key`: Set the OpenAI API key
- `set_model`: Set the Whisper model
- `set_method`: Set the transcription method (api, local, docker)

## Dependencies

- openai
- whisper
- ffmpeg-python
- docker (optional, for Docker method)
- rich (for console output)
- FFmpeg (system dependency)