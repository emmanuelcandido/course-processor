"""
Settings management for Curso Processor

This module provides comprehensive configuration management for the Curso Processor
application, including loading, saving, validating, and resetting settings.
"""

import os
import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS = {
    "directories": {
        "work_directory": os.getcwd(),
        "github_local": os.path.expanduser("~/Github/Feeds"),
        "xml_output": os.path.expanduser("~/Documents/CURSO_PROCESSOR"),
        "audio_cache": "./temp/audio_cache",
        "video_input": os.path.expanduser("~/Videos/curso_input"),
        "audio_output": os.path.expanduser("~/Audio/curso_output"),
        "transcription_output": os.path.expanduser("~/Documents/curso_transcriptions"),
        "processed_output": os.path.expanduser("~/Documents/curso_processed"),
        "tts_output": os.path.expanduser("~/Audio/curso_tts"),
        "timestamps_output": os.path.expanduser("~/Documents/curso_timestamps")
    },
    "language": {
        "interface": "pt-BR",
        "tts_language": "pt-BR", 
        "tts_voice": "pt-BR-FranciscaNeural"
    },
    "processing": {
        "audio_quality": 128,
        "max_tokens_per_request": 100000,
        "batch_size": 5,
        "auto_cleanup": True
    },
    "xml": {
        "feed_name": "cursos.xml",
        "feed_title": "Meus Cursos Processados",
        "feed_description": "Feed automático de cursos processados"
    },
    "tts": {
        "rate": 180,
        "volume": 1.0,
        "pitch": 0
    },
    "ai": {
        "default_provider": "openai",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "history": {
        "max_entries": 50,
        "auto_backup": True
    },
    "system": {
        "version": "1.0.0",
        "last_update_check": None,
        "auto_update": True
    }
}

# Settings file path
SETTINGS_FILE = Path(__file__).parent.parent / "data" / "settings.json"
SETTINGS_BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


class ConfigManager:
    """
    Configuration manager for Curso Processor
    
    This class provides methods for loading, saving, validating, and resetting
    application settings, as well as importing and exporting configurations.
    """
    
    def __init__(self, settings_file: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager
        
        Args:
            settings_file: Path to settings file (optional)
        """
        self.settings_file = Path(settings_file) if settings_file else SETTINGS_FILE
        self.settings = self.load_settings()
        
        # Create backup directory if it doesn't exist
        os.makedirs(SETTINGS_BACKUP_DIR, exist_ok=True)
        
        # Auto-update settings with new keys from defaults
        self._update_with_new_defaults()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file
        
        Returns:
            Dict[str, Any]: Current settings
        """
        # Create settings directory if it doesn't exist
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        # Create settings file with defaults if it doesn't exist
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_SETTINGS, f, indent=4)
            return DEFAULT_SETTINGS.copy()
        
        # Load settings from file
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return settings
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading settings: {e}")
            # Create backup of corrupted file
            if os.path.exists(self.settings_file):
                backup_file = f"{self.settings_file}.corrupted"
                shutil.copy2(self.settings_file, backup_file)
                logger.info(f"Corrupted settings file backed up to {backup_file}")
            
            # Return defaults
            return DEFAULT_SETTINGS.copy()
    
    def save_settings(self, settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save settings to file
        
        Args:
            settings: Settings to save (optional, uses current settings if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if settings is None:
            settings = self.settings
        
        try:
            # Create backup before saving
            if os.path.exists(self.settings_file):
                self._create_backup()
            
            # Save settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            
            # Update current settings
            self.settings = settings
            
            return True
        except IOError as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        Reset settings to defaults
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create backup before resetting
            if os.path.exists(self.settings_file):
                self._create_backup()
            
            # Reset to defaults
            self.settings = DEFAULT_SETTINGS.copy()
            
            # Save defaults
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_SETTINGS, f, indent=4)
            
            return True
        except IOError as e:
            logger.error(f"Error resetting settings: {e}")
            return False
    
    def validate_paths(self) -> Dict[str, bool]:
        """
        Validate directory paths
        
        Returns:
            Dict[str, bool]: Dictionary of directory names and their validity
        """
        results = {}
        
        for name, path in self.settings.get("directories", {}).items():
            # Expand user directory if needed
            expanded_path = os.path.expanduser(path)
            
            # Check if directory exists
            exists = os.path.exists(expanded_path)
            
            # Try to create directory if it doesn't exist
            if not exists:
                try:
                    os.makedirs(expanded_path, exist_ok=True)
                    exists = True
                except OSError:
                    exists = False
            
            results[name] = exists
        
        return results
    
    def create_missing_directories(self) -> Dict[str, bool]:
        """
        Create missing directories
        
        Returns:
            Dict[str, bool]: Dictionary of directory names and creation success
        """
        results = {}
        
        for name, path in self.settings.get("directories", {}).items():
            # Expand user directory if needed
            expanded_path = os.path.expanduser(path)
            
            # Check if directory exists
            exists = os.path.exists(expanded_path)
            
            # Try to create directory if it doesn't exist
            if not exists:
                try:
                    os.makedirs(expanded_path, exist_ok=True)
                    results[name] = True
                except OSError:
                    results[name] = False
            else:
                results[name] = True
        
        return results
    
    def update_setting(self, key_path: str, value: Any) -> bool:
        """
        Update a specific setting
        
        Args:
            key_path: Dot-separated path to the setting (e.g., "directories.work_directory")
            value: New value for the setting
            
        Returns:
            bool: True if successful, False otherwise
        """
        keys = key_path.split('.')
        
        # Navigate to the correct nested dictionary
        current = self.settings
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Update the value
        current[keys[-1]] = value
        
        # Save settings
        return self.save_settings()
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific setting
        
        Args:
            key_path: Dot-separated path to the setting (e.g., "directories.work_directory")
            default: Default value to return if setting not found
            
        Returns:
            Any: Setting value or default
        """
        keys = key_path.split('.')
        
        # Navigate to the correct nested dictionary
        current = self.settings
        for key in keys:
            if key not in current:
                return default
            current = current[key]
        
        return current
    
    def export_settings(self, export_file: Union[str, Path]) -> bool:
        """
        Export settings to a file
        
        Args:
            export_file: Path to export file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            export_path = Path(export_file)
            
            # Create directory if it doesn't exist
            os.makedirs(export_path.parent, exist_ok=True)
            
            # Export settings
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            
            return True
        except IOError as e:
            logger.error(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, import_file: Union[str, Path]) -> bool:
        """
        Import settings from a file
        
        Args:
            import_file: Path to import file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import_path = Path(import_file)
            
            # Check if file exists
            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return False
            
            # Import settings
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_settings = json.load(f)
            
            # Create backup before importing
            self._create_backup()
            
            # Update settings with imported values
            self.settings = imported_settings
            
            # Save settings
            return self.save_settings()
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error importing settings: {e}")
            return False
    
    def _create_backup(self) -> str:
        """
        Create a backup of the current settings file
        
        Returns:
            str: Path to backup file
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = SETTINGS_BACKUP_DIR / f"settings_{timestamp}.json"
        
        try:
            shutil.copy2(self.settings_file, backup_file)
            logger.info(f"Settings backed up to {backup_file}")
            return str(backup_file)
        except IOError as e:
            logger.error(f"Error creating backup: {e}")
            return ""
    
    def restore_from_backup(self, backup_file: Union[str, Path]) -> bool:
        """
        Restore settings from a backup file
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            backup_path = Path(backup_file)
            
            # Check if file exists
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current settings
            self._create_backup()
            
            # Restore from backup
            shutil.copy2(backup_path, self.settings_file)
            
            # Reload settings
            self.settings = self.load_settings()
            
            return True
        except IOError as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups
        
        Returns:
            List[Dict[str, Any]]: List of backup information
        """
        backups = []
        
        try:
            for file in SETTINGS_BACKUP_DIR.glob("settings_*.json"):
                # Extract timestamp from filename
                timestamp_str = file.stem.replace("settings_", "")
                
                try:
                    # Parse timestamp
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    # Get file size
                    size = file.stat().st_size
                    
                    backups.append({
                        "file": str(file),
                        "timestamp": timestamp,
                        "size": size
                    })
                except ValueError:
                    # Skip files with invalid timestamps
                    continue
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return backups
        except IOError as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def _update_with_new_defaults(self):
        """Update settings with new keys from defaults"""
        updated = False
        
        def update_dict(target, source):
            nonlocal updated
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                    updated = True
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    update_dict(target[key], value)
        
        update_dict(self.settings, DEFAULT_SETTINGS)
        
        if updated:
            logger.info("Settings updated with new default values")
            self.save_settings()


# Create global instance
config_manager = ConfigManager()

def ensure_settings_file():
    """Ensure settings file exists with default values"""
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)

def get_settings() -> Dict[str, Any]:
    """Get current settings"""
    return config_manager.settings

def update_settings(new_settings: Dict[str, Any]) -> bool:
    """
    Update settings
    
    Args:
        new_settings: New settings to merge with current settings
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Deep update settings
    def update_dict(d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                update_dict(d[k], v)
            else:
                d[k] = v
    
    update_dict(config_manager.settings, new_settings)
    
    return config_manager.save_settings()

def get_default_video_dir() -> str:
    """Get default video directory"""
    return config_manager.get_setting("directories.video_input")

def get_default_audio_dir() -> str:
    """Get default audio directory"""
    return config_manager.get_setting("directories.audio_output")

def get_default_transcription_dir() -> str:
    """Get default transcription directory"""
    return config_manager.get_setting("directories.transcription_output")

def get_default_processed_dir() -> str:
    """Get default processed directory"""
    return config_manager.get_setting("directories.processed_output")

def get_default_tts_dir() -> str:
    """Get default TTS directory"""
    return config_manager.get_setting("directories.tts_output")

def get_default_xml_dir() -> str:
    """Get default XML directory"""
    return config_manager.get_setting("directories.xml_output")

def get_default_timestamps_dir() -> str:
    """Get default timestamps directory"""
    return config_manager.get_setting("directories.timestamps_output")

def get_default_github_dir() -> str:
    """Get default GitHub directory"""
    return config_manager.get_setting("directories.github_local")

def get_default_work_dir() -> str:
    """Get default work directory"""
    return config_manager.get_setting("directories.work_directory", os.getcwd())

def get_default_audio_cache_dir() -> str:
    """Get default audio cache directory"""
    return config_manager.get_setting("directories.audio_cache", "./temp/audio_cache")

def get_default_base_dir() -> str:
    """Get default base directory"""
    # Use the parent directory of the video input directory
    video_dir = get_default_video_dir()
    return os.path.dirname(os.path.expanduser(video_dir))

def get_tts_settings() -> Dict[str, Any]:
    """Get TTS settings"""
    return config_manager.get_setting("tts", {})

def get_language_settings() -> Dict[str, Any]:
    """Get language settings"""
    return config_manager.get_setting("language", {})

def get_ai_settings() -> Dict[str, Any]:
    """Get AI settings"""
    return config_manager.get_setting("ai", {})

def get_processing_settings() -> Dict[str, Any]:
    """Get processing settings"""
    return config_manager.get_setting("processing", {})

def get_xml_settings() -> Dict[str, Any]:
    """Get XML settings"""
    return config_manager.get_setting("xml", {})

def get_history_settings() -> Dict[str, Any]:
    """Get history settings"""
    return config_manager.get_setting("history", {})

def get_system_settings() -> Dict[str, Any]:
    """Get system settings"""
    return config_manager.get_setting("system", {})

def update_directory_settings(directory_type: str, path: str) -> bool:
    """
    Update a specific directory setting
    
    Args:
        directory_type: Directory type (e.g., "work_directory", "github_local")
        path: Directory path
        
    Returns:
        bool: True if successful, False otherwise
    """
    return config_manager.update_setting(f"directories.{directory_type}", path)

def update_tts_settings(language: Optional[str] = None, voice: Optional[str] = None, 
                        rate: Optional[int] = None, volume: Optional[float] = None,
                        pitch: Optional[int] = None) -> bool:
    """
    Update TTS settings
    
    Args:
        language: TTS language
        voice: TTS voice
        rate: Speech rate
        volume: Volume level
        pitch: Voice pitch
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    if language is not None:
        success = success and config_manager.update_setting("language.tts_language", language)
    
    if voice is not None:
        success = success and config_manager.update_setting("language.tts_voice", voice)
    
    if rate is not None:
        success = success and config_manager.update_setting("tts.rate", rate)
    
    if volume is not None:
        success = success and config_manager.update_setting("tts.volume", volume)
    
    if pitch is not None:
        success = success and config_manager.update_setting("tts.pitch", pitch)
    
    return success

def update_language_settings(interface: Optional[str] = None, 
                            tts_language: Optional[str] = None,
                            tts_voice: Optional[str] = None) -> bool:
    """
    Update language settings
    
    Args:
        interface: Interface language
        tts_language: TTS language
        tts_voice: TTS voice
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    if interface is not None:
        success = success and config_manager.update_setting("language.interface", interface)
    
    if tts_language is not None:
        success = success and config_manager.update_setting("language.tts_language", tts_language)
    
    if tts_voice is not None:
        success = success and config_manager.update_setting("language.tts_voice", tts_voice)
    
    return success

def update_ai_settings(provider: Optional[str] = None, model: Optional[str] = None,
                      temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> bool:
    """
    Update AI settings
    
    Args:
        provider: AI provider (e.g., "openai", "anthropic")
        model: AI model
        temperature: Temperature parameter
        max_tokens: Maximum tokens
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    if provider is not None:
        success = success and config_manager.update_setting("ai.default_provider", provider)
    
    if model is not None:
        success = success and config_manager.update_setting("ai.model", model)
    
    if temperature is not None:
        success = success and config_manager.update_setting("ai.temperature", temperature)
    
    if max_tokens is not None:
        success = success and config_manager.update_setting("ai.max_tokens", max_tokens)
    
    return success

def update_processing_settings(audio_quality: Optional[int] = None,
                              max_tokens_per_request: Optional[int] = None,
                              batch_size: Optional[int] = None,
                              auto_cleanup: Optional[bool] = None) -> bool:
    """
    Update processing settings
    
    Args:
        audio_quality: Audio quality (bitrate)
        max_tokens_per_request: Maximum tokens per request
        batch_size: Batch size for processing
        auto_cleanup: Auto cleanup flag
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    if audio_quality is not None:
        success = success and config_manager.update_setting("processing.audio_quality", audio_quality)
    
    if max_tokens_per_request is not None:
        success = success and config_manager.update_setting("processing.max_tokens_per_request", max_tokens_per_request)
    
    if batch_size is not None:
        success = success and config_manager.update_setting("processing.batch_size", batch_size)
    
    if auto_cleanup is not None:
        success = success and config_manager.update_setting("processing.auto_cleanup", auto_cleanup)
    
    return success

def update_xml_settings(feed_name: Optional[str] = None,
                       feed_title: Optional[str] = None,
                       feed_description: Optional[str] = None) -> bool:
    """
    Update XML settings
    
    Args:
        feed_name: Feed filename
        feed_title: Feed title
        feed_description: Feed description
        
    Returns:
        bool: True if successful, False otherwise
    """
    success = True
    
    if feed_name is not None:
        success = success and config_manager.update_setting("xml.feed_name", feed_name)
    
    if feed_title is not None:
        success = success and config_manager.update_setting("xml.feed_title", feed_title)
    
    if feed_description is not None:
        success = success and config_manager.update_setting("xml.feed_description", feed_description)
    
    return success

def reset_to_defaults() -> bool:
    """
    Reset settings to defaults
    
    Returns:
        bool: True if successful, False otherwise
    """
    return config_manager.reset_to_defaults()

def validate_paths() -> Dict[str, bool]:
    """
    Validate directory paths
    
    Returns:
        Dict[str, bool]: Dictionary of directory names and their validity
    """
    return config_manager.validate_paths()

def create_missing_directories() -> Dict[str, bool]:
    """
    Create missing directories
    
    Returns:
        Dict[str, bool]: Dictionary of directory names and creation success
    """
    return config_manager.create_missing_directories()

def export_settings(export_file: Union[str, Path]) -> bool:
    """
    Export settings to a file
    
    Args:
        export_file: Path to export file
        
    Returns:
        bool: True if successful, False otherwise
    """
    return config_manager.export_settings(export_file)

def import_settings(import_file: Union[str, Path]) -> bool:
    """
    Import settings from a file
    
    Args:
        import_file: Path to import file
        
    Returns:
        bool: True if successful, False otherwise
    """
    return config_manager.import_settings(import_file)

def list_backups() -> List[Dict[str, Any]]:
    """
    List available backups
    
    Returns:
        List[Dict[str, Any]]: List of backup information
    """
    return config_manager.list_backups()

def restore_from_backup(backup_file: Union[str, Path]) -> bool:
    """
    Restore settings from a backup file
    
    Args:
        backup_file: Path to backup file
        
    Returns:
        bool: True if successful, False otherwise
    """
    return config_manager.restore_from_backup(backup_file)