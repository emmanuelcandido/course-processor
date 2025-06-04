"""
File management utilities for Curso Processor
"""

import os
import json
import shutil
import logging
import yaml
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import timedelta
import hashlib

from config import settings
from utils import ui_components

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / "data" / "file_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("file_manager")

# Cache file for file durations
DURATION_CACHE_FILE = Path(__file__).parent.parent / "data" / "duration_cache.json"

def initialize_directories():
    """Initialize all required directories"""
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Create processed courses file if it doesn't exist
    processed_courses_file = data_dir / "processed_courses.json"
    if not processed_courses_file.exists():
        with open(processed_courses_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
    
    # Create duration cache file if it doesn't exist
    if not DURATION_CACHE_FILE.exists():
        with open(DURATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
    
    # Ensure all configured directories exist
    ensure_directory_exists(settings.get_default_video_dir())
    ensure_directory_exists(settings.get_default_audio_dir())
    ensure_directory_exists(settings.get_default_transcription_dir())
    ensure_directory_exists(settings.get_default_tts_dir())
    ensure_directory_exists(settings.get_default_xml_dir())
    ensure_directory_exists(settings.get_default_github_dir())

def ensure_directory_exists(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory: Path to the directory
        
    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    try:
        directory_path = Path(directory).expanduser()
        directory_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def get_video_files(directory: str) -> List[Path]:
    """
    Get all video files in a directory
    
    Args:
        directory: Path to the directory
        
    Returns:
        List[Path]: List of video file paths
    """
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    
    directory_path = Path(directory).expanduser()
    video_files = []
    
    try:
        for path in directory_path.rglob('*'):
            if path.is_file() and path.suffix.lower() in video_extensions:
                video_files.append(path)
    except Exception as e:
        logger.error(f"Error scanning for video files in {directory}: {str(e)}")
    
    return sorted(video_files)

def get_text_files(directory: str) -> List[Path]:
    """
    Get all text files in a directory
    
    Args:
        directory: Path to the directory
        
    Returns:
        List[Path]: List of text file paths
    """
    text_extensions = {'.txt', '.md', '.text'}
    
    directory_path = Path(directory).expanduser()
    text_files = []
    
    try:
        for file_path in directory_path.glob('**/*'):
            if file_path.is_file() and file_path.suffix.lower() in text_extensions:
                text_files.append(file_path)
        
        # Sort files by name
        text_files.sort()
        
        return text_files
    
    except Exception as e:
        logging.error(f"Error getting text files: {str(e)}")
        return []

def get_markdown_files(directory: str) -> List[str]:
    """
    Get all markdown files in a directory
    
    Args:
        directory: Path to the directory
        
    Returns:
        List[str]: List of markdown file paths as strings
    """
    directory_path = Path(directory).expanduser()
    markdown_files = []
    
    try:
        for path in directory_path.rglob('*.md'):
            if path.is_file():
                markdown_files.append(str(path))
    except Exception as e:
        logger.error(f"Error scanning for markdown files in {directory}: {str(e)}")
    
    return sorted(markdown_files)

def get_files_by_extensions(directory: str, extensions: List[str]) -> List[str]:
    """
    Get all files with specified extensions in a directory
    
    Args:
        directory: Path to the directory
        extensions: List of file extensions (without dots)
        
    Returns:
        List[str]: List of file paths as strings
    """
    # Normalize extensions (add dot if missing)
    normalized_extensions = {ext if ext.startswith('.') else f'.{ext}' for ext in extensions}
    
    directory_path = Path(directory).expanduser()
    files = []
    
    try:
        for path in directory_path.rglob('*'):
            if path.is_file() and path.suffix.lower() in normalized_extensions:
                files.append(str(path))
    except Exception as e:
        logger.error(f"Error scanning for files in {directory}: {str(e)}")
    
    return sorted(files)

def get_audio_files(directory: str) -> List[Path]:
    """
    Get all audio files in a directory
    
    Args:
        directory: Path to the directory
        
    Returns:
        List[Path]: List of audio file paths
    """
    audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}
    
    directory_path = Path(directory).expanduser()
    audio_files = []
    
    try:
        for path in directory_path.rglob('*'):
            if path.is_file() and path.suffix.lower() in audio_extensions:
                audio_files.append(path)
    except Exception as e:
        logger.error(f"Error scanning for audio files in {directory}: {str(e)}")
    
    return sorted(audio_files)

def get_transcription_files(directory: str) -> List[Path]:
    """
    Get all transcription files in a directory
    
    Args:
        directory: Path to the directory
        
    Returns:
        List[Path]: List of transcription file paths
    """
    text_extensions = {'.txt', '.json', '.md'}
    
    directory_path = Path(directory).expanduser()
    text_files = []
    
    try:
        for path in directory_path.rglob('*'):
            if path.is_file() and path.suffix.lower() in text_extensions:
                text_files.append(path)
    except Exception as e:
        logger.error(f"Error scanning for transcription files in {directory}: {str(e)}")
    
    return sorted(text_files)

def get_file_hash(file_path: Path) -> str:
    """
    Calculate MD5 hash of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MD5 hash of the file
    """
    try:
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {str(e)}")
        return ""

def get_audio_duration(audio_path: Path) -> float:
    """
    Get the duration of an audio file in seconds
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        float: Duration in seconds
    """
    # Check cache first
    try:
        with open(DURATION_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        file_hash = get_file_hash(audio_path)
        if file_hash and file_hash in cache:
            return cache[file_hash]
    except Exception as e:
        logger.warning(f"Error reading duration cache: {str(e)}")
    
    # Try with mutagen first
    try:
        import mutagen
        audio = mutagen.File(audio_path)
        if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            duration = audio.info.length
            
            # Cache the result
            try:
                with open(DURATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                
                file_hash = get_file_hash(audio_path)
                if file_hash:
                    cache[file_hash] = duration
                    
                    with open(DURATION_CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cache, f, indent=4)
            except Exception as e:
                logger.warning(f"Error updating duration cache: {str(e)}")
            
            return duration
    except ImportError:
        logger.warning("mutagen not installed, trying librosa")
    except Exception as e:
        logger.warning(f"Error getting duration with mutagen: {str(e)}")
    
    # Try with librosa as fallback
    try:
        import librosa
        duration = librosa.get_duration(path=str(audio_path))
        
        # Cache the result
        try:
            with open(DURATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            file_hash = get_file_hash(audio_path)
            if file_hash:
                cache[file_hash] = duration
                
                with open(DURATION_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=4)
        except Exception as e:
            logger.warning(f"Error updating duration cache: {str(e)}")
        
        return duration
    except ImportError:
        logger.warning("librosa not installed, trying ffprobe")
    except Exception as e:
        logger.warning(f"Error getting duration with librosa: {str(e)}")
    
    # Try with ffprobe as last resort
    try:
        import subprocess
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(audio_path)
        ]
        output = subprocess.check_output(cmd).decode('utf-8').strip()
        duration = float(output)
        
        # Cache the result
        try:
            with open(DURATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            file_hash = get_file_hash(audio_path)
            if file_hash:
                cache[file_hash] = duration
                
                with open(DURATION_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=4)
        except Exception as e:
            logger.warning(f"Error updating duration cache: {str(e)}")
        
        return duration
    except Exception as e:
        logger.error(f"Error getting duration with ffprobe: {str(e)}")
        return 0.0

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to HH:MM:SS
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration
    """
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def save_processed_course(course_data: Dict[str, Any]):
    """
    Save processed course data
    
    Args:
        course_data: Course data to save
    """
    processed_courses_file = Path(__file__).parent.parent / "data" / "processed_courses.json"
    
    try:
        # Load existing data
        with open(processed_courses_file, 'r', encoding='utf-8') as f:
            courses = json.load(f)
        
        # Add new course data
        courses.append(course_data)
        
        # Limit the number of entries if needed
        max_entries = settings.get_history_settings().get("max_entries", 50)
        if len(courses) > max_entries:
            courses = courses[-max_entries:]
        
        # Save updated data
        with open(processed_courses_file, 'w', encoding='utf-8') as f:
            json.dump(courses, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving processed course data: {str(e)}")

def get_processed_courses() -> List[Dict[str, Any]]:
    """
    Get all processed courses
    
    Returns:
        List[Dict[str, Any]]: List of processed course data
    """
    processed_courses_file = Path(__file__).parent.parent / "data" / "processed_courses.json"
    
    try:
        with open(processed_courses_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error getting processed courses: {str(e)}")
        return []

def clear_processed_courses():
    """Clear all processed courses data"""
    processed_courses_file = Path(__file__).parent.parent / "data" / "processed_courses.json"
    
    try:
        with open(processed_courses_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)
    except Exception as e:
        logger.error(f"Error clearing processed courses: {str(e)}")

def clear_cache():
    """Clear cache files"""
    try:
        # Clear duration cache
        with open(DURATION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4)
        
        logger.info("Cache cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False

def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed
    
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
    try:
        import subprocess
        subprocess.check_output(["ffmpeg", "-version"], stderr=subprocess.STDOUT)
        return True
    except Exception:
        return False

def read_yaml_header(file_path: Path) -> Dict[str, Any]:
    """
    Read YAML header from a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dict[str, Any]: YAML header data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has YAML header
        if content.startswith('---'):
            # Extract YAML header
            parts = content.split('---', 2)
            if len(parts) >= 3:
                header = parts[1].strip()
                return yaml.safe_load(header) or {}
        
        return {}
    except Exception as e:
        logger.error(f"Error reading YAML header from {file_path}: {str(e)}")
        return {}

def write_yaml_header(file_path: Path, header_data: Dict[str, Any], content: Optional[str] = None):
    """
    Write YAML header to a file
    
    Args:
        file_path: Path to the file
        header_data: YAML header data
        content: File content (if None, preserve existing content)
    """
    try:
        if content is None and file_path.exists():
            # Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Remove existing YAML header if present
            if file_content.startswith('---'):
                parts = file_content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2]
                else:
                    content = ""
            else:
                content = file_content
        
        # Format YAML header
        yaml_header = yaml.dump(header_data, default_flow_style=False)
        
        # Write file with header
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('---\n')
            f.write(yaml_header)
            f.write('---\n')
            if content:
                f.write(content)
    except Exception as e:
        logger.error(f"Error writing YAML header to {file_path}: {str(e)}")

class CourseFileManager:
    """Class to manage course files and directory structure"""
    
    def __init__(self, course_dir: str):
        """
        Initialize CourseFileManager
        
        Args:
            course_dir: Path to the course directory
        """
        self.course_dir = Path(course_dir).expanduser()
        self.course_name = self.course_dir.name
        self.hierarchy = {}
        self.total_duration = 0.0
        self.timestamps = {}
        
        # Create cache directory
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache" / self.course_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache file for hierarchy
        self.hierarchy_cache = self.cache_dir / "hierarchy.json"
    
    def scan_course_directory(self) -> Dict[str, Any]:
        """
        Scan course directory and build hierarchy
        
        Returns:
            Dict[str, Any]: Course hierarchy
        """
        # Check if cached hierarchy exists and is recent
        if self.hierarchy_cache.exists():
            try:
                cache_mtime = self.hierarchy_cache.stat().st_mtime
                course_mtime = max(p.stat().st_mtime for p in self.course_dir.rglob('*') if p.is_file())
                
                if cache_mtime >= course_mtime:
                    # Cache is up to date
                    with open(self.hierarchy_cache, 'r', encoding='utf-8') as f:
                        self.hierarchy = json.load(f)
                    
                    logger.info(f"Loaded hierarchy from cache for {self.course_name}")
                    return self.hierarchy
            except Exception as e:
                logger.warning(f"Error checking cache: {str(e)}")
        
        # Build hierarchy
        logger.info(f"Scanning course directory: {self.course_dir}")
        
        self.hierarchy = {
            "name": self.course_name,
            "path": str(self.course_dir),
            "type": "directory",
            "children": [],
            "duration": 0.0,
            "formatted_duration": "00:00:00",
            "timestamp": "00:00:00"
        }
        
        # Get all directories and files
        try:
            self._scan_directory(self.course_dir, self.hierarchy["children"])
            
            # Calculate timestamps
            self.calculate_timestamps()
            
            # Save hierarchy to cache
            with open(self.hierarchy_cache, 'w', encoding='utf-8') as f:
                json.dump(self.hierarchy, f, indent=4)
            
            return self.hierarchy
        except Exception as e:
            logger.error(f"Error scanning course directory: {str(e)}")
            return self.hierarchy
    
    def _scan_directory(self, directory: Path, children: List[Dict[str, Any]]):
        """
        Recursively scan directory and build hierarchy
        
        Args:
            directory: Directory to scan
            children: List to add children to
        """
        # Get all items in directory
        items = list(directory.iterdir())
        
        # Sort items: directories first, then files, both alphabetically
        dirs = sorted([item for item in items if item.is_dir()], key=lambda x: x.name.lower())
        files = sorted([item for item in items if item.is_file()], key=lambda x: x.name.lower())
        
        # Process directories
        for dir_path in dirs:
            dir_item = {
                "name": dir_path.name,
                "path": str(dir_path),
                "type": "directory",
                "children": [],
                "duration": 0.0,
                "formatted_duration": "00:00:00",
                "timestamp": "00:00:00"
            }
            
            children.append(dir_item)
            self._scan_directory(dir_path, dir_item["children"])
        
        # Process files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}
        
        for file_path in files:
            # Skip hidden files
            if file_path.name.startswith('.'):
                continue
            
            file_item = {
                "name": file_path.name,
                "path": str(file_path),
                "type": "file",
                "extension": file_path.suffix.lower(),
                "duration": 0.0,
                "formatted_duration": "00:00:00",
                "timestamp": "00:00:00"
            }
            
            # Get duration for audio and video files
            if file_path.suffix.lower() in video_extensions or file_path.suffix.lower() in audio_extensions:
                # For video files, we'll estimate duration based on file size
                # For audio files, we'll get actual duration
                if file_path.suffix.lower() in audio_extensions:
                    file_item["duration"] = get_audio_duration(file_path)
                    file_item["formatted_duration"] = format_duration(file_item["duration"])
            
            # Read YAML header if exists
            yaml_data = read_yaml_header(file_path)
            if yaml_data:
                file_item["yaml_header"] = yaml_data
            
            children.append(file_item)
    
    def calculate_timestamps(self):
        """Calculate timestamps for all items in hierarchy"""
        self.timestamps = {}
        self.total_duration = 0.0
        
        # Start with timestamp 00:00:00
        current_timestamp = 0.0
        
        # Process hierarchy
        self._calculate_timestamps_recursive(self.hierarchy, current_timestamp)
        
        # Update total duration
        self.hierarchy["duration"] = self.total_duration
        self.hierarchy["formatted_duration"] = format_duration(self.total_duration)
    
    def _calculate_timestamps_recursive(self, item: Dict[str, Any], current_timestamp: float):
        """
        Recursively calculate timestamps
        
        Args:
            item: Hierarchy item
            current_timestamp: Current timestamp in seconds
        """
        # Set timestamp for current item
        item["timestamp"] = format_duration(current_timestamp)
        self.timestamps[item["path"]] = {
            "timestamp": item["timestamp"],
            "timestamp_seconds": current_timestamp
        }
        
        # Process children if any
        if "children" in item and item["children"]:
            child_timestamp = current_timestamp
            
            for child in item["children"]:
                self._calculate_timestamps_recursive(child, child_timestamp)
                
                # Update child timestamp for next child
                if "duration" in child and child["duration"] > 0:
                    child_timestamp += child["duration"]
                    
                    # Update parent duration
                    item["duration"] += child["duration"]
            
            # Update formatted duration
            item["formatted_duration"] = format_duration(item["duration"])
        
        # Update total duration
        if item == self.hierarchy:
            self.total_duration = item["duration"]
    
    def generate_hierarchy(self) -> Dict[str, Any]:
        """
        Generate course hierarchy
        
        Returns:
            Dict[str, Any]: Course hierarchy
        """
        if not self.hierarchy:
            self.scan_course_directory()
        
        return self.hierarchy
    
    def create_folder_structure(self, target_dir: str, structure_type: str = "audio") -> bool:
        """
        Create folder structure in target directory
        
        Args:
            target_dir: Target directory
            structure_type: Type of structure to create (audio, transcription, etc.)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.hierarchy:
            self.scan_course_directory()
        
        target_path = Path(target_dir).expanduser()
        
        try:
            # Create target directory
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Create course directory
            course_target = target_path / self.course_name
            course_target.mkdir(exist_ok=True)
            
            # Create subdirectories
            self._create_folder_structure_recursive(self.hierarchy, course_target)
            
            return True
        except Exception as e:
            logger.error(f"Error creating folder structure: {str(e)}")
            return False
    
    def _create_folder_structure_recursive(self, item: Dict[str, Any], target_path: Path):
        """
        Recursively create folder structure
        
        Args:
            item: Hierarchy item
            target_path: Target path
        """
        # Process children if any
        if "children" in item and item["children"]:
            for child in item["children"]:
                if child["type"] == "directory":
                    # Create directory
                    child_path = target_path / child["name"]
                    child_path.mkdir(exist_ok=True)
                    
                    # Process children
                    self._create_folder_structure_recursive(child, child_path)
    
    def get_relative_path(self, path: str) -> str:
        """
        Get path relative to course directory
        
        Args:
            path: Absolute path
            
        Returns:
            str: Relative path
        """
        return str(Path(path).relative_to(self.course_dir))
    
    def get_timestamp_for_file(self, file_path: str) -> str:
        """
        Get timestamp for a file
        
        Args:
            file_path: File path
            
        Returns:
            str: Timestamp in format HH:MM:SS
        """
        if not self.timestamps:
            self.calculate_timestamps()
        
        return self.timestamps.get(file_path, {}).get("timestamp", "00:00:00")
    
    def get_audio_output_path(self, file_path: str, output_dir: str) -> Path:
        """
        Get output path for audio file
        
        Args:
            file_path: Original file path
            output_dir: Output directory
            
        Returns:
            Path: Output path
        """
        # Get relative path
        rel_path = self.get_relative_path(file_path)
        
        # Create output path
        output_path = Path(output_dir).expanduser() / self.course_name / Path(rel_path)
        
        # Change extension to .mp3
        output_path = output_path.with_suffix('.mp3')
        
        return output_path
    
    def validate_file_integrity(self, file_path: Path) -> bool:
        """
        Validate file integrity
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return False
            
            # Check if file is empty
            if file_path.stat().st_size == 0:
                return False
            
            # For audio and video files, check if they can be opened
            if file_path.suffix.lower() in {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a',
                                          '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}:
                try:
                    # Try to get duration
                    duration = get_audio_duration(file_path)
                    return duration > 0
                except Exception:
                    return False
            
            # For other files, just check if they exist and are not empty
            return True
        except Exception as e:
            logger.error(f"Error validating file integrity for {file_path}: {str(e)}")
            return False