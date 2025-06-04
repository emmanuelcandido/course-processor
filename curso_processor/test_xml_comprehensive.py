#!/usr/bin/env python3
"""
Comprehensive test script for XML generator
Tests all functionality of the XML generator module
"""

import os
import sys
import shutil
from pathlib import Path
from rich.console import Console

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from modules import xml_generator
from config import settings

# Create console
console = Console()

def test_xml_comprehensive():
    """Test all XML generator functionality"""
    console.print("[bold cyan]Testing XML Generator Comprehensive[/bold cyan]")
    
    # Create output directory
    output_dir = Path("/workspace/test_output/xml_comprehensive")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test audio files
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Create dummy audio files
    for i in range(1, 6):
        with open(audio_dir / f"module_{i}.mp3", "wb") as f:
            f.write(b"DUMMY AUDIO FILE")
    
    # Create generator
    generator = xml_generator.PodcastXMLGenerator(console=console)
    
    # Test 1: Create feed
    console.print("\n[bold]Test 1: Creating podcast feed...[/bold]")
    success, result = xml_generator.create_podcast_feed(
        title="Comprehensive Test Feed",
        description="This is a comprehensive test feed",
        language="pt-BR",
        category="Education",
        author="Test Author",
        email="test@example.com",
        image_url="https://example.com/image.jpg",
        output_path=output_dir / "test_feed.xml",
        console=console
    )
    
    if success:
        console.print(f"[bold green]Feed created successfully: {result}[/bold green]")
        generator.preview_xml(result)
    else:
        console.print(f"[bold red]Failed to create feed: {result}[/bold red]")
        return
    
    # Test 2: Generate timestamps
    console.print("\n[bold]Test 2: Generating timestamps...[/bold]")
    success, result = generator.generate_timestamps_markdown(
        course_name="Comprehensive Test Course",
        audio_files=list(audio_dir.glob("*.mp3")),
        output_path=output_dir / "timestamps.md"
    )
    
    if success:
        console.print(f"[bold green]Timestamps generated successfully: {result}[/bold green]")
        
        # Display content
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
        
        console.print("Timestamps content:")
        console.print(content)
    else:
        console.print(f"[bold red]Failed to generate timestamps: {result}[/bold red]")
        return
    
    # Test 3: Add course to feed
    console.print("\n[bold]Test 3: Adding course to feed...[/bold]")
    success, result = xml_generator.add_course_to_feed(
        xml_path=output_dir / "test_feed.xml",
        course_name="Comprehensive Test Course",
        audio_url="https://example.com/test_course.mp3",
        timestamps_path=output_dir / "timestamps.md",
        duration="01:30:00",
        author="Test Author",
        console=console
    )
    
    if success:
        console.print(f"[bold green]Course added successfully: {result}[/bold green]")
        generator.preview_xml(result)
    else:
        console.print(f"[bold red]Failed to add course: {result}[/bold red]")
        return
    
    # Test 4: Validate XML
    console.print("\n[bold]Test 4: Validating XML...[/bold]")
    success, results = generator.validate_xml(output_dir / "test_feed.xml")
    
    if success:
        console.print("[bold green]XML is valid![/bold green]")
        
        # Display validation results
        for key, value in results.items():
            console.print(f"[bold]{key}:[/bold] {value}")
    else:
        console.print(f"[bold red]XML is invalid: {results.get('error', 'Unknown error')}[/bold red]")
        return
    
    # Test 5: Update feed
    console.print("\n[bold]Test 5: Updating feed...[/bold]")
    success, result = generator.update_existing_feed(
        xml_path=output_dir / "test_feed.xml",
        title="Updated Test Feed",
        description="This is an updated test feed",
        language="en-US",
        category="Technology",
        author="Updated Author",
        email="updated@example.com",
        image_url="https://example.com/updated_image.jpg"
    )
    
    if success:
        console.print(f"[bold green]Feed updated successfully: {result}[/bold green]")
        generator.preview_xml(result)
    else:
        console.print(f"[bold red]Failed to update feed: {result}[/bold red]")
        return
    
    # Test 6: Add another course
    console.print("\n[bold]Test 6: Adding another course...[/bold]")
    success, result = xml_generator.add_course_to_feed(
        xml_path=output_dir / "test_feed.xml",
        course_name="Second Test Course",
        audio_url="https://example.com/second_course.mp3",
        duration="00:45:00",
        author="Another Author",
        console=console
    )
    
    if success:
        console.print(f"[bold green]Second course added successfully: {result}[/bold green]")
        generator.preview_xml(result)
    else:
        console.print(f"[bold red]Failed to add second course: {result}[/bold red]")
        return
    
    # Test 7: Validate XML again
    console.print("\n[bold]Test 7: Validating XML again...[/bold]")
    success, results = generator.validate_xml(output_dir / "test_feed.xml")
    
    if success:
        console.print("[bold green]XML is valid![/bold green]")
        
        # Display validation results
        for key, value in results.items():
            console.print(f"[bold]{key}:[/bold] {value}")
    else:
        console.print(f"[bold red]XML is invalid: {results.get('error', 'Unknown error')}[/bold red]")
        return
    
    console.print("\n[bold green]All tests completed successfully![/bold green]")

if __name__ == "__main__":
    test_xml_comprehensive()