#!/usr/bin/env python3
"""
Test script for the XML generator module
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import modules
from modules.xml_generator import PodcastXMLGenerator, create_podcast_feed, add_course_to_feed, validate_podcast_feed
from utils import ui_components

# Initialize console
console = Console()

def setup_test_environment():
    """Set up test environment"""
    console.print(Panel("Setting Up Test Environment", border_style="bright_blue"))
    
    # Create test directory
    test_dir = Path("/workspace/test_output/xml")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test audio files directory
    audio_dir = test_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test timestamps directory
    timestamps_dir = test_dir / "timestamps"
    timestamps_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test timestamps file
    timestamps_file = timestamps_dir / "test_timestamps.md"
    
    # Create timestamps content
    timestamps_content = """# Timestamps - Test Course

## 1. Introduction
   00:00 01_introduction.mp3
   05:30 02_overview.mp3

## 2. Fundamentals
   12:15 01_concepts.mp3
   28:45 02_strategies.mp3
"""
    
    # Write to file
    with open(timestamps_file, "w", encoding="utf-8") as f:
        f.write(timestamps_content)
    
    console.print(f"Created test timestamps file: {timestamps_file}")
    
    return test_dir, timestamps_file

def test_create_rss_feed():
    """Test creating RSS feed"""
    console.print(Panel("Testing RSS Feed Creation", border_style="bright_blue"))
    
    # Set up test environment
    test_dir, _ = setup_test_environment()
    
    # Initialize XML generator
    generator = PodcastXMLGenerator(xml_dir=test_dir, console=console)
    
    # Create RSS feed
    success, output_path = generator.create_rss_feed(
        title="Test Podcast Feed",
        description="This is a test podcast feed",
        language="pt-BR",
        category="Education",
        author="Test Author",
        email="test@example.com",
        image_url="https://example.com/image.jpg",
        output_path=test_dir / "test_feed.xml"
    )
    
    # Display results
    console.print(f"RSS feed creation success: {success}")
    console.print(f"Output path: {output_path}")
    
    # Preview XML
    if success:
        generator.preview_xml(output_path)
    
    return success, output_path

def test_add_course_episode():
    """Test adding course episode to RSS feed"""
    console.print(Panel("Testing Course Episode Addition", border_style="bright_blue"))
    
    # Set up test environment
    test_dir, timestamps_file = setup_test_environment()
    
    # Create RSS feed
    success, xml_path = test_create_rss_feed()
    
    if not success:
        console.print("[red]Failed to create RSS feed, skipping episode addition test[/red]")
        return False, None
    
    # Initialize XML generator
    generator = PodcastXMLGenerator(xml_dir=test_dir, console=console)
    
    # Add course episode
    success, output_path = generator.add_course_episode(
        xml_path=xml_path,
        course_name="Test Course",
        audio_url="https://example.com/test_course.mp3",
        timestamps_path=timestamps_file,
        duration="01:30:00",
        author="Test Author"
    )
    
    # Display results
    console.print(f"Course episode addition success: {success}")
    console.print(f"Output path: {output_path}")
    
    # Preview XML
    if success:
        generator.preview_xml(output_path)
    
    return success, output_path

def test_validate_xml():
    """Test validating XML file"""
    console.print(Panel("Testing XML Validation", border_style="bright_blue"))
    
    # Create RSS feed with course episode
    success, xml_path = test_add_course_episode()
    
    if not success:
        console.print("[red]Failed to create RSS feed with course episode, skipping validation test[/red]")
        return False, None
    
    # Initialize XML generator
    test_dir = Path("/workspace/test_output/xml")
    generator = PodcastXMLGenerator(xml_dir=test_dir, console=console)
    
    # Validate XML
    success, results = generator.validate_xml(xml_path)
    
    # Display results
    console.print(f"XML validation success: {success}")
    console.print(f"Validation results: {results}")
    
    return success, results

def test_generate_timestamps_markdown():
    """Test generating timestamps markdown"""
    console.print(Panel("Testing Timestamps Markdown Generation", border_style="bright_blue"))
    
    # Set up test environment
    test_dir, _ = setup_test_environment()
    
    # Create test audio files
    audio_files = []
    
    # Create introduction directory
    intro_dir = test_dir / "audio" / "introduction"
    intro_dir.mkdir(parents=True, exist_ok=True)
    
    # Create fundamentals directory
    fund_dir = test_dir / "audio" / "fundamentals"
    fund_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test audio files
    audio_files.append(intro_dir / "01_introduction.mp3")
    audio_files.append(intro_dir / "02_overview.mp3")
    audio_files.append(fund_dir / "01_concepts.mp3")
    audio_files.append(fund_dir / "02_strategies.mp3")
    
    # Create empty files
    for file_path in audio_files:
        with open(file_path, "w") as f:
            f.write("")
    
    # Initialize XML generator
    generator = PodcastXMLGenerator(xml_dir=test_dir, console=console)
    
    # Generate timestamps markdown
    success, output_path = generator.generate_timestamps_markdown(
        course_name="Test Course",
        audio_files=audio_files,
        output_path=test_dir / "timestamps" / "test_course_timestamps.md"
    )
    
    # Display results
    console.print(f"Timestamps markdown generation success: {success}")
    console.print(f"Output path: {output_path}")
    
    # Display content
    if success:
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        console.print("Timestamps markdown content:")
        console.print(content)
    
    return success, output_path

def test_helper_functions():
    """Test helper functions"""
    console.print(Panel("Testing Helper Functions", border_style="bright_blue"))
    
    # Set up test environment
    test_dir, timestamps_file = setup_test_environment()
    
    # Test create_podcast_feed
    console.print("Testing create_podcast_feed:")
    success, output_path = create_podcast_feed(
        title="Helper Test Feed",
        description="This is a test feed created with helper function",
        output_path=test_dir / "helper_test_feed.xml",
        console=console
    )
    console.print(f"  Success: {success}")
    console.print(f"  Output path: {output_path}")
    
    if not success:
        return False
    
    # Test add_course_to_feed
    console.print("Testing add_course_to_feed:")
    success, output_path = add_course_to_feed(
        xml_path=output_path,
        course_name="Helper Test Course",
        audio_url="https://example.com/helper_test_course.mp3",
        timestamps_path=timestamps_file,
        duration="01:15:00",
        author="Helper Test Author",
        console=console
    )
    console.print(f"  Success: {success}")
    console.print(f"  Output path: {output_path}")
    
    if not success:
        return False
    
    # Test validate_podcast_feed
    console.print("Testing validate_podcast_feed:")
    success, results = validate_podcast_feed(
        xml_path=output_path,
        console=console
    )
    console.print(f"  Success: {success}")
    console.print(f"  Results: {results}")
    
    return success

def main():
    """Main function"""
    console.print(Panel("Testing XML Generator Module", border_style="bright_blue"))
    
    # Test RSS feed creation
    rss_success, _ = test_create_rss_feed()
    
    # Test course episode addition
    episode_success, _ = test_add_course_episode()
    
    # Test XML validation
    validation_success, _ = test_validate_xml()
    
    # Test timestamps markdown generation
    timestamps_success, _ = test_generate_timestamps_markdown()
    
    # Test helper functions
    helper_success = test_helper_functions()
    
    # Display summary
    console.print(Panel("Test Summary", border_style="bright_blue"))
    console.print(f"RSS feed creation: {'[green]Success[/green]' if rss_success else '[red]Failed[/red]'}")
    console.print(f"Course episode addition: {'[green]Success[/green]' if episode_success else '[red]Failed[/red]'}")
    console.print(f"XML validation: {'[green]Success[/green]' if validation_success else '[red]Failed[/red]'}")
    console.print(f"Timestamps markdown generation: {'[green]Success[/green]' if timestamps_success else '[red]Failed[/red]'}")
    console.print(f"Helper functions: {'[green]Success[/green]' if helper_success else '[red]Failed[/red]'}")

if __name__ == "__main__":
    main()