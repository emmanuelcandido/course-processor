# Curso Processor Documentation

Welcome to the Curso Processor documentation. This documentation provides information about the Curso Processor system, its modules, and how to use them.

## Table of Contents

- [Main CLI Interface](main_cli.md)
- [Audio Converter](audio_converter.md)
- [Transcription](transcription.md)
- [AI Processor](ai_processor.md)
- [Timestamp Generator](timestamp_generator.md)
- [XML Generator](xml_generator.md)
- [TTS Generator](tts_generator.md)
- [Drive Uploader](drive_uploader.md)
- [GitHub Manager](github_manager.md)
- [File Manager](file_manager.md)
- [Progress Tracker](progress_tracker.md)
- [UI Components](ui_components.md)

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/curso-processor.git
cd curso-processor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install system dependencies:
```bash
# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg

# For macOS
brew install ffmpeg

# For Windows
# Download and install FFmpeg from https://ffmpeg.org/download.html
```

4. Make the main script executable:
```bash
chmod +x main.py
```

### Running the CLI

```bash
# Run the CLI
python main.py

# Or if the script is executable
./main.py
```

## System Requirements

- Python 3.8 or higher
- FFmpeg (for audio conversion)
- Docker (optional, for local transcription)
- Internet connection (for API access)

## Configuration

The Curso Processor system can be configured using the settings menu in the CLI. The following settings can be configured:

- API credentials (OpenAI, Anthropic, Google, GitHub)
- Directories (work, GitHub local, XML, audio, transcription, processed)
- Languages and voices for TTS
- Default settings for audio conversion, transcription, and AI processing

## License

MIT