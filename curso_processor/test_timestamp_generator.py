#!/usr/bin/env python3
"""
Test script for the timestamp generator module
"""

import os
import sys
import logging
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
from modules.timestamp_generator import TimestampGenerator, generate_timestamps_from_markdown
from utils import ui_components

# Initialize console
console = Console()

def create_test_markdown_file():
    """Create a test markdown file with timestamps"""
    console.print(Panel("Creating Test Markdown File", border_style="bright_blue"))
    
    # Create test directory
    test_dir = Path("/workspace/test_output/processed")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test markdown file
    test_file = test_dir / "test_timestamps.md"
    
    # Create markdown content with timestamps
    markdown_content = """---
title: Test Timestamps
author: OpenHands
date: 2025-06-03
---

# Test Markdown File with Timestamps

## Introduction [00:00]
This is the introduction section of the test file.

## First Section [01:30]
This is the first section of the test file.

### Subsection 1.1 [02:15]
This is a subsection of the first section.

### Subsection 1.2 [03:45]
This is another subsection of the first section.

## Second Section [05:00]
This is the second section of the test file.

### Subsection 2.1 [06:30]
This is a subsection of the second section.

## Conclusion [10:00]
This is the conclusion section of the test file.
"""
    
    # Write to file
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    console.print(f"Created test markdown file: {test_file}")
    
    return test_file

def test_extract_timestamps():
    """Test extracting timestamps from markdown content"""
    console.print(Panel("Testing Timestamp Extraction", border_style="bright_blue"))
    
    # Create test markdown content
    markdown_content = """# Test Markdown

## Introduction [00:00]
This is the introduction.

## First Section [01:30]
This is the first section.

### Subsection 1.1 [02:15]
This is a subsection.

## Second Section [05:00]
This is the second section.
"""
    
    # Initialize timestamp generator
    generator = TimestampGenerator(console=console)
    
    # Extract timestamps
    timestamps = generator.extract_timestamps_from_markdown(markdown_content)
    
    # Display timestamps
    console.print(f"Found {len(timestamps)} timestamps:")
    for ts in timestamps:
        console.print(f"  Level {ts['level']}: {ts['text']} at {ts['timestamp']} ({ts['seconds']} seconds)")
    
    # Verify timestamps are sorted by time
    is_sorted = all(timestamps[i]['seconds'] <= timestamps[i+1]['seconds'] for i in range(len(timestamps)-1))
    console.print(f"Timestamps are sorted by time: {is_sorted}")
    
    return len(timestamps) == 4 and is_sorted

def test_generate_timestamp_file():
    """Test generating timestamp file from markdown file"""
    console.print(Panel("Testing Timestamp File Generation", border_style="bright_blue"))
    
    # Create test markdown file
    test_file = create_test_markdown_file()
    
    # Initialize timestamp generator
    generator = TimestampGenerator(console=console)
    
    # Test JSON format
    console.print("Testing JSON format:")
    json_success, json_result = generator.generate_timestamp_file(
        markdown_path=test_file,
        format_type="json"
    )
    console.print(f"  Success: {json_success}")
    console.print(f"  Output: {json_result}")
    
    # Test CSV format
    console.print("Testing CSV format:")
    csv_success, csv_result = generator.generate_timestamp_file(
        markdown_path=test_file,
        format_type="csv"
    )
    console.print(f"  Success: {csv_success}")
    console.print(f"  Output: {csv_result}")
    
    # Test TXT format
    console.print("Testing TXT format:")
    txt_success, txt_result = generator.generate_timestamp_file(
        markdown_path=test_file,
        format_type="txt"
    )
    console.print(f"  Success: {txt_success}")
    console.print(f"  Output: {txt_result}")
    
    return json_success and csv_success and txt_success

def test_batch_generate_timestamps():
    """Test batch generating timestamps from multiple markdown files"""
    console.print(Panel("Testing Batch Timestamp Generation", border_style="bright_blue"))
    
    # Create test directory (clean it first)
    test_dir = Path("/workspace/test_output/processed/batch_test")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create multiple test markdown files
    for i in range(3):
        test_file = test_dir / f"test_timestamps_{i+1}.md"
        
        # Create markdown content with timestamps
        markdown_content = f"""# Test Markdown {i+1}

## Introduction [00:00]
This is the introduction.

## First Section [01:{i+1}0]
This is the first section.

## Second Section [02:{i+1}0]
This is the second section.
"""
        
        # Write to file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        console.print(f"Created test markdown file: {test_file}")
    
    # Create output directory
    output_dir = Path("/workspace/test_output/timestamps_test")
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize timestamp generator
    generator = TimestampGenerator(console=console)
    
    # Batch generate timestamps
    success, results = generator.batch_generate_timestamps(
        markdown_dir=test_dir,
        output_dir=output_dir,
        format_type="json",
        recursive=False  # Only process files in the test directory
    )
    
    # Display results
    console.print(f"Batch generation success: {success}")
    console.print(f"Processed files: {len(results['processed'])}")
    if 'failed' in results:
        console.print(f"Failed files: {len(results['failed'])}")
        for item in results['failed']:
            console.print(f"  Failed file: {item['markdown_path']}")
            console.print(f"  Error: {item['error']}")
    
    return len(results['processed']) == 3

def main():
    """Main function"""
    console.print(Panel("Testing Timestamp Generator Module", border_style="bright_blue"))
    
    # Test timestamp extraction
    extraction_success = test_extract_timestamps()
    
    # Test timestamp file generation
    file_generation_success = test_generate_timestamp_file()
    
    # Test batch timestamp generation
    batch_generation_success = test_batch_generate_timestamps()
    
    # Display summary
    console.print(Panel("Test Summary", border_style="bright_blue"))
    console.print(f"Timestamp extraction: {'[green]Success[/green]' if extraction_success else '[red]Failed[/red]'}")
    console.print(f"Timestamp file generation: {'[green]Success[/green]' if file_generation_success else '[red]Failed[/red]'}")
    console.print(f"Batch timestamp generation: {'[green]Success[/green]' if batch_generation_success else '[red]Failed[/red]'}")

if __name__ == "__main__":
    main()