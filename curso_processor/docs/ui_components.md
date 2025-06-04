# UI Components Module

The UI Components module provides reusable UI components for the Curso Processor system.

## Features

- Nord Theme styling
- ASCII art display
- Menu rendering
- Error handling
- Progress bars
- Tables and panels
- Input prompts
- Status indicators

## Usage

### ASCII Art

```python
from utils.ui_components import display_ascii_art
from rich.console import Console

console = Console()

# Display ASCII art
display_ascii_art(console, "CURSO PROCESSOR")
```

### Menus

```python
from utils.ui_components import render_menu
from rich.console import Console

console = Console()

# Define menu options
menu_options = {
    "1": ("🎬 Convert Videos to Audio", convert_videos),
    "2": ("📝 Transcribe Audio", transcribe_audio),
    "3": ("🤖 Process with AI", process_with_ai),
    "0": ("← Exit", exit_app)
}

# Render menu
selected_option = render_menu(console, "Main Menu", menu_options)

# Handle selected option
if selected_option in menu_options:
    menu_options[selected_option][1]()
```

### Error Handling

```python
from utils.ui_components import handle_error
from rich.console import Console

console = Console()

try:
    # Some code that might raise an exception
    result = 1 / 0
except Exception as e:
    handle_error(console, "Division by zero error", e)
```

### Progress Bars

```python
from utils.ui_components import create_progress_bar
from rich.console import Console
import time

console = Console()

# Create progress bar
progress = create_progress_bar(console, "Processing")

# Use progress bar
with progress:
    task = progress.add_task("Converting...", total=100)
    for i in range(100):
        time.sleep(0.1)
        progress.update(task, advance=1)
```

### Tables and Panels

```python
from utils.ui_components import create_table, create_panel
from rich.console import Console

console = Console()

# Create table
table = create_table(
    console,
    title="Files",
    columns=["Name", "Size", "Type"],
    rows=[
        ["file1.mp3", "10 MB", "Audio"],
        ["file2.mp4", "50 MB", "Video"],
        ["file3.txt", "1 KB", "Text"]
    ]
)

# Display table
console.print(table)

# Create panel
panel = create_panel(
    console,
    title="Information",
    content="This is some information in a panel."
)

# Display panel
console.print(panel)
```

### Input Prompts

```python
from utils.ui_components import prompt_input, prompt_confirm, prompt_choice
from rich.console import Console

console = Console()

# Prompt for input
name = prompt_input(console, "Enter your name")

# Prompt for confirmation
proceed = prompt_confirm(console, "Do you want to proceed?", default=True)

# Prompt for choice
option = prompt_choice(
    console,
    "Select an option",
    choices=["Option 1", "Option 2", "Option 3"],
    default="Option 1"
)
```

### Status Indicators

```python
from utils.ui_components import show_status
from rich.console import Console
import time

console = Console()

# Show status
with show_status(console, "Processing..."):
    # Do some work
    time.sleep(3)

# Show success status
show_status(console, "Operation completed successfully!", status="success")

# Show error status
show_status(console, "Operation failed!", status="error")

# Show warning status
show_status(console, "Operation completed with warnings!", status="warning")
```

## Function Reference

### ASCII Art

- `display_ascii_art`: Display ASCII art

### Menus

- `render_menu`: Render a menu
- `create_menu_table`: Create a menu table

### Error Handling

- `handle_error`: Handle an error
- `show_error`: Show an error message

### Progress Bars

- `create_progress_bar`: Create a progress bar
- `create_spinner`: Create a spinner

### Tables and Panels

- `create_table`: Create a table
- `create_panel`: Create a panel

### Input Prompts

- `prompt_input`: Prompt for input
- `prompt_confirm`: Prompt for confirmation
- `prompt_choice`: Prompt for choice
- `prompt_file`: Prompt for a file
- `prompt_directory`: Prompt for a directory

### Status Indicators

- `show_status`: Show a status indicator
- `show_success`: Show a success message
- `show_error`: Show an error message
- `show_warning`: Show a warning message
- `show_info`: Show an information message

## Dependencies

- rich (for UI components)
- typer (for CLI interface)