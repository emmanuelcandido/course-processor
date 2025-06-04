# File Manager Module

The File Manager module provides functionality for managing files and directories in the Curso Processor system.

## Features

- Create and manage directory structures
- Scan directories for specific file types
- Create and manage YAML headers for tracking processing status
- Calculate file sizes and durations
- Batch file operations
- File validation and verification

## Usage

### Basic Usage

```python
from utils.file_manager import CourseFileManager
from rich.console import Console

console = Console()

# Initialize file manager
file_manager = CourseFileManager(console=console)

# Create directory structure
success, result = file_manager.create_directory_structure(
    base_dir="/path/to/course",
    course_name="Python Programming"
)

if success:
    print(f"Directory structure created successfully: {result}")
else:
    print(f"Failed to create directory structure: {result}")
```

### Scanning Directories

```python
# Scan directory for audio files
success, result = file_manager.scan_directory(
    directory="/path/to/course",
    file_types=[".mp3", ".wav", ".m4a"],
    recursive=True
)

if success:
    print(f"Found {len(result)} audio files:")
    for file in result:
        print(f"- {file}")
else:
    print(f"Failed to scan directory: {result}")
```

### Managing YAML Headers

```python
# Create YAML header
header = {
    "title": "Python Programming",
    "author": "John Doe",
    "date": "2023-01-01",
    "status": "processing",
    "progress": 0
}

success, result = file_manager.create_yaml_header(
    file_path="/path/to/file.md",
    header=header
)

if success:
    print(f"YAML header created successfully: {result}")
else:
    print(f"Failed to create YAML header: {result}")

# Update YAML header
updates = {
    "status": "completed",
    "progress": 100
}

success, result = file_manager.update_yaml_header(
    file_path="/path/to/file.md",
    updates=updates
)

if success:
    print(f"YAML header updated successfully: {result}")
else:
    print(f"Failed to update YAML header: {result}")
```

### Calculating File Information

```python
# Calculate file size
size = file_manager.get_file_size("/path/to/file.mp3")
print(f"File size: {size} bytes")

# Calculate audio duration
duration = file_manager.get_audio_duration("/path/to/file.mp3")
print(f"Audio duration: {duration} seconds")

# Format duration
formatted_duration = file_manager.format_duration(duration)
print(f"Formatted duration: {formatted_duration}")
```

### Batch Operations

```python
# Process multiple files
files = [
    "/path/to/file1.mp3",
    "/path/to/file2.mp3",
    "/path/to/file3.mp3"
]

success, results = file_manager.batch_process(
    files=files,
    operation="calculate_duration"
)

if success:
    print(f"Batch processing completed successfully")
    for file, duration in results.items():
        print(f"{file}: {file_manager.format_duration(duration)}")
else:
    print(f"Failed to process batch: {results}")
```

## Class Reference

### CourseFileManager

The main class for managing files and directories.

#### Methods

- `create_directory_structure`: Create a directory structure
- `scan_directory`: Scan a directory for specific file types
- `create_yaml_header`: Create a YAML header
- `update_yaml_header`: Update a YAML header
- `get_yaml_header`: Get a YAML header
- `get_file_size`: Get the size of a file
- `get_audio_duration`: Get the duration of an audio file
- `format_duration`: Format a duration in seconds to HH:MM:SS
- `batch_process`: Process multiple files
- `validate_file`: Validate a file
- `verify_file_exists`: Verify that a file exists
- `get_file_extension`: Get the extension of a file
- `get_file_name`: Get the name of a file without extension
- `get_file_path`: Get the path of a file without the file name
- `get_absolute_path`: Get the absolute path of a file

## Dependencies

- rich (for console output)
- pyyaml (for YAML processing)
- mutagen (for audio duration detection)
- ffmpeg-python (for audio processing)