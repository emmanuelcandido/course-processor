#!/usr/bin/env python3
"""
Test script for TTS Generator and Drive Uploader modules
"""

import os
import sys
import asyncio
from pathlib import Path
from rich.console import Console

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.tts_generator import EdgeTTSGenerator, VoiceSettings, run_async
from modules.drive_uploader import GoogleDriveManager

# Create console
console = Console()

# Test directory
TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')
os.makedirs(TEST_DIR, exist_ok=True)

# Test markdown content
TEST_MARKDOWN = """---
title: Test Markdown
author: Test Author
date: 2023-01-01
---

# Test Heading

This is a test paragraph with **bold** and *italic* text.

## Second Heading

- List item 1
- List item 2
- List item 3

### Code Example

```python
def hello_world():
    print("Hello, world!")
```

[Link text](https://example.com)

> Blockquote text

"""

async def test_edge_tts():
    """Test Edge TTS Generator"""
    console.print("\n[bold cyan]Testing Edge TTS Generator[/bold cyan]")
    
    # Create test markdown file
    test_md_path = os.path.join(TEST_DIR, 'test.md')
    with open(test_md_path, 'w', encoding='utf-8') as f:
        f.write(TEST_MARKDOWN)
    
    # Create TTS generator
    tts = EdgeTTSGenerator(console=console)
    
    # Test voice listing
    console.print("[bold]Testing voice listing...[/bold]")
    voices = await tts.get_available_voices()
    console.print(f"Found {len(voices)} voices")
    
    # Test voice preview
    console.print("[bold]Testing voice preview...[/bold]")
    voice_settings = VoiceSettings(voice="pt-BR-FranciscaNeural")
    preview_path = await tts.preview_voice(voice_settings)
    if preview_path and os.path.exists(preview_path):
        console.print(f"Preview generated at: {preview_path}")
    
    # Test markdown cleaning
    console.print("[bold]Testing markdown cleaning...[/bold]")
    with open(test_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned = tts.clean_markdown_for_tts(content)
    console.print("Original length:", len(content))
    console.print("Cleaned length:", len(cleaned))
    console.print("Cleaned content sample:", cleaned[:100] + "...")
    
    # Test content splitting
    console.print("[bold]Testing content splitting...[/bold]")
    segments = tts.split_long_content(cleaned, max_chars=500)
    console.print(f"Split into {len(segments)} segments")
    
    # Test audio generation (small sample)
    console.print("[bold]Testing audio generation (small sample)...[/bold]")
    sample_text = "Este é um teste de geração de áudio com Edge TTS."
    sample_output = os.path.join(TEST_DIR, 'sample.mp3')
    
    segment_result = await tts.generate_audio_segment(sample_text, sample_output, voice_settings)
    if segment_result and os.path.exists(sample_output):
        console.print(f"Sample audio generated at: {sample_output}")
        
        # Test direct merge of a single file
        console.print("[bold]Testing direct merge of a single file...[/bold]")
        merged_output = os.path.join(TEST_DIR, 'merged_sample.mp3')
        merge_result = await tts.merge_audio_segments([sample_output], merged_output)
        
        if merge_result and os.path.exists(merged_output):
            console.print(f"[bold green]Merged audio successfully: {merged_output}[/bold green]")
            
            # Use this as our test output for Drive upload
            return merged_output
    
    # Test full markdown to audio (optional - can be slow)
    console.print("[bold]Testing full markdown to audio...[/bold]")
    output_path = os.path.join(TEST_DIR, 'test_output.mp3')
    
    # Remove any existing resume file
    resume_file = os.path.join(os.path.dirname(output_path), f".{os.path.basename(output_path)}.resume")
    if os.path.exists(resume_file):
        os.remove(resume_file)
    
    # Generate audio from markdown
    success, result = await tts.generate_audio_from_markdown(
        test_md_path, 
        output_path,
        voice_settings,
        resume=False  # Start fresh
    )
    
    if success:
        console.print(f"[bold green]Full audio generated successfully: {result}[/bold green]")
        return result
    else:
        console.print(f"[bold red]Failed to generate full audio: {result}[/bold red]")
        
        # Return the sample audio if it exists
        if os.path.exists(sample_output):
            return sample_output
    
    return None

def test_drive_uploader(audio_path=None):
    """Test Google Drive Uploader"""
    console.print("\n[bold cyan]Testing Google Drive Uploader[/bold cyan]")
    
    # Skip if no audio path provided
    if not audio_path or not os.path.exists(audio_path):
        console.print("[bold yellow]Skipping Drive upload test (no audio file)[/bold yellow]")
        return
    
    # Create Drive manager
    drive = GoogleDriveManager(console=console)
    
    # Test authentication
    console.print("[bold]Testing authentication...[/bold]")
    if not drive.authenticate():
        console.print("[bold red]Authentication failed, skipping Drive tests[/bold red]")
        return
    
    # Test folder creation
    console.print("[bold]Testing folder creation...[/bold]")
    success, folder_id = drive.create_folder("Test_Curso_Processor")
    
    if success:
        console.print(f"[bold green]Folder created: {folder_id}[/bold green]")
        
        # Test file upload
        console.print("[bold]Testing file upload...[/bold]")
        success, file_id = drive.upload_file(audio_path, folder_id)
        
        if success:
            console.print(f"[bold green]File uploaded: {file_id}[/bold green]")
            
            # Test setting permissions
            console.print("[bold]Testing permission setting...[/bold]")
            success, message = drive.set_public_permissions(file_id)
            
            if success:
                console.print(f"[bold green]{message}[/bold green]")
                
                # Get download URL
                download_url = drive.get_direct_download_url(file_id)
                podcast_url = drive.get_podcast_url(file_id)
                
                console.print(f"[bold]Download URL:[/bold] {download_url}")
                console.print(f"[bold]Podcast URL:[/bold] {podcast_url}")
                
                # Test file info
                console.print("[bold]Testing file info...[/bold]")
                success, file_info = drive.get_file_info(file_id)
                
                if success:
                    console.print(f"[bold green]File info retrieved[/bold green]")
                    console.print(f"Name: {file_info.get('name')}")
                    console.print(f"MIME Type: {file_info.get('mimeType')}")
                    console.print(f"Size: {file_info.get('size', 'Unknown')} bytes")
                    console.print(f"Web View Link: {file_info.get('webViewLink')}")
                else:
                    console.print(f"[bold red]Failed to get file info: {file_info}[/bold red]")
                
                # Test file deletion (optional)
                if input("Delete test file? (y/n): ").lower() == 'y':
                    console.print("[bold]Testing file deletion...[/bold]")
                    success, message = drive.delete_file(file_id)
                    
                    if success:
                        console.print(f"[bold green]{message}[/bold green]")
                    else:
                        console.print(f"[bold red]Failed to delete file: {message}[/bold red]")
            else:
                console.print(f"[bold red]Failed to set permissions: {message}[/bold red]")
        else:
            console.print(f"[bold red]Failed to upload file: {file_id}[/bold red]")
    else:
        console.print(f"[bold red]Failed to create folder: {folder_id}[/bold red]")

if __name__ == "__main__":
    # Run TTS tests
    audio_path = run_async(test_edge_tts())
    
    # Run Drive tests
    test_drive_uploader(audio_path)
    
    console.print("\n[bold green]Tests completed![/bold green]")