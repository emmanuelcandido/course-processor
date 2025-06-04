# Progress Tracker Module

The Progress Tracker module provides functionality for tracking and displaying progress in the Curso Processor system.

## Features

- Track progress of long-running operations
- Display progress bars with Rich
- Track multiple operations simultaneously
- Calculate estimated time remaining
- Log progress to file
- Customizable progress display

## Usage

### Basic Usage

```python
from utils.progress_tracker import ProgressTracker
from rich.console import Console
import time

console = Console()

# Initialize progress tracker
tracker = ProgressTracker(console=console)

# Start tracking progress
with tracker.track("Processing files", total=100) as progress:
    for i in range(100):
        # Do some work
        time.sleep(0.1)
        
        # Update progress
        progress.update(advance=1)
```

### Tracking Multiple Operations

```python
# Track multiple operations
with tracker.track_multiple([
    ("Converting videos", 5),
    ("Transcribing audio", 3),
    ("Processing with AI", 2)
]) as progress:
    # Converting videos
    for i in range(5):
        time.sleep(0.5)
        progress[0].update(advance=1)
    
    # Transcribing audio
    for i in range(3):
        time.sleep(1)
        progress[1].update(advance=1)
    
    # Processing with AI
    for i in range(2):
        time.sleep(2)
        progress[2].update(advance=1)
```

### Customizing Progress Display

```python
# Customize progress display
tracker.set_progress_columns([
    "task",
    "percentage",
    "bar",
    "elapsed",
    "eta",
    "speed"
])

# Start tracking with custom display
with tracker.track("Processing files", total=100) as progress:
    for i in range(100):
        time.sleep(0.1)
        progress.update(advance=1)
```

### Logging Progress

```python
# Enable progress logging
tracker.enable_logging("/path/to/progress.log")

# Start tracking with logging
with tracker.track("Processing files", total=100) as progress:
    for i in range(100):
        time.sleep(0.1)
        progress.update(advance=1)

# Disable progress logging
tracker.disable_logging()
```

### Creating Custom Progress Bars

```python
# Create a custom progress bar
progress = tracker.create_progress_bar(
    description="Custom progress bar",
    total=50,
    columns=["task", "percentage", "bar"]
)

# Use the custom progress bar
with progress:
    task = progress.add_task("Processing", total=50)
    for i in range(50):
        time.sleep(0.1)
        progress.update(task, advance=1)
```

## Class Reference

### ProgressTracker

The main class for tracking and displaying progress.

#### Methods

- `track`: Track progress of an operation
- `track_multiple`: Track progress of multiple operations
- `create_progress_bar`: Create a custom progress bar
- `set_progress_columns`: Set the columns to display in progress bars
- `enable_logging`: Enable progress logging
- `disable_logging`: Disable progress logging
- `log_progress`: Log progress to file
- `get_elapsed_time`: Get the elapsed time of an operation
- `get_eta`: Get the estimated time remaining for an operation
- `get_speed`: Get the speed of an operation

## Dependencies

- rich (for progress display)
- tqdm (for progress calculation)