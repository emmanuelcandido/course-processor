# TTS Generator Module

The TTS Generator module provides functionality for generating text-to-speech audio from text files.

## Features

- Convert text to speech using various engines
- Support for multiple languages and voices
- Batch processing of text files
- Customizable speech parameters (rate, volume, pitch)

## Usage

### Basic Usage

```python
from modules.tts_generator import TTSGenerator
from rich.console import Console

console = Console()

# Initialize TTS generator
tts = TTSGenerator(console=console)

# Generate speech from text
success, result = tts.generate_speech(
    text="Hello, this is a test of the TTS generator.",
    output_path="/path/to/output.mp3",
    voice="en-US",
    rate=150,
    volume=1.0,
    pitch=1.0
)

if success:
    print(f"Speech generated successfully: {result}")
else:
    print(f"Failed to generate speech: {result}")
```

### Batch Processing

```python
# Process multiple text files
text_files = [
    "/path/to/text1.txt",
    "/path/to/text2.txt",
    "/path/to/text3.txt"
]

output_dir = "/path/to/output_directory"

success, results = tts.batch_process(
    text_files=text_files,
    output_dir=output_dir,
    voice="pt-BR",
    rate=150,
    volume=1.0,
    pitch=1.0
)

if success:
    print(f"Batch processing completed successfully")
    for text_file, audio_file in results.items():
        print(f"{text_file} -> {audio_file}")
else:
    print(f"Failed to process batch: {results}")
```

### Using Different Engines

```python
# Using pyttsx3 engine
tts = TTSGenerator(engine="pyttsx3", console=console)

# Using Google Cloud TTS (requires API key)
tts = TTSGenerator(engine="google", api_key="your-api-key", console=console)

# Using Amazon Polly (requires AWS credentials)
tts = TTSGenerator(engine="polly", aws_access_key="your-access-key", aws_secret_key="your-secret-key", console=console)
```

## Class Reference

### TTSGenerator

The main class for generating text-to-speech audio.

#### Methods

- `generate_speech`: Generate speech from text
- `batch_process`: Process multiple text files
- `list_available_voices`: List available voices
- `set_engine`: Set the TTS engine
- `set_voice`: Set the voice
- `set_rate`: Set the speech rate
- `set_volume`: Set the volume
- `set_pitch`: Set the pitch

## Dependencies

- pyttsx3 (for local TTS)
- google-cloud-texttospeech (for Google Cloud TTS)
- boto3 (for Amazon Polly)
- rich (for console output)