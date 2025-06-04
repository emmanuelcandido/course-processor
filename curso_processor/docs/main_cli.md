# Main CLI Interface

The main CLI interface provides a user-friendly way to interact with the Curso Processor system.

## Features

- Nord Theme styling
- ASCII art title
- Menu-based navigation
- Progress tracking
- Error handling
- Configuration management

## Menu Options

1. 🎬 **Convert Videos to Audio**: Convert video files to audio format
2. 📝 **Transcribe Audio**: Transcribe audio files using Whisper or local transcription
3. 🤖 **Process with AI**: Process transcriptions with Claude or ChatGPT
4. ⏱️ **Generate Timestamps**: Generate timestamps from audio files
5. 🎙️ **Create TTS Audio**: Generate text-to-speech audio
6. 📊 **Generate XML Podcast**: Create and manage podcast RSS feeds
7. ☁️ **Upload to Google Drive**: Upload files to Google Drive
8. 🔗 **Update GitHub**: Manage GitHub repositories
9. 🔄 **Process Complete Course**: Run the complete course processing pipeline
10. ⚙️ **Settings**: Configure system settings

## Usage

### Running the CLI

```bash
# Run the CLI
python main.py

# Or if the script is executable
./main.py
```

### Converting Videos to Audio

1. Select option 1 from the menu
2. Enter the path to the video file or directory
3. Choose the output format (MP3, WAV, etc.)
4. Set the output directory
5. Start the conversion

### Transcribing Audio

1. Select option 2 from the menu
2. Enter the path to the audio file or directory
3. Choose the transcription method (Whisper API or Local)
4. Set the output directory
5. Start the transcription

### Processing with AI

1. Select option 3 from the menu
2. Enter the path to the transcription file or directory
3. Choose the AI model (Claude or ChatGPT)
4. Select the prompt template
5. Start the processing

### Generating Timestamps

1. Select option 4 from the menu
2. Enter the path to the audio file or directory
3. Set the output directory
4. Start the timestamp generation

### Creating TTS Audio

1. Select option 5 from the menu
2. Enter the path to the text file or directory
3. Choose the voice and language
4. Set the output directory
5. Start the TTS generation

### Generating XML Podcast

1. Select option 6 from the menu
2. Choose the action (create feed, add course, update feed, validate XML, generate timestamps)
3. Enter the required information
4. Start the XML generation

### Uploading to Google Drive

1. Select option 7 from the menu
2. Enter the path to the file or directory
3. Choose the destination folder
4. Start the upload

### Updating GitHub

1. Select option 8 from the menu
2. Choose the action (clone, commit, push, create PR, etc.)
3. Enter the required information
4. Start the GitHub operation

### Processing Complete Course

1. Select option 9 from the menu
2. Enter the path to the course directory
3. Configure the processing options
4. Start the complete processing pipeline

### Settings

1. Select option 10 from the menu
2. Choose the setting to configure (credentials, directories, languages, etc.)
3. Enter the new setting value
4. Save the settings

## Customization

### Changing the Theme

The CLI uses the Nord Theme by default. To change the theme, modify the color constants in the main.py file:

```python
# Nord Theme colors
NORD_WHITE = "bright_white"
NORD_BLUE = "bright_blue"
NORD_CYAN = "bright_cyan"
NORD_GREEN = "bright_green"
NORD_YELLOW = "bright_yellow"
NORD_RED = "bright_red"
NORD_DIM = "dim white"
```

### Adding New Menu Options

To add a new menu option, add a new function to the main.py file and update the main menu:

```python
def new_function():
    """New function description"""
    try:
        console.print(f"[{NORD_CYAN}]Starting new function...[/{NORD_CYAN}]")
        
        # Function implementation
        
        console.print(f"[{NORD_GREEN}]New function completed successfully![/{NORD_GREEN}]")
    
    except Exception as e:
        handle_error("Error in new function", e)

# Update the main menu
def main():
    # ...
    menu_options = {
        # ...
        "11": ("🆕 New Function", new_function),
        # ...
    }
    # ...
```

## Dependencies

- typer
- rich
- pydantic