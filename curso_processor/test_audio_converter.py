#!/usr/bin/env python3
"""
Test script for audio_converter and file_manager modules
"""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from utils import file_manager
from modules import audio_converter

# Initialize console
console = Console()

def test_course_file_manager():
    """Test CourseFileManager"""
    console.print(Panel(Text("Testing CourseFileManager", style="bold cyan"), expand=False))
    
    # Test directory
    test_dir = Path("/workspace/test_course")
    
    # Initialize CourseFileManager
    course_manager = file_manager.CourseFileManager(test_dir)
    
    # Scan course directory
    console.print("Scanning course directory...")
    hierarchy = course_manager.scan_course_directory()
    
    # Print hierarchy
    console.print("Course hierarchy:")
    console.print(hierarchy)
    
    # Calculate timestamps
    console.print("Calculating timestamps...")
    course_manager.calculate_timestamps()
    
    # Print timestamps
    console.print("Timestamps:")
    console.print(course_manager.timestamps)
    
    # Test create_folder_structure
    output_dir = Path("/workspace/test_output")
    console.print(f"Creating folder structure in {output_dir}...")
    course_manager.create_folder_structure(output_dir)
    
    # List created directories
    console.print("Created directories:")
    for path in output_dir.rglob("*"):
        if path.is_dir():
            console.print(f"  {path}")
    
    console.print(Panel(Text("CourseFileManager test completed", style="bold green"), expand=False))

def test_audio_converter():
    """Test audio_converter"""
    console.print(Panel(Text("Testing audio_converter", style="bold cyan"), expand=False))
    
    # Check if FFmpeg is installed
    if not audio_converter.check_ffmpeg_installed():
        console.print("FFmpeg is not installed. Skipping audio conversion test.")
        return
    
    # Test directory
    test_dir = Path("/workspace/test_course")
    output_dir = Path("/workspace/test_output")
    
    # Convert videos to audio
    console.print("Converting videos to audio...")
    success, results = audio_converter.convert_videos_to_audio(
        input_dir=test_dir,
        output_dir=output_dir,
        bitrate="128k",
        format="mp3",
        copy_to_source=True,
        merge_output=True,
        console=console
    )
    
    # Print results
    console.print(f"Conversion success: {success}")
    console.print(f"Converted files: {len(results.get('converted', []))}")
    console.print(f"Failed files: {len(results.get('failed', []))}")
    
    if results.get("merged_file"):
        console.print(f"Merged file: {results['merged_file']}")
    
    console.print(Panel(Text("audio_converter test completed", style="bold green"), expand=False))

if __name__ == "__main__":
    # Test CourseFileManager
    test_course_file_manager()
    
    # Test audio_converter
    test_audio_converter()