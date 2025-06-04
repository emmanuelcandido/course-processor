"""
Timestamp generator module for Curso Processor
Generates timestamps from various sources including Whisper transcriptions and markdown files
"""

import os
import json
import re
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table

from utils import ui_components, file_manager

# Configure logging
logger = logging.getLogger("timestamp_generator")

def extract_timestamps_from_whisper(transcription_path: str, output_dir: str,
                                  progress: Optional[Progress] = None,
                                  task_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Extract timestamps from Whisper transcription
    
    Args:
        transcription_path: Path to the Whisper transcription file
        output_dir: Directory to save the timestamps
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, str]: Success status and output file path or error message
    """
    try:
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Extraindo timestamps de {os.path.basename(transcription_path)}")
        
        # Load transcription
        with open(transcription_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract segments with timestamps
        timestamps = []
        
        if "segments" in data:
            for segment in data["segments"]:
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                text = segment.get("text", "").strip()
                
                if text:
                    # Format timestamps as HH:MM:SS
                    start_formatted = format_time(start_time)
                    end_formatted = format_time(end_time)
                    
                    timestamps.append({
                        "start": start_time,
                        "end": end_time,
                        "start_formatted": start_formatted,
                        "end_formatted": end_formatted,
                        "text": text
                    })
        
        # Create output filename
        transcription_filename = os.path.basename(transcription_path)
        output_filename = f"timestamps_{os.path.splitext(transcription_filename)[0]}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save timestamps
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timestamps, f, indent=4, ensure_ascii=False)
        
        # Also save as plain text
        text_output_path = os.path.join(output_dir, f"timestamps_{os.path.splitext(transcription_filename)[0]}.txt")
        with open(text_output_path, 'w', encoding='utf-8') as f:
            for ts in timestamps:
                f.write(f"[{ts['start_formatted']} - {ts['end_formatted']}] {ts['text']}\n")
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        return True, output_path
    
    except Exception as e:
        error_message = f"Erro ao extrair timestamps de {transcription_path}: {str(e)}"
        return False, error_message

def generate_timestamps_from_text(text_path: str, output_dir: str,
                                progress: Optional[Progress] = None,
                                task_id: Optional[int] = None) -> Tuple[bool, str]:
    """
    Generate timestamps from processed text
    
    Args:
        text_path: Path to the processed text file
        output_dir: Directory to save the timestamps
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, str]: Success status and output file path or error message
    """
    try:
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Gerando timestamps para {os.path.basename(text_path)}")
        
        # Load text
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Look for timestamp patterns in the text
        # Format: [HH:MM:SS] or [MM:SS] or [H:MM:SS]
        timestamp_pattern = r'\[(\d{1,2}:)?\d{1,2}:\d{2}\]'
        
        # Find all timestamps
        timestamps = []
        
        # Split text by lines
        lines = text.split('\n')
        
        for line in lines:
            # Check if line starts with a timestamp
            match = re.match(r'^\s*\[(\d{1,2}:)?\d{1,2}:\d{2}\]\s*(.*)', line)
            if match:
                timestamp_str = match.group(0).split(']')[0].strip('[')
                content = match.group(2).strip()
                
                # Convert timestamp to seconds
                seconds = parse_time(timestamp_str)
                
                timestamps.append({
                    "start": seconds,
                    "start_formatted": timestamp_str,
                    "text": content
                })
        
        # Create output filename
        text_filename = os.path.basename(text_path)
        output_filename = f"timestamps_{os.path.splitext(text_filename)[0]}.json"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save timestamps
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timestamps, f, indent=4, ensure_ascii=False)
        
        # Also save as plain text
        text_output_path = os.path.join(output_dir, f"timestamps_{os.path.splitext(text_filename)[0]}.txt")
        with open(text_output_path, 'w', encoding='utf-8') as f:
            for ts in timestamps:
                f.write(f"[{ts['start_formatted']}] {ts['text']}\n")
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        return True, output_path
    
    except Exception as e:
        error_message = f"Erro ao gerar timestamps para {text_path}: {str(e)}"
        return False, error_message

def format_time(seconds: float) -> str:
    """
    Format time in seconds to HH:MM:SS
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def parse_time(time_str: str) -> float:
    """
    Parse time string to seconds
    
    Args:
        time_str: Time string in format HH:MM:SS or MM:SS
        
    Returns:
        float: Time in seconds
    """
    parts = time_str.split(':')
    
    if len(parts) == 3:
        # HH:MM:SS
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        # MM:SS
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        # Invalid format
        return 0.0

def batch_generate_timestamps(file_paths: List[str], output_dir: str,
                            is_whisper_json: bool = True) -> List[Tuple[bool, str]]:
    """
    Generate timestamps for multiple files
    
    Args:
        file_paths: List of file paths (Whisper JSON or processed text)
        output_dir: Directory to save the timestamps
        is_whisper_json: Whether the files are Whisper JSON (True) or processed text (False)
        
    Returns:
        List[Tuple[bool, str]]: List of results (success status and output path or error message)
    """
    results = []
    
    # Create progress bar
    progress = ui_components.create_progress_bar("Gerando timestamps")
    
    with progress:
        # Add task
        task = progress.add_task("Iniciando geração de timestamps...", total=len(file_paths))
        
        # Process each file
        for file_path in file_paths:
            if is_whisper_json:
                result = extract_timestamps_from_whisper(
                    transcription_path=file_path,
                    output_dir=output_dir,
                    progress=progress,
                    task_id=task
                )
            else:
                result = generate_timestamps_from_text(
                    text_path=file_path,
                    output_dir=output_dir,
                    progress=progress,
                    task_id=task
                )
            
            results.append(result)
    
    # Count successful generations
    successful = sum(1 for result in results if result[0])
    
    # Print summary
    ui_components.print_success(f"Geração de timestamps concluída: {successful}/{len(file_paths)} arquivos processados com sucesso")
    
    return results


class TimestampGenerator:
    """Class for generating timestamps for processed transcriptions"""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize TimestampGenerator
        
        Args:
            console: Rich console for output
        """
        self.console = console or Console()
    
    def extract_timestamps_from_markdown(
        self,
        markdown_content: str
    ) -> List[Dict[str, Any]]:
        """
        Extract timestamps from markdown content
        
        Args:
            markdown_content: Markdown content with timestamps
            
        Returns:
            List[Dict[str, Any]]: List of timestamps
        """
        # Regular expression to match timestamps in markdown headings
        # Format: ## Heading [MM:SS] or ## Heading [HH:MM:SS]
        timestamp_pattern = r'^(#+)\s+(.*?)\s+\[(\d{1,2}:\d{2}(?::\d{2})?)\]'
        
        timestamps = []
        
        # Process each line
        for line in markdown_content.split('\n'):
            match = re.match(timestamp_pattern, line)
            if match:
                heading_level = len(match.group(1))
                heading_text = match.group(2).strip()
                timestamp_str = match.group(3)
                
                # Convert timestamp to seconds
                seconds = parse_time(timestamp_str)
                
                # Add to timestamps list
                timestamps.append({
                    "level": heading_level,
                    "text": heading_text,
                    "timestamp": timestamp_str,
                    "seconds": seconds
                })
        
        # Sort by seconds
        timestamps.sort(key=lambda x: x["seconds"])
        
        return timestamps
    
    def generate_timestamp_file(
        self,
        markdown_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        format_type: str = "json"
    ) -> Tuple[bool, str]:
        """
        Generate timestamp file from markdown file
        
        Args:
            markdown_path: Path to markdown file
            output_path: Path to output file (if None, will use markdown path with new extension)
            format_type: Output format type (json, csv, txt)
            
        Returns:
            Tuple[bool, str]: Success status and output path or error message
        """
        try:
            # Convert paths to Path objects
            markdown_path = Path(markdown_path)
            
            # Read markdown file
            with open(markdown_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
            
            # Extract timestamps
            timestamps = self.extract_timestamps_from_markdown(markdown_content)
            
            if not timestamps:
                return False, "No timestamps found in markdown file"
            
            # Determine output path if not provided
            if output_path is None:
                output_path = markdown_path.with_suffix(f".timestamps.{format_type}")
            else:
                output_path = Path(output_path)
            
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate output based on format type
            if format_type == "json":
                self._write_json_timestamps(timestamps, output_path)
            elif format_type == "csv":
                self._write_csv_timestamps(timestamps, output_path)
            elif format_type == "txt":
                self._write_txt_timestamps(timestamps, output_path)
            else:
                return False, f"Unsupported format type: {format_type}"
            
            return True, str(output_path)
        
        except Exception as e:
            error_message = f"Error generating timestamp file: {str(e)}"
            logger.error(error_message)
            return False, error_message
    
    def batch_generate_timestamps(
        self,
        markdown_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        format_type: str = "json",
        recursive: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate timestamps for all markdown files in a directory
        
        Args:
            markdown_dir: Directory containing markdown files
            output_dir: Directory to save timestamp files (if None, will use markdown_dir)
            format_type: Output format type (json, csv, txt)
            recursive: Whether to search recursively
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and results
        """
        # Convert paths to Path objects
        markdown_dir = Path(markdown_dir)
        
        # Determine output directory
        if output_dir is None:
            output_dir = markdown_dir
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all markdown files
        if recursive:
            markdown_files = list(markdown_dir.glob("**/*.md"))
        else:
            markdown_files = list(markdown_dir.glob("*.md"))
        
        if not markdown_files:
            return False, {"error": f"No markdown files found in {markdown_dir}"}
        
        # Create progress bar
        progress = ui_components.create_progress_bar("Gerando timestamps")
        
        results = {
            "success": True,
            "processed": [],
            "failed": [],
            "total": len(markdown_files)
        }
        
        with progress:
            # Add task
            task = progress.add_task("Iniciando processamento...", total=len(markdown_files))
            
            # Process each markdown file
            for markdown_file in markdown_files:
                # Update progress
                progress.update(task, description=f"Processando {markdown_file.name}")
                
                try:
                    # Determine output path
                    rel_path = markdown_file.relative_to(markdown_dir)
                    output_path = output_dir / rel_path.with_suffix(f".timestamps.{format_type}")
                    
                    # Generate timestamp file
                    success, result = self.generate_timestamp_file(
                        markdown_path=markdown_file,
                        output_path=output_path,
                        format_type=format_type
                    )
                    
                    # Store result
                    if success:
                        results["processed"].append({
                            "markdown_path": str(markdown_file),
                            "output_path": result
                        })
                    else:
                        results["failed"].append({
                            "markdown_path": str(markdown_file),
                            "error": result
                        })
                        results["success"] = False
                
                except Exception as e:
                    error_message = f"Error processing {markdown_file}: {str(e)}"
                    logger.error(error_message)
                    
                    results["failed"].append({
                        "markdown_path": str(markdown_file),
                        "error": error_message
                    })
                    results["success"] = False
                
                # Update progress
                progress.update(task, advance=1)
        
        # Display summary
        self.console.print(f"Timestamp generation completed: {len(results['processed'])}/{len(markdown_files)} files processed successfully")
        
        if results["failed"]:
            self.console.print(f"Failed: {len(results['failed'])} files")
        
        return results["success"], results
    
    def _write_json_timestamps(self, timestamps: List[Dict[str, Any]], output_path: Path):
        """
        Write timestamps to JSON file
        
        Args:
            timestamps: List of timestamps
            output_path: Output file path
        """
        # Create JSON structure
        json_data = {
            "timestamps": timestamps,
            "count": len(timestamps),
            "generated_at": datetime.datetime.now().isoformat()
        }
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def _write_csv_timestamps(self, timestamps: List[Dict[str, Any]], output_path: Path):
        """
        Write timestamps to CSV file
        
        Args:
            timestamps: List of timestamps
            output_path: Output file path
        """
        # Create CSV content
        csv_lines = ["timestamp,seconds,level,text"]
        
        for ts in timestamps:
            # Escape commas and quotes in text
            text = ts["text"].replace('"', '""')
            if "," in text:
                text = f'"{text}"'
            
            csv_lines.append(f'{ts["timestamp"]},{ts["seconds"]},{ts["level"]},{text}')
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(csv_lines))
    
    def _write_txt_timestamps(self, timestamps: List[Dict[str, Any]], output_path: Path):
        """
        Write timestamps to text file
        
        Args:
            timestamps: List of timestamps
            output_path: Output file path
        """
        # Create text content
        txt_lines = []
        
        for ts in timestamps:
            # Format based on heading level
            indent = "  " * (ts["level"] - 1)
            txt_lines.append(f'{ts["timestamp"]} {indent}{ts["text"]}')
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(txt_lines))


def generate_timestamps_from_markdown(
    markdown_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    format_type: str = "json",
    console: Optional[Console] = None
) -> Tuple[bool, str]:
    """
    Generate timestamps from a markdown file
    
    Args:
        markdown_path: Path to markdown file
        output_path: Path to output file (if None, will use markdown path with new extension)
        format_type: Output format type (json, csv, txt)
        console: Rich console for output
        
    Returns:
        Tuple[bool, str]: Success status and output path or error message
    """
    generator = TimestampGenerator(console=console)
    return generator.generate_timestamp_file(
        markdown_path=markdown_path,
        output_path=output_path,
        format_type=format_type
    )


def batch_generate_timestamps_from_markdown(
    markdown_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    format_type: str = "json",
    recursive: bool = True,
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Generate timestamps for all markdown files in a directory
    
    Args:
        markdown_dir: Directory containing markdown files
        output_dir: Directory to save timestamp files (if None, will use markdown_dir)
        format_type: Output format type (json, csv, txt)
        recursive: Whether to search recursively
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and results
    """
    generator = TimestampGenerator(console=console)
    return generator.batch_generate_timestamps(
        markdown_dir=markdown_dir,
        output_dir=output_dir,
        format_type=format_type,
        recursive=recursive
    )