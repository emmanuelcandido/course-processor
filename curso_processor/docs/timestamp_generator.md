# Timestamp Generator Module

The Timestamp Generator module provides functionality for generating and managing timestamps for audio and video files.

## Features

- Extract timestamps from markdown files
- Generate timestamp files from audio files
- Convert between different timestamp formats
- Batch processing of files
- Validate and fix timestamp formats

## Usage

### Basic Usage

```python
from modules.timestamp_generator import TimestampGenerator
from rich.console import Console

console = Console()

# Initialize timestamp generator
generator = TimestampGenerator(console=console)

# Extract timestamps from markdown
success, result = generator.extract_timestamps(
    markdown_path="/path/to/markdown.md",
    output_path="/path/to/timestamps.md"
)

if success:
    print(f"Timestamps extracted successfully: {result}")
else:
    print(f"Failed to extract timestamps: {result}")
```

### Generating Timestamps from Audio Files

```python
# Generate timestamps from audio files
audio_files = [
    "/path/to/audio1.mp3",
    "/path/to/audio2.mp3",
    "/path/to/audio3.mp3"
]

success, result = generator.generate_timestamps_from_audio(
    audio_files=audio_files,
    course_name="My Course",
    output_path="/path/to/timestamps.md"
)

if success:
    print(f"Timestamps generated successfully: {result}")
else:
    print(f"Failed to generate timestamps: {result}")
```

### Converting Timestamp Formats

```python
# Convert timestamps from one format to another
success, result = generator.convert_timestamp_format(
    input_path="/path/to/timestamps.md",
    output_path="/path/to/timestamps.srt",
    input_format="markdown",
    output_format="srt"
)

if success:
    print(f"Timestamps converted successfully: {result}")
else:
    print(f"Failed to convert timestamps: {result}")
```

### Batch Processing

```python
# Process multiple markdown files
markdown_files = [
    "/path/to/markdown1.md",
    "/path/to/markdown2.md",
    "/path/to/markdown3.md"
]

output_dir = "/path/to/output_directory"

success, results = generator.batch_extract(
    markdown_files=markdown_files,
    output_dir=output_dir
)

if success:
    print(f"Batch extraction completed successfully")
    for markdown_file, timestamp_file in results.items():
        print(f"{markdown_file} -> {timestamp_file}")
else:
    print(f"Failed to extract batch: {results}")
```

### Validating Timestamps

```python
# Validate timestamps
success, result = generator.validate_timestamps(
    timestamp_path="/path/to/timestamps.md"
)

if success:
    print(f"Timestamps are valid: {result}")
else:
    print(f"Timestamps are invalid: {result}")
```

## Class Reference

### TimestampGenerator

The main class for generating and managing timestamps.

#### Methods

- `extract_timestamps`: Extract timestamps from markdown
- `generate_timestamps_from_audio`: Generate timestamps from audio files
- `convert_timestamp_format`: Convert timestamps from one format to another
- `batch_extract`: Extract timestamps from multiple markdown files
- `validate_timestamps`: Validate timestamps
- `fix_timestamps`: Fix invalid timestamps
- `merge_timestamps`: Merge multiple timestamp files
- `split_timestamps`: Split a timestamp file into multiple files

## Dependencies

- rich (for console output)
- mutagen (for audio duration detection)
- ffmpeg-python (for audio processing)