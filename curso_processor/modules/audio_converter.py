"""
Audio conversion module for Curso Processor
"""

import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Union

from rich.progress import Progress, TaskID
from rich.console import Console

from utils import ui_components, file_manager
from config import settings

# Configure logging
logger = logging.getLogger("audio_converter")

def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed
    
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
    return file_manager.check_ffmpeg_installed()

def convert_video_to_audio(
    video_path: Union[str, Path], 
    output_path: Union[str, Path], 
    bitrate: str = "128k",
    format: str = "mp3", 
    progress: Optional[Progress] = None,
    task_id: Optional[TaskID] = None
) -> Tuple[bool, str]:
    """
    Convert a video file to audio
    
    Args:
        video_path: Path to the video file
        output_path: Path to save the audio file
        bitrate: Audio bitrate (e.g., "128k")
        format: Output audio format
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, str]: Success status and output file path or error message
    """
    try:
        # Convert paths to Path objects
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Convertendo {video_path.name}")
        
        # Run ffmpeg command
        command = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # No video
            "-ar", "44100",  # Audio sample rate
            "-ac", "2",  # Stereo
            "-b:a", bitrate,  # Audio bitrate
            "-f", format,  # Output format
            str(output_path),
            "-y"  # Overwrite if exists
        ]
        
        # Execute command
        process = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Verify the output file exists and is not empty
        if not output_path.exists() or output_path.stat().st_size == 0:
            return False, f"Output file {output_path} does not exist or is empty"
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        # Add YAML header to the output file
        try:
            # Get audio duration
            duration = file_manager.get_audio_duration(output_path)
            formatted_duration = file_manager.format_duration(duration)
            
            # Create metadata for the file
            yaml_header = {
                "processed": True,
                "audio_converted": True,
                "transcribed": False,
                "ai_processed": False,
                "tts_generated": False,
                "duration": formatted_duration,
                "original_file": str(video_path),
                "conversion_date": subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip()
            }
            
            # Create a temporary text file with the YAML header
            temp_file = output_path.with_suffix('.txt')
            file_manager.write_yaml_header(temp_file, yaml_header, "")
        except Exception as e:
            logger.warning(f"Error adding YAML header: {str(e)}")
        
        return True, str(output_path)
    
    except subprocess.CalledProcessError as e:
        error_message = f"Error converting {video_path}: {e.stderr}"
        logger.error(error_message)
        return False, error_message
    
    except Exception as e:
        error_message = f"Unexpected error converting {video_path}: {str(e)}"
        logger.error(error_message)
        return False, error_message

def convert_videos_to_audio(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    bitrate: str = "128k",
    format: str = "mp3",
    copy_to_source: bool = True,
    merge_output: bool = True,
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Convert all videos in a directory to audio files
    
    Args:
        input_dir: Directory containing video files
        output_dir: Directory to save audio files
        bitrate: Audio bitrate (e.g., "128k")
        format: Output audio format
        copy_to_source: Whether to copy audio files back to source directory
        merge_output: Whether to merge all audio files into one
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and results
    """
    # Check if FFmpeg is installed
    if not check_ffmpeg_installed():
        error_message = "FFmpeg is not installed. Please install FFmpeg to use this feature."
        if console:
            ui_components.print_error(error_message)
        logger.error(error_message)
        return False, {"error": error_message}
    
    # Convert paths to Path objects
    input_dir = Path(input_dir).expanduser()
    output_dir = Path(output_dir).expanduser()
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize CourseFileManager
    course_manager = file_manager.CourseFileManager(input_dir)
    
    # Scan course directory
    hierarchy = course_manager.scan_course_directory()
    
    # Create folder structure in output directory
    course_manager.create_folder_structure(output_dir)
    
    # Get all video files
    video_files = file_manager.get_video_files(input_dir)
    
    if not video_files:
        message = f"No video files found in {input_dir}"
        if console:
            ui_components.print_warning(message)
        logger.warning(message)
        return False, {"error": message}
    
    # Create progress bar
    progress = ui_components.create_progress_bar("Convertendo vídeos para áudio")
    
    results = {
        "success": True,
        "converted": [],
        "failed": [],
        "total": len(video_files),
        "merged_file": None
    }
    
    with progress:
        # Add task
        task = progress.add_task("Iniciando conversão...", total=len(video_files))
        
        # Process each video
        for video_path in video_files:
            # Get output path
            output_path = course_manager.get_audio_output_path(str(video_path), str(output_dir))
            
            # Convert video to audio
            success, result = convert_video_to_audio(
                video_path=video_path,
                output_path=output_path,
                bitrate=bitrate,
                format=format,
                progress=progress,
                task_id=task
            )
            
            if success:
                results["converted"].append({
                    "video_path": str(video_path),
                    "audio_path": result,
                    "timestamp": course_manager.get_timestamp_for_file(str(video_path))
                })
                
                # Copy audio file to source directory if requested
                if copy_to_source:
                    try:
                        source_audio_path = video_path.with_suffix(f".{format}")
                        shutil.copy2(result, source_audio_path)
                        logger.info(f"Copied audio file to {source_audio_path}")
                    except Exception as e:
                        logger.error(f"Error copying audio file to source directory: {str(e)}")
            else:
                results["failed"].append({
                    "video_path": str(video_path),
                    "error": result
                })
                results["success"] = False
    
    # Count successful conversions
    successful = len(results["converted"])
    
    # Print summary
    if console:
        ui_components.print_success(f"Conversão concluída: {successful}/{len(video_files)} arquivos convertidos com sucesso")
    
    # Merge audio files if requested
    if merge_output and successful > 0:
        if console:
            ui_components.print_info("Unificando arquivos de áudio...")
        
        merged_file = output_dir / f"{course_manager.course_name}_merged.{format}"
        success, result = merge_audio_files(
            [item["audio_path"] for item in results["converted"]],
            str(merged_file)
        )
        
        if success:
            results["merged_file"] = result
            if console:
                ui_components.print_success(f"Arquivo unificado criado: {result}")
        else:
            if console:
                ui_components.print_error(f"Erro ao unificar arquivos: {result}")
    
    return results["success"], results

def merge_audio_files(
    audio_files: List[str],
    output_path: Union[str, Path],
    format: str = "mp3",
    progress: Optional[Progress] = None,
    task_id: Optional[TaskID] = None
) -> Tuple[bool, str]:
    """
    Merge multiple audio files into one
    
    Args:
        audio_files: List of audio file paths
        output_path: Path to save the merged audio file
        format: Output audio format
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, str]: Success status and output file path or error message
    """
    try:
        # Check if FFmpeg is installed
        if not check_ffmpeg_installed():
            return False, "FFmpeg is not installed. Please install FFmpeg to use this feature."
        
        # Convert output_path to Path object
        output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Unificando {len(audio_files)} arquivos de áudio")
        
        # Create a temporary file with the list of audio files
        temp_list_file = output_path.with_name("temp_file_list.txt")
        with open(temp_list_file, 'w', encoding='utf-8') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
        
        # Run ffmpeg command to concatenate files
        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(temp_list_file),
            "-c", "copy",
            str(output_path),
            "-y"  # Overwrite if exists
        ]
        
        # Execute command
        process = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Remove temporary file
        temp_list_file.unlink()
        
        # Verify the output file exists and is not empty
        if not output_path.exists() or output_path.stat().st_size == 0:
            return False, f"Output file {output_path} does not exist or is empty"
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        # Add YAML header to the output file
        try:
            # Get audio duration
            duration = file_manager.get_audio_duration(output_path)
            formatted_duration = file_manager.format_duration(duration)
            
            # Create metadata for the file
            yaml_header = {
                "processed": True,
                "audio_converted": True,
                "transcribed": False,
                "ai_processed": False,
                "tts_generated": False,
                "duration": formatted_duration,
                "merged_from": len(audio_files),
                "conversion_date": subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip()
            }
            
            # Create a temporary text file with the YAML header
            temp_file = output_path.with_suffix('.txt')
            file_manager.write_yaml_header(temp_file, yaml_header, "")
        except Exception as e:
            logger.warning(f"Error adding YAML header: {str(e)}")
        
        return True, str(output_path)
    
    except subprocess.CalledProcessError as e:
        error_message = f"Error merging audio files: {e.stderr}"
        logger.error(error_message)
        return False, error_message
    
    except Exception as e:
        error_message = f"Unexpected error merging audio files: {str(e)}"
        logger.error(error_message)
        return False, error_message

def batch_convert_videos(
    video_paths: List[Union[str, Path]],
    output_dir: Union[str, Path],
    bitrate: str = "128k",
    format: str = "mp3",
    progress: Optional[Progress] = None
) -> List[Tuple[bool, str]]:
    """
    Convert multiple video files to audio
    
    Args:
        video_paths: List of video file paths
        output_dir: Directory to save the audio files
        bitrate: Audio bitrate (e.g., "128k")
        format: Output audio format
        progress: Rich progress object
        
    Returns:
        List[Tuple[bool, str]]: List of results (success status and output path or error message)
    """
    # Check if FFmpeg is installed
    if not check_ffmpeg_installed():
        return [(False, "FFmpeg is not installed. Please install FFmpeg to use this feature.")]
    
    # Convert output_dir to Path object
    output_dir = Path(output_dir).expanduser()
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # Create progress bar if not provided
    if progress is None:
        progress = ui_components.create_progress_bar("Convertendo vídeos para áudio")
    
    with progress:
        # Add task
        task = progress.add_task("Iniciando conversão...", total=len(video_paths))
        
        # Process each video
        for video_path in video_paths:
            # Create output path
            video_path = Path(video_path)
            output_path = output_dir / f"{video_path.stem}.{format}"
            
            # Convert video to audio
            result = convert_video_to_audio(
                video_path=video_path,
                output_path=output_path,
                bitrate=bitrate,
                format=format,
                progress=progress,
                task_id=task
            )
            
            results.append(result)
    
    # Count successful conversions
    successful = sum(1 for result in results if result[0])
    
    # Print summary
    ui_components.print_success(f"Conversão concluída: {successful}/{len(video_paths)} arquivos convertidos com sucesso")
    
    return results