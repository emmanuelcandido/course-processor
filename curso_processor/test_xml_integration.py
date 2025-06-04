#!/usr/bin/env python3
"""
Test script for XML generator integration
"""

import os
import sys
from pathlib import Path
from rich.console import Console

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from modules import xml_generator
from config import settings

# Create console
console = Console()

def test_xml_integration():
    """Test XML generator integration"""
    console.print("[bold cyan]Testing XML Generator Integration[/bold cyan]")
    
    # Create output directory
    output_dir = Path("/workspace/test_output/xml_integration")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create feed
    console.print("[bold]Creating podcast feed...[/bold]")
    success, result = xml_generator.create_podcast_feed(
        title="Test Integration Feed",
        description="This is a test feed for integration testing",
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
        
        # Preview XML
        generator = xml_generator.PodcastXMLGenerator(console=console)
        generator.preview_xml(result)
        
        # Add course
        console.print("[bold]Adding course to feed...[/bold]")
        
        # Create test timestamps file
        timestamps_path = output_dir / "test_timestamps.md"
        with open(timestamps_path, "w", encoding="utf-8") as f:
            f.write("# Test Course\n\n")
            f.write("## Module 1\n")
            f.write("00:00 Introduction\n")
            f.write("05:00 Basic Concepts\n\n")
            f.write("## Module 2\n")
            f.write("10:00 Advanced Topics\n")
            f.write("15:00 Conclusion\n")
        
        success, result = xml_generator.add_course_to_feed(
            xml_path=output_dir / "test_feed.xml",
            course_name="Test Course",
            audio_url="https://example.com/test_course.mp3",
            timestamps_path=timestamps_path,
            duration="01:00:00",
            author="Test Author",
            console=console
        )
        
        if success:
            console.print(f"[bold green]Course added successfully: {result}[/bold green]")
            
            # Preview XML
            generator.preview_xml(result)
            
            # Validate XML
            console.print("[bold]Validating XML...[/bold]")
            success, results = generator.validate_xml(result)
            
            if success:
                console.print("[bold green]XML is valid![/bold green]")
                
                # Display validation results
                for key, value in results.items():
                    console.print(f"[bold]{key}:[/bold] {value}")
            else:
                console.print(f"[bold red]XML is invalid: {results.get('error', 'Unknown error')}[/bold red]")
        else:
            console.print(f"[bold red]Failed to add course: {result}[/bold red]")
    else:
        console.print(f"[bold red]Failed to create feed: {result}[/bold red]")

if __name__ == "__main__":
    test_xml_integration()