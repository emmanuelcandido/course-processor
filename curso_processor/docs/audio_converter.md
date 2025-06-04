# Audio Converter Module

The Audio Converter module provides functionality for converting video files to audio format.

## Features

- Convert video files to audio format (MP3, WAV, etc.)
- Batch processing of video files
- Extract audio from specific time ranges
- Normalize audio volume
- Adjust audio quality and bitrate
- Support for various video formats (MP4, AVI, MKV, etc.)

## Usage

### Basic Usage

```python
from modules.audio_converter import AudioConverter
from rich.console import Console

console = Console()

# Initialize audio converter
converter = AudioConverter(console=console)

# Convert video to audio
success, result = converter.convert_video_to_audio(
    video_path="/path/to/video.mp4",
    output_path="/path/to/output.mp3",
    format="mp3",
    bitrate="192k"
)

if success:
    print(f"Video converted successfully: {result}")
else:
    print(f"Failed to convert video: {result}")
```

### Batch Processing

```python
# Process multiple video files
video_files = [
    "/path/to/video1.mp4",
    "/path/to/video2.mp4",
    "/path/to/video3.mp4"
]

output_dir = "/path/to/output_directory"

success, results = converter.batch_convert(
    video_files=video_files,
    output_dir=output_dir,
    format="mp3",
    bitrate="192k"
)

if success:
    print(f"Batch conversion completed successfully")
    for video_file, audio_file in results.items():
        print(f"{video_file} -> {audio_file}")
else:
    print(f"Failed to convert batch: {results}")
```

### Advanced Options

```python
# Convert with advanced options
success, result = converter.convert_video_to_audio(
    video_path="/path/to/video.mp4",
    output_path="/path/to/output.mp3",
    format="mp3",
    bitrate="320k",
    start_time="00:01:30",  # Start at 1 minute 30 seconds
    end_time="00:05:45",    # End at 5 minutes 45 seconds
    normalize=True,         # Normalize audio volume
    channels=2,             # Stereo audio
    sample_rate=44100       # 44.1 kHz sample rate
)

if success:
    print(f"Video converted successfully with advanced options: {result}")
else:
    print(f"Failed to convert video: {result}")
```

### Directory Processing

```python
# Process all videos in a directory
success, results = converter.process_directory(
    input_dir="/path/to/videos",
    output_dir="/path/to/output",
    format="mp3",
    bitrate="192k",
    recursive=True  # Process subdirectories
)

if success:
    print(f"Directory processed successfully")
    print(f"Converted {len(results)} videos")
else:
    print(f"Failed to process directory: {results}")
```

## Class Reference

### AudioConverter

The main class for converting video files to audio format.

#### Methods

- `convert_video_to_audio`: Convert a video file to audio format
- `batch_convert`: Convert multiple video files
- `process_directory`: Process all videos in a directory
- `extract_audio_segment`: Extract a specific segment from a video
- `normalize_audio`: Normalize audio volume
- `get_video_info`: Get information about a video file
- `get_audio_info`: Get information about an audio file

## Dependencies

- ffmpeg-python
- rich (for console output)
- FFmpeg (system dependency)