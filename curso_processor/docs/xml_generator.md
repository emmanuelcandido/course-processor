# XML Generator Module

The XML Generator module provides functionality for creating and managing podcast RSS feeds.

## Features

- Create podcast RSS feeds
- Add course episodes to feeds
- Update existing feeds
- Validate XML feeds
- Generate timestamps from audio files

## Usage

### Creating a Podcast Feed

```python
from modules import xml_generator
from rich.console import Console

console = Console()

success, result = xml_generator.create_podcast_feed(
    title="My Podcast Feed",
    description="This is my podcast feed",
    language="pt-BR",
    category="Education",
    author="Your Name",
    email="your@email.com",
    image_url="https://example.com/image.jpg",
    output_path="/path/to/feed.xml",
    console=console
)

if success:
    print(f"Feed created successfully: {result}")
else:
    print(f"Failed to create feed: {result}")
```

### Adding a Course to a Feed

```python
success, result = xml_generator.add_course_to_feed(
    xml_path="/path/to/feed.xml",
    course_name="My Course",
    audio_url="https://example.com/course.mp3",
    timestamps_path="/path/to/timestamps.md",
    duration="01:30:00",
    author="Your Name",
    console=console
)

if success:
    print(f"Course added successfully: {result}")
else:
    print(f"Failed to add course: {result}")
```

### Updating an Existing Feed

```python
from modules.xml_generator import PodcastXMLGenerator

generator = PodcastXMLGenerator(console=console)

success, result = generator.update_existing_feed(
    xml_path="/path/to/feed.xml",
    title="Updated Feed Title",
    description="Updated feed description",
    language="en-US",
    category="Technology",
    author="Updated Author",
    email="updated@email.com",
    image_url="https://example.com/updated_image.jpg"
)

if success:
    print(f"Feed updated successfully: {result}")
else:
    print(f"Failed to update feed: {result}")
```

### Validating XML

```python
success, results = generator.validate_xml("/path/to/feed.xml")

if success:
    print("XML is valid!")
    
    # Display validation results
    for key, value in results.items():
        print(f"{key}: {value}")
else:
    print(f"XML is invalid: {results.get('error', 'Unknown error')}")
```

### Generating Timestamps

```python
success, result = generator.generate_timestamps_markdown(
    course_name="My Course",
    audio_files=["/path/to/audio1.mp3", "/path/to/audio2.mp3"],
    output_path="/path/to/timestamps.md"
)

if success:
    print(f"Timestamps generated successfully: {result}")
else:
    print(f"Failed to generate timestamps: {result}")
```

## Class Reference

### PodcastXMLGenerator

The main class for generating and managing podcast XML feeds.

#### Methods

- `create_rss_feed`: Create a new podcast RSS feed
- `add_course_episode`: Add a course episode to an existing feed
- `update_existing_feed`: Update an existing feed
- `validate_xml`: Validate an XML feed
- `generate_timestamps_markdown`: Generate timestamps from audio files
- `preview_xml`: Preview an XML file in the console

## Helper Functions

- `create_podcast_feed`: Create a new podcast RSS feed
- `add_course_to_feed`: Add a course episode to an existing feed
- `generate_timestamps`: Generate timestamps from audio files

## Dependencies

- xml.etree.ElementTree
- xml.dom.minidom
- rich
- mutagen (optional, for audio duration detection)
- ffmpeg (optional, for audio duration detection)