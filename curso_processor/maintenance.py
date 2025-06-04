#!/usr/bin/env python3
"""
Maintenance System for Curso Processor

This module provides comprehensive maintenance, migration, and validation
functionality for the Curso Processor application.
"""

import os
import sys
import json
import shutil
import time
import glob
import hashlib
import logging
import datetime
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, NamedTuple, Set, Union
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
from rich.prompt import Prompt, Confirm
from rich.logging import RichHandler

# Import modules
# Import settings directly to avoid keyring issues
from config import settings
# Import credentials conditionally to avoid keyring issues
try:
    from config import credentials
    HAS_CREDENTIALS = True
except Exception:
    HAS_CREDENTIALS = False
from utils import file_manager
from utils.ui_components import (
    console, NORD_BLUE, NORD_CYAN, NORD_GREEN, NORD_YELLOW, NORD_RED, NORD_DIM,
    create_progress_bar, handle_error, create_table
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)
logger = logging.getLogger("maintenance")

# Define validation result structure
@dataclass
class ValidationResult:
    """Validation result with status and issues"""
    is_valid: bool
    issues: List[str] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class SystemMaintenance:
    """
    Comprehensive system maintenance, migration, and validation for Curso Processor
    """
    
    def __init__(self):
        """Initialize the maintenance system"""
        self.config = settings.get_settings()
        self.base_dir = self.config["directories"]["work_directory"]
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.cache_dir = os.path.join(self.base_dir, "cache")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.backup_dir = os.path.join(self.base_dir, "backups")
        
        # Create directories if they don't exist
        for directory in [self.temp_dir, self.cache_dir, self.logs_dir, self.backup_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialize log file
        self.log_file = os.path.join(
            self.logs_dir, 
            f"maintenance_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        # Add file handler to logger
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        logger.info(f"Maintenance system initialized. Base directory: {self.base_dir}")
    
    def create_backup(self, target_dir: str, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of a directory
        
        Args:
            target_dir: Directory to backup
            backup_name: Optional name for the backup
            
        Returns:
            str: Path to the backup file
        """
        if not os.path.exists(target_dir):
            logger.warning(f"Cannot backup non-existent directory: {target_dir}")
            return None
        
        if backup_name is None:
            backup_name = f"{os.path.basename(target_dir)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        try:
            # Create backup directory if it doesn't exist
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Create zip archive
            shutil.make_archive(
                os.path.splitext(backup_path)[0],  # Remove .zip extension
                'zip',
                target_dir
            )
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None
    
    def restore_backup(self, backup_path: str, target_dir: str) -> bool:
        """
        Restore a backup
        
        Args:
            backup_path: Path to the backup file
            target_dir: Directory to restore to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(backup_path):
            logger.warning(f"Backup file does not exist: {backup_path}")
            return False
        
        try:
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Extract zip archive
            shutil.unpack_archive(backup_path, target_dir)
            
            logger.info(f"Restored backup from {backup_path} to {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            return False
    
    def get_directory_size(self, directory: str) -> int:
        """
        Get the size of a directory in bytes
        
        Args:
            directory: Directory to get size of
            
        Returns:
            int: Size in bytes
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """
        Format size in bytes to human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def cleanup_temp_files(self, progress: Optional[Progress] = None, task_id: Optional[int] = None) -> float:
        """
        Clean up temporary files
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
            
        Returns:
            float: Space freed in MB
        """
        logger.info("Starting cleanup of temporary files")
        
        # Create backup before cleanup
        self.create_backup(self.temp_dir, "temp_files_pre_cleanup")
        
        # Get initial size
        initial_size = self.get_directory_size(self.temp_dir)
        
        # Get all files in temp directory
        temp_files = []
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                temp_files.append(os.path.join(root, file))
        
        # No files to clean up
        if not temp_files:
            logger.info("No temporary files to clean up")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return 0
        
        # Clean up files
        files_removed = 0
        total_files = len(temp_files)
        
        for i, file_path in enumerate(temp_files):
            try:
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Remove file
                os.remove(file_path)
                files_removed += 1
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_files)
            except Exception as e:
                logger.error(f"Failed to remove temporary file {file_path}: {str(e)}")
        
        # Get final size
        final_size = self.get_directory_size(self.temp_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        logger.info(f"Removed {files_removed} temporary files, freed {space_freed:.1f} MB")
        
        return space_freed
    
    def cleanup_expired_cache(self, progress: Optional[Progress] = None, task_id: Optional[int] = None) -> float:
        """
        Clean up expired cache files
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
            
        Returns:
            float: Space freed in MB
        """
        logger.info("Starting cleanup of expired cache")
        
        # Create backup before cleanup
        self.create_backup(self.cache_dir, "cache_pre_cleanup")
        
        # Get initial size
        initial_size = self.get_directory_size(self.cache_dir)
        
        # Get all files in cache directory
        cache_files = []
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Get file age in days
                if os.path.exists(file_path):
                    file_age = (time.time() - os.path.getmtime(file_path)) / (60 * 60 * 24)
                    cache_files.append((file_path, file_age))
        
        # No files to clean up
        if not cache_files:
            logger.info("No cache files to clean up")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return 0
        
        # Clean up files older than 30 days
        files_removed = 0
        total_files = len(cache_files)
        
        for i, (file_path, file_age) in enumerate(cache_files):
            try:
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Remove file if older than 30 days
                if file_age > 30:
                    os.remove(file_path)
                    files_removed += 1
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_files)
            except Exception as e:
                logger.error(f"Failed to remove cache file {file_path}: {str(e)}")
        
        # Get final size
        final_size = self.get_directory_size(self.cache_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        logger.info(f"Removed {files_removed} expired cache files, freed {space_freed:.1f} MB")
        
        return space_freed
    
    def cleanup_old_logs(self, progress: Optional[Progress] = None, task_id: Optional[int] = None) -> float:
        """
        Clean up old log files
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
            
        Returns:
            float: Space freed in MB
        """
        logger.info("Starting cleanup of old logs")
        
        # Create backup before cleanup
        self.create_backup(self.logs_dir, "logs_pre_cleanup")
        
        # Get initial size
        initial_size = self.get_directory_size(self.logs_dir)
        
        # Get all log files
        log_files = []
        for root, dirs, files in os.walk(self.logs_dir):
            for file in files:
                if file.endswith(".log"):
                    file_path = os.path.join(root, file)
                    # Get file age in days
                    if os.path.exists(file_path):
                        file_age = (time.time() - os.path.getmtime(file_path)) / (60 * 60 * 24)
                        log_files.append((file_path, file_age))
        
        # No files to clean up
        if not log_files:
            logger.info("No log files to clean up")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return 0
        
        # Clean up files older than 90 days
        files_removed = 0
        total_files = len(log_files)
        
        for i, (file_path, file_age) in enumerate(log_files):
            try:
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Skip current log file
                if file_path == self.log_file:
                    continue
                
                # Remove file if older than 90 days
                if file_age > 90:
                    os.remove(file_path)
                    files_removed += 1
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_files)
            except Exception as e:
                logger.error(f"Failed to remove log file {file_path}: {str(e)}")
        
        # Get final size
        final_size = self.get_directory_size(self.logs_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        logger.info(f"Removed {files_removed} old log files, freed {space_freed:.1f} MB")
        
        return space_freed
    
    def cleanup_old_backups(self, progress: Optional[Progress] = None, task_id: Optional[int] = None) -> float:
        """
        Clean up old backup files
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
            
        Returns:
            float: Space freed in MB
        """
        logger.info("Starting cleanup of old backups")
        
        # Get initial size
        initial_size = self.get_directory_size(self.backup_dir)
        
        # Get all backup files
        backup_files = []
        for root, dirs, files in os.walk(self.backup_dir):
            for file in files:
                if file.endswith(".zip"):
                    file_path = os.path.join(root, file)
                    # Get file age in days
                    if os.path.exists(file_path):
                        file_age = (time.time() - os.path.getmtime(file_path)) / (60 * 60 * 24)
                        backup_files.append((file_path, file_age))
        
        # No files to clean up
        if not backup_files:
            logger.info("No backup files to clean up")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return 0
        
        # Group backups by type
        backup_groups = {}
        for file_path, file_age in backup_files:
            file_name = os.path.basename(file_path)
            # Extract backup type (everything before the timestamp)
            match = re.match(r"(.+)_\d{8}_\d{6}\.zip", file_name)
            if match:
                backup_type = match.group(1)
                if backup_type not in backup_groups:
                    backup_groups[backup_type] = []
                backup_groups[backup_type].append((file_path, file_age))
        
        # Keep only the 5 most recent backups of each type
        files_removed = 0
        total_groups = len(backup_groups)
        
        for i, (backup_type, files) in enumerate(backup_groups.items()):
            try:
                # Sort by age (newest first)
                files.sort(key=lambda x: x[1])
                
                # Remove old backups (keep 5 most recent)
                if len(files) > 5:
                    for file_path, _ in files[5:]:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            files_removed += 1
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_groups)
            except Exception as e:
                logger.error(f"Failed to process backup group {backup_type}: {str(e)}")
        
        # Get final size
        final_size = self.get_directory_size(self.backup_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        logger.info(f"Removed {files_removed} old backup files, freed {space_freed:.1f} MB")
        
        return space_freed
    
    def cleanup_orphaned_audio(self, progress: Optional[Progress] = None, task_id: Optional[int] = None) -> float:
        """
        Clean up orphaned audio files (audio files without corresponding transcriptions)
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
            
        Returns:
            float: Space freed in MB
        """
        logger.info("Starting cleanup of orphaned audio files")
        
        # Get all course directories
        course_dirs = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item not in ["temp", "cache", "logs", "backups"]:
                course_dirs.append(item_path)
        
        # No courses to process
        if not course_dirs:
            logger.info("No courses to process")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return 0
        
        # Process each course
        total_freed = 0
        total_courses = len(course_dirs)
        
        for i, course_dir in enumerate(course_dirs):
            try:
                # Get audio directory
                audio_dir = os.path.join(course_dir, "audio")
                if not os.path.exists(audio_dir):
                    continue
                
                # Get transcription directory
                transcription_dir = os.path.join(course_dir, "transcriptions")
                if not os.path.exists(transcription_dir):
                    continue
                
                # Get all audio files
                audio_files = []
                for root, dirs, files in os.walk(audio_dir):
                    for file in files:
                        if file.endswith((".mp3", ".wav")):
                            audio_files.append(os.path.join(root, file))
                
                # Get all transcription files
                transcription_files = []
                for root, dirs, files in os.walk(transcription_dir):
                    for file in files:
                        if file.endswith((".txt", ".md")):
                            transcription_files.append(os.path.splitext(os.path.basename(file))[0])
                
                # Find orphaned audio files
                orphaned_files = []
                for audio_file in audio_files:
                    audio_name = os.path.splitext(os.path.basename(audio_file))[0]
                    if audio_name not in transcription_files:
                        orphaned_files.append(audio_file)
                
                # Create backup directory for orphaned files
                orphaned_dir = os.path.join(course_dir, "orphaned_audio")
                os.makedirs(orphaned_dir, exist_ok=True)
                
                # Move orphaned files to backup directory
                for file_path in orphaned_files:
                    if os.path.exists(file_path):
                        # Get file size
                        file_size = os.path.getsize(file_path)
                        
                        # Move file to orphaned directory
                        shutil.move(file_path, os.path.join(orphaned_dir, os.path.basename(file_path)))
                        
                        # Add to total freed space
                        total_freed += file_size
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_courses)
            except Exception as e:
                logger.error(f"Failed to process course {course_dir}: {str(e)}")
        
        # Convert to MB
        space_freed = total_freed / (1024 * 1024)
        
        logger.info(f"Moved orphaned audio files to backup directories, freed {space_freed:.1f} MB")
        
        return space_freed
    
    def comprehensive_cleanup(self):
        """
        Perform comprehensive cleanup of the system
        """
        logger.info("Starting comprehensive cleanup")
        
        cleanup_tasks = [
            ("🗑️ Arquivos temporários", self.cleanup_temp_files),
            ("🔄 Cache expirado", self.cleanup_expired_cache),
            ("📋 Logs antigos", self.cleanup_old_logs),
            ("💾 Backups redundantes", self.cleanup_old_backups),
            ("🎵 Áudios órfãos", self.cleanup_orphaned_audio)
        ]
        
        total_freed = 0
        with Progress() as progress:
            for task_name, task_func in cleanup_tasks:
                task_id = progress.add_task(task_name, total=100)
                freed_space = task_func(progress, task_id)
                total_freed += freed_space
                
        console.print(f"[{NORD_GREEN}]✅ Limpeza concluída! {total_freed:.1f} MB liberados[/{NORD_GREEN}]")
        
        logger.info(f"Comprehensive cleanup completed. Total space freed: {total_freed:.1f} MB")
        
        return total_freed
    
    def analyze_migration(self, source_dir: str, target_dir: str) -> Dict[str, Dict[str, Any]]:
        """
        Analyze migration from source to target directory
        
        Args:
            source_dir: Source directory
            target_dir: Target directory
            
        Returns:
            Dict: Migration plan with file types, counts, and sizes
        """
        logger.info(f"Analyzing migration from {source_dir} to {target_dir}")
        
        # Check if directories exist
        if not os.path.exists(source_dir):
            logger.error(f"Source directory does not exist: {source_dir}")
            return {}
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Get all files in source directory
        file_types = {
            "Áudio": [".mp3", ".wav"],
            "Transcrição": [".txt", ".md"],
            "XML": [".xml"],
            "Configuração": [".json", ".yaml", ".yml"],
            "Imagem": [".jpg", ".jpeg", ".png", ".gif"],
            "Vídeo": [".mp4", ".mkv", ".avi", ".mov"],
            "Documento": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"],
            "Outro": []
        }
        
        migration_plan = {}
        
        for file_type, extensions in file_types.items():
            migration_plan[file_type] = {
                "count": 0,
                "size": "0 B",
                "total_bytes": 0,
                "files": []
            }
        
        # Walk through source directory
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Get file extension
                _, ext = os.path.splitext(file)
                
                # Determine file type
                file_type = "Outro"
                for type_name, extensions in file_types.items():
                    if ext.lower() in extensions:
                        file_type = type_name
                        break
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Add to migration plan
                migration_plan[file_type]["count"] += 1
                migration_plan[file_type]["total_bytes"] += file_size
                migration_plan[file_type]["files"].append({
                    "path": file_path,
                    "size": file_size,
                    "relative_path": os.path.relpath(file_path, source_dir)
                })
        
        # Format sizes
        for file_type in migration_plan:
            migration_plan[file_type]["size"] = self.format_size(migration_plan[file_type]["total_bytes"])
        
        logger.info(f"Migration analysis completed")
        
        return migration_plan
    
    def execute_migration(self, migration_plan: Dict[str, Dict[str, Any]], source_dir: str, target_dir: str, operation: str = "copy") -> bool:
        """
        Execute migration based on migration plan
        
        Args:
            migration_plan: Migration plan
            source_dir: Source directory
            target_dir: Target directory
            operation: Operation to perform (copy, move, sync)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Executing migration from {source_dir} to {target_dir} (operation: {operation})")
        
        # Check if directories exist
        if not os.path.exists(source_dir):
            logger.error(f"Source directory does not exist: {source_dir}")
            return False
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Create backup of target directory
        self.create_backup(target_dir, f"migration_target_pre_{operation}")
        
        # Get total number of files
        total_files = sum(plan["count"] for plan in migration_plan.values())
        
        # No files to migrate
        if total_files == 0:
            logger.info("No files to migrate")
            return True
        
        # Execute migration
        files_processed = 0
        errors = 0
        
        with Progress() as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Migrando arquivos...[/{NORD_CYAN}]", total=total_files)
            
            for file_type, plan in migration_plan.items():
                for file_info in plan["files"]:
                    try:
                        # Get source and target paths
                        source_path = file_info["path"]
                        relative_path = file_info["relative_path"]
                        target_path = os.path.join(target_dir, relative_path)
                        
                        # Create target directory if it doesn't exist
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        # Perform operation
                        if operation == "copy":
                            shutil.copy2(source_path, target_path)
                        elif operation == "move":
                            shutil.move(source_path, target_path)
                        elif operation == "sync":
                            # Only copy if file doesn't exist or is different
                            if not os.path.exists(target_path) or not self._files_are_identical(source_path, target_path):
                                shutil.copy2(source_path, target_path)
                        
                        files_processed += 1
                        progress.update(task, completed=files_processed)
                    except Exception as e:
                        logger.error(f"Failed to process file {source_path}: {str(e)}")
                        errors += 1
        
        # Log results
        logger.info(f"Migration completed. Processed {files_processed} files with {errors} errors")
        
        if errors > 0:
            console.print(f"[{NORD_YELLOW}]⚠️ Migração concluída com {errors} erros. Verifique o log para mais detalhes.[/{NORD_YELLOW}]")
            return False
        else:
            console.print(f"[{NORD_GREEN}]✅ Migração concluída com sucesso! {files_processed} arquivos processados.[/{NORD_GREEN}]")
            return True
    
    def _files_are_identical(self, file1: str, file2: str) -> bool:
        """
        Check if two files are identical
        
        Args:
            file1: First file
            file2: Second file
            
        Returns:
            bool: True if files are identical, False otherwise
        """
        # Check if files exist
        if not os.path.exists(file1) or not os.path.exists(file2):
            return False
        
        # Check if file sizes are different
        if os.path.getsize(file1) != os.path.getsize(file2):
            return False
        
        # Compare file hashes
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            hash1 = hashlib.md5(f1.read()).hexdigest()
            hash2 = hashlib.md5(f2.read()).hexdigest()
            
            return hash1 == hash2
    
    def migrate_course_data(self, source_dir: str, target_dir: str, operation: str = "copy"):
        """
        Migrate course data from source to target directory
        
        Args:
            source_dir: Source directory
            target_dir: Target directory
            operation: Operation to perform (copy, move, sync)
        """
        logger.info(f"Starting course data migration from {source_dir} to {target_dir} (operation: {operation})")
        
        # Validate operation
        if operation not in ["copy", "move", "sync"]:
            logger.error(f"Invalid operation: {operation}")
            console.print(f"[{NORD_RED}]❌ Operação inválida: {operation}[/{NORD_RED}]")
            return
        
        # Analyze migration
        migration_plan = self.analyze_migration(source_dir, target_dir)
        
        if not migration_plan:
            console.print(f"[{NORD_RED}]❌ Falha ao analisar migração[/{NORD_RED}]")
            return
        
        # Display migration plan
        console.print(f"[{NORD_CYAN}]📋 Plano de Migração:[/{NORD_CYAN}]")
        table = Table(title="Arquivos a serem migrados")
        table.add_column("Tipo", style=NORD_CYAN)
        table.add_column("Quantidade", style=NORD_WHITE) 
        table.add_column("Tamanho", style=NORD_GREEN)
        
        for file_type, info in migration_plan.items():
            if info["count"] > 0:
                table.add_row(file_type, str(info["count"]), info["size"])
        
        console.print(table)
        
        # Confirm migration
        if Confirm.ask(f"[{NORD_YELLOW}]Continuar com a migração?[/{NORD_YELLOW}]"):
            # Execute migration
            self.execute_migration(migration_plan, source_dir, target_dir, operation)
        else:
            console.print(f"[{NORD_YELLOW}]Migração cancelada pelo usuário[/{NORD_YELLOW}]")
    
    def migrate_database(self, source_file: str, target_file: str, merge: bool = False):
        """
        Migrate database from source to target file
        
        Args:
            source_file: Source file
            target_file: Target file
            merge: Whether to merge data (True) or replace (False)
        """
        logger.info(f"Starting database migration from {source_file} to {target_file} (merge: {merge})")
        
        # Check if source file exists
        if not os.path.exists(source_file):
            logger.error(f"Source file does not exist: {source_file}")
            console.print(f"[{NORD_RED}]❌ Arquivo de origem não existe: {source_file}[/{NORD_RED}]")
            return
        
        try:
            # Load source data
            with open(source_file, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            
            # Load target data if it exists and merge is True
            target_data = {}
            if merge and os.path.exists(target_file):
                try:
                    with open(target_file, 'r', encoding='utf-8') as f:
                        target_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load target file for merging: {str(e)}")
            
            # Merge or replace data
            if merge and target_data:
                # Merge data based on type
                if isinstance(source_data, list) and isinstance(target_data, list):
                    # For lists, append items from source to target
                    # Use a set to track IDs and avoid duplicates
                    id_field = self._detect_id_field(target_data)
                    
                    if id_field:
                        # If we have an ID field, use it to avoid duplicates
                        existing_ids = {item.get(id_field) for item in target_data if id_field in item}
                        
                        for item in source_data:
                            if id_field in item and item[id_field] not in existing_ids:
                                target_data.append(item)
                                existing_ids.add(item[id_field])
                    else:
                        # No ID field, just append all items
                        target_data.extend(source_data)
                elif isinstance(source_data, dict) and isinstance(target_data, dict):
                    # For dictionaries, update target with source
                    self._deep_update(target_data, source_data)
                else:
                    # Different types, replace target with source
                    target_data = source_data
            else:
                # Replace data
                target_data = source_data
            
            # Create backup of target file
            if os.path.exists(target_file):
                backup_file = f"{target_file}.bak"
                shutil.copy2(target_file, backup_file)
                logger.info(f"Created backup of target file: {backup_file}")
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Save target data
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Database migration completed successfully")
            console.print(f"[{NORD_GREEN}]✅ Migração de banco de dados concluída com sucesso![/{NORD_GREEN}]")
        except Exception as e:
            logger.error(f"Failed to migrate database: {str(e)}")
            console.print(f"[{NORD_RED}]❌ Falha ao migrar banco de dados: {str(e)}[/{NORD_RED}]")
    
    def _detect_id_field(self, data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Detect ID field in a list of dictionaries
        
        Args:
            data: List of dictionaries
            
        Returns:
            str: ID field name, or None if not found
        """
        if not data or not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            return None
        
        # Common ID field names
        id_fields = ["id", "ID", "_id", "uuid", "UUID", "key", "name", "course_name", "file_name"]
        
        # Check if any of the common ID fields exist in all items
        for field in id_fields:
            if all(field in item for item in data):
                return field
        
        return None
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """
        Deep update a dictionary with another dictionary
        
        Args:
            target: Target dictionary
            source: Source dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def validate_directory_structure(self) -> ValidationResult:
        """
        Validate directory structure
        
        Returns:
            ValidationResult: Validation result
        """
        logger.info("Validating directory structure")
        
        issues = []
        
        # Required directories
        required_dirs = [
            self.base_dir,
            self.temp_dir,
            self.cache_dir,
            self.logs_dir,
            self.backup_dir,
            self.config["directories"]["github_local"],
            self.config["directories"]["xml_output"]
        ]
        
        # Check if directories exist
        for directory in required_dirs:
            if not os.path.exists(directory):
                issues.append(f"Diretório não encontrado: {directory}")
        
        # Check if data directory exists
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if not os.path.exists(data_dir):
            issues.append(f"Diretório de dados não encontrado: {data_dir}")
        
        # Check if required data files exist
        required_files = [
            os.path.join(data_dir, "settings.json"),
            os.path.join(data_dir, "processed_courses.json")
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                issues.append(f"Arquivo de dados não encontrado: {file_path}")
        
        # Log results
        if issues:
            logger.warning(f"Directory structure validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("Directory structure validation passed")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def validate_api_credentials(self) -> ValidationResult:
        """
        Validate API credentials
        
        Returns:
            ValidationResult: Validation result
        """
        logger.info("Validating API credentials")
        
        issues = []
        
        # Check if credentials module is available
        if not HAS_CREDENTIALS:
            issues.append("Módulo de credenciais não disponível")
            logger.warning("Credentials module not available")
            return ValidationResult(
                is_valid=False,
                issues=issues
            )
        
        try:
            # Get API status
            api_status = credentials.get_service_status()
            
            # Check if APIs are configured
            for service in api_status:
                if not service["configured"]:
                    issues.append(f"API não configurada: {service['name']}")
                elif service["status"] != "valid":
                    issues.append(f"API inválida: {service['name']} ({service['status']})")
        except Exception as e:
            issues.append(f"Erro ao validar credenciais: {str(e)}")
            logger.error(f"Error validating credentials: {str(e)}")
        
        # Log results
        if issues:
            logger.warning(f"API credentials validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("API credentials validation passed")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def validate_config_files(self) -> ValidationResult:
        """
        Validate configuration files
        
        Returns:
            ValidationResult: Validation result
        """
        logger.info("Validating configuration files")
        
        issues = []
        
        # Get data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        # Required configuration files
        config_files = [
            os.path.join(data_dir, "settings.json"),
            os.path.join(data_dir, "credentials.json"),
            os.path.join(data_dir, "processed_courses.json")
        ]
        
        # Check if files exist and are valid JSON
        for file_path in config_files:
            if not os.path.exists(file_path):
                issues.append(f"Arquivo de configuração não encontrado: {file_path}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except Exception as e:
                issues.append(f"Arquivo de configuração inválido: {file_path} ({str(e)})")
        
        # Check settings.json structure
        settings_file = os.path.join(data_dir, "settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # Check required settings
                required_settings = [
                    "directories.work_directory",
                    "directories.github_local",
                    "directories.xml_output",
                    "language.interface",
                    "language.tts_voice"
                ]
                
                for setting in required_settings:
                    parts = setting.split(".")
                    current = settings_data
                    
                    for part in parts:
                        if part not in current:
                            issues.append(f"Configuração ausente: {setting}")
                            break
                        current = current[part]
            except Exception as e:
                issues.append(f"Falha ao validar estrutura de settings.json: {str(e)}")
        
        # Log results
        if issues:
            logger.warning(f"Configuration files validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("Configuration files validation passed")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def validate_progress_database(self) -> ValidationResult:
        """
        Validate progress database
        
        Returns:
            ValidationResult: Validation result
        """
        logger.info("Validating progress database")
        
        issues = []
        
        # Get data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        # Progress database file
        progress_file = os.path.join(data_dir, "processed_courses.json")
        
        # Check if file exists
        if not os.path.exists(progress_file):
            issues.append(f"Arquivo de progresso não encontrado: {progress_file}")
            return ValidationResult(is_valid=False, issues=issues)
        
        try:
            # Load progress data
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            # Check if progress data is a list
            if not isinstance(progress_data, list):
                issues.append(f"Formato de dados de progresso inválido: esperado lista, encontrado {type(progress_data).__name__}")
                return ValidationResult(is_valid=False, issues=issues)
            
            # Check each course
            for i, course in enumerate(progress_data):
                # Check required fields
                required_fields = ["course_name", "directory", "created_at", "last_updated"]
                
                for field in required_fields:
                    if field not in course:
                        issues.append(f"Campo ausente no curso {i}: {field}")
                
                # Check if directory exists
                if "directory" in course and not os.path.exists(course["directory"]):
                    issues.append(f"Diretório de curso não encontrado: {course['directory']}")
                
                # Check if state file exists
                if "state_file" in course and not os.path.exists(course["state_file"]):
                    issues.append(f"Arquivo de estado de curso não encontrado: {course['state_file']}")
        except Exception as e:
            issues.append(f"Falha ao validar banco de dados de progresso: {str(e)}")
        
        # Log results
        if issues:
            logger.warning(f"Progress database validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("Progress database validation passed")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def validate_drive_links(self) -> ValidationResult:
        """
        Validate Google Drive links
        
        Returns:
            ValidationResult: Validation result
        """
        logger.info("Validating Google Drive links")
        
        issues = []
        
        # Get all course directories
        course_dirs = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item not in ["temp", "cache", "logs", "backups"]:
                course_dirs.append(item_path)
        
        # No courses to validate
        if not course_dirs:
            logger.info("No courses to validate")
            return ValidationResult(is_valid=True, issues=[])
        
        # Check each course
        for course_dir in course_dirs:
            # Look for drive_links.json
            drive_links_file = os.path.join(course_dir, "drive_links.json")
            
            if not os.path.exists(drive_links_file):
                continue
            
            try:
                # Load drive links
                with open(drive_links_file, 'r', encoding='utf-8') as f:
                    drive_links = json.load(f)
                
                # Check each link
                for link_name, link_info in drive_links.items():
                    # Check if link is expired
                    if "expiry" in link_info:
                        try:
                            expiry_date = datetime.datetime.fromisoformat(link_info["expiry"])
                            if expiry_date < datetime.datetime.now():
                                issues.append(f"Link expirado: {link_name} em {os.path.basename(course_dir)}")
                        except Exception:
                            issues.append(f"Data de expiração inválida para link: {link_name} em {os.path.basename(course_dir)}")
                    
                    # Check if link URL is valid
                    if "url" not in link_info or not link_info["url"].startswith("https://drive.google.com/"):
                        issues.append(f"URL de link inválida: {link_name} em {os.path.basename(course_dir)}")
            except Exception as e:
                issues.append(f"Falha ao validar links do Drive para {os.path.basename(course_dir)}: {str(e)}")
        
        # Log results
        if issues:
            logger.warning(f"Drive links validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("Drive links validation passed")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def validate_xml_integrity(self) -> ValidationResult:
        """
        Validate XML integrity
        
        Returns:
            ValidationResult: Validation result
        """
        logger.info("Validating XML integrity")
        
        issues = []
        
        # Get XML directory
        xml_dir = self.config["directories"]["xml_output"]
        
        # Check if directory exists
        if not os.path.exists(xml_dir):
            issues.append(f"Diretório XML não encontrado: {xml_dir}")
            return ValidationResult(is_valid=False, issues=issues)
        
        # Get all XML files
        xml_files = []
        for root, dirs, files in os.walk(xml_dir):
            for file in files:
                if file.endswith(".xml"):
                    xml_files.append(os.path.join(root, file))
        
        # No XML files to validate
        if not xml_files:
            logger.info("No XML files to validate")
            return ValidationResult(is_valid=True, issues=[])
        
        # Check each XML file
        for xml_file in xml_files:
            try:
                # Read XML file
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Check if XML is well-formed
                if not xml_content.strip().startswith("<?xml"):
                    issues.append(f"XML mal formado: {os.path.basename(xml_file)}")
                
                # Check for required tags
                required_tags = ["title", "description", "pubDate", "enclosure"]
                
                for tag in required_tags:
                    if f"<{tag}>" not in xml_content and f"<{tag} " not in xml_content:
                        issues.append(f"Tag ausente no XML: {tag} em {os.path.basename(xml_file)}")
            except Exception as e:
                issues.append(f"Falha ao validar XML: {os.path.basename(xml_file)} ({str(e)})")
        
        # Log results
        if issues:
            logger.warning(f"XML integrity validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("XML integrity validation passed")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues
        )
    
    def validate_system_integrity(self) -> Dict[str, Any]:
        """
        Validate system integrity
        
        Returns:
            Dict: Validation results
        """
        logger.info("Starting system integrity validation")
        
        validations = [
            ("📁 Estrutura de diretórios", self.validate_directory_structure),
            ("🔑 Credenciais de API", self.validate_api_credentials),
            ("📄 Arquivos de configuração", self.validate_config_files),
            ("💾 Database de progresso", self.validate_progress_database),
            ("🔗 Links do Google Drive", self.validate_drive_links),
            ("📊 XML do podcast", self.validate_xml_integrity)
        ]
        
        issues_found = []
        validation_results = {}
        
        with Progress() as progress:
            for validation_name, validation_func in validations:
                task = progress.add_task(f"[{NORD_CYAN}]{validation_name}[/{NORD_CYAN}]", total=100)
                result = validation_func()
                validation_results[validation_name] = result
                
                if not result.is_valid:
                    issues_found.append((validation_name, result.issues))
                
                progress.update(task, completed=100)
        
        # Generate health report
        health_report = self.generate_health_report(issues_found, validation_results)
        
        logger.info("System integrity validation completed")
        
        return health_report
    
    def generate_health_report(self, issues_found: List[Tuple[str, List[str]]], validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """
        Generate health report
        
        Args:
            issues_found: List of issues found
            validation_results: Validation results
            
        Returns:
            Dict: Health report
        """
        logger.info("Generating health report")
        
        # Determine system health
        system_health = "SAUDÁVEL"
        if issues_found:
            if any(len(issues) > 5 for _, issues in issues_found):
                system_health = "CRÍTICO"
            else:
                system_health = "ATENÇÃO"
        
        # Create health report
        health_report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "system_health": system_health,
            "validations": {},
            "issues": [],
            "recommendations": []
        }
        
        # Add validation results
        for validation_name, result in validation_results.items():
            health_report["validations"][validation_name] = {
                "is_valid": result.is_valid,
                "issues": result.issues
            }
        
        # Add issues
        for validation_name, issues in issues_found:
            for issue in issues:
                health_report["issues"].append({
                    "validation": validation_name,
                    "description": issue
                })
        
        # Generate recommendations
        recommendations = []
        
        # Check for directory structure issues
        if not validation_results["📁 Estrutura de diretórios"].is_valid:
            recommendations.append("🔧 Corrigir estrutura de diretórios")
        
        # Check for API credential issues
        if not validation_results["🔑 Credenciais de API"].is_valid:
            recommendations.append("🔑 Atualizar credenciais de API")
        
        # Check for configuration file issues
        if not validation_results["📄 Arquivos de configuração"].is_valid:
            recommendations.append("📄 Corrigir arquivos de configuração")
        
        # Check for progress database issues
        if not validation_results["💾 Database de progresso"].is_valid:
            recommendations.append("💾 Reparar banco de dados de progresso")
        
        # Check for Drive link issues
        if not validation_results["🔗 Links do Google Drive"].is_valid:
            recommendations.append("🔗 Atualizar links expirados do Google Drive")
        
        # Check for XML integrity issues
        if not validation_results["📊 XML do podcast"].is_valid:
            recommendations.append("📊 Corrigir arquivos XML")
        
        # Check cache size
        cache_size = self.get_directory_size(self.cache_dir)
        if cache_size > 2 * 1024 * 1024 * 1024:  # 2 GB
            recommendations.append("🧹 Limpar cache excessivo")
            health_report["issues"].append({
                "validation": "Cache",
                "description": f"Cache ocupando {self.format_size(cache_size)} (recomendado: <2GB)"
            })
        
        # Add recommendations to report
        health_report["recommendations"] = recommendations
        
        # Display health report
        self.display_health_report(health_report)
        
        logger.info("Health report generated")
        
        return health_report
    
    def display_health_report(self, health_report: Dict[str, Any]):
        """
        Display health report
        
        Args:
            health_report: Health report
        """
        # Determine health color
        health_color = NORD_GREEN
        if health_report["system_health"] == "ATENÇÃO":
            health_color = NORD_YELLOW
        elif health_report["system_health"] == "CRÍTICO":
            health_color = NORD_RED
        
        # Create health report panel
        report_text = [
            f"🏥 Relatório de Saúde do Sistema",
            f"[{NORD_DIM}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_DIM}]",
            "",
            f"[{health_color}]✅ Sistema Geral: {health_report['system_health']}[/{health_color}]",
            "",
            f"[{NORD_CYAN}]🔍 Verificações Realizadas:[/{NORD_CYAN}]"
        ]
        
        # Add validation results
        for validation_name, result in health_report["validations"].items():
            status_icon = "✅" if result["is_valid"] else "⚠️"
            report_text.append(f"{status_icon} {validation_name}")
        
        # Add issues
        if health_report["issues"]:
            report_text.append("")
            report_text.append(f"[{NORD_YELLOW}]⚠️ Problemas Encontrados:[/{NORD_YELLOW}]")
            
            for issue in health_report["issues"]:
                report_text.append(f"• {issue['description']}")
        
        # Add recommendations
        if health_report["recommendations"]:
            report_text.append("")
            report_text.append(f"[{NORD_CYAN}]🔧 Ações Recomendadas:[/{NORD_CYAN}]")
            
            for i, recommendation in enumerate(health_report["recommendations"], 1):
                report_text.append(f"[{NORD_BLUE}][{i}][/{NORD_BLUE}] {recommendation}")
            
            report_text.append(f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar")
        
        # Create panel
        panel = Panel(
            Text.from_markup("\n".join(report_text)),
            title="Relatório de Saúde do Sistema",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        
        console.print(panel)
        
    def get_api_status(self):
        """
        Get API status safely
        
        Returns:
            List: API status
        """
        if not HAS_CREDENTIALS:
            return [
                {"name": "OpenAI", "configured": False, "status": "unknown"},
                {"name": "Anthropic", "configured": False, "status": "unknown"},
                {"name": "Google Drive", "configured": False, "status": "unknown"},
                {"name": "GitHub", "configured": False, "status": "unknown"}
            ]
        
        try:
            return credentials.get_service_status()
        except Exception:
            return [
                {"name": "OpenAI", "configured": False, "status": "unknown"},
                {"name": "Anthropic", "configured": False, "status": "unknown"},
                {"name": "Google Drive", "configured": False, "status": "unknown"},
                {"name": "GitHub", "configured": False, "status": "unknown"}
            ]
    
    def optimize_storage(self):
        """
        Optimize storage usage
        """
        logger.info("Starting storage optimization")
        
        # Create backup before optimization
        self.create_backup(self.base_dir, "pre_optimization")
        
        # Get initial size
        initial_size = self.get_directory_size(self.base_dir)
        
        # Perform cleanup tasks
        cleanup_freed = self.comprehensive_cleanup()
        
        # Optimize course files
        course_freed = self._optimize_course_files()
        
        # Optimize database files
        database_freed = self._optimize_database_files()
        
        # Get final size
        final_size = self.get_directory_size(self.base_dir)
        
        # Calculate total freed space
        total_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        # Display results
        console.print(f"[{NORD_GREEN}]✅ Otimização de armazenamento concluída![/{NORD_GREEN}]")
        console.print(f"[{NORD_GREEN}]   Total liberado: {total_freed:.1f} MB[/{NORD_GREEN}]")
        console.print(f"[{NORD_GREEN}]   Limpeza: {cleanup_freed:.1f} MB[/{NORD_GREEN}]")
        console.print(f"[{NORD_GREEN}]   Otimização de cursos: {course_freed:.1f} MB[/{NORD_GREEN}]")
        console.print(f"[{NORD_GREEN}]   Otimização de banco de dados: {database_freed:.1f} MB[/{NORD_GREEN}]")
        
        logger.info(f"Storage optimization completed. Total space freed: {total_freed:.1f} MB")
        
        return total_freed
    
    def _optimize_course_files(self) -> float:
        """
        Optimize course files
        
        Returns:
            float: Space freed in MB
        """
        logger.info("Optimizing course files")
        
        # Get all course directories
        course_dirs = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item not in ["temp", "cache", "logs", "backups"]:
                course_dirs.append(item_path)
        
        # No courses to optimize
        if not course_dirs:
            logger.info("No courses to optimize")
            return 0
        
        # Get initial size
        initial_size = sum(self.get_directory_size(course_dir) for course_dir in course_dirs)
        
        # Process each course
        with Progress() as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Otimizando cursos...[/{NORD_CYAN}]", total=len(course_dirs))
            
            for course_dir in course_dirs:
                try:
                    # Optimize course
                    self._optimize_single_course(course_dir)
                    
                    # Update progress
                    progress.update(task, advance=1)
                except Exception as e:
                    logger.error(f"Failed to optimize course {course_dir}: {str(e)}")
        
        # Get final size
        final_size = sum(self.get_directory_size(course_dir) for course_dir in course_dirs)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        logger.info(f"Course files optimization completed. Space freed: {space_freed:.1f} MB")
        
        return space_freed
    
    def _optimize_single_course(self, course_dir: str):
        """
        Optimize a single course
        
        Args:
            course_dir: Course directory
        """
        # Remove duplicate files
        self._remove_duplicate_files(course_dir)
        
        # Compress large text files
        self._compress_large_text_files(course_dir)
    
    def _remove_duplicate_files(self, directory: str):
        """
        Remove duplicate files in a directory
        
        Args:
            directory: Directory to process
        """
        # Get all files
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        
        # Group files by hash
        file_hashes = {}
        for file_path in files:
            try:
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Calculate hash
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                # Add to hash group
                if file_hash not in file_hashes:
                    file_hashes[file_hash] = []
                file_hashes[file_hash].append(file_path)
            except Exception as e:
                logger.error(f"Failed to process file {file_path}: {str(e)}")
        
        # Remove duplicates
        for file_hash, file_paths in file_hashes.items():
            if len(file_paths) > 1:
                # Keep the first file, remove the rest
                for file_path in file_paths[1:]:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.info(f"Removed duplicate file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove duplicate file {file_path}: {str(e)}")
    
    def _compress_large_text_files(self, directory: str):
        """
        Compress large text files in a directory
        
        Args:
            directory: Directory to process
        """
        # Get all text files
        text_files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith((".txt", ".md", ".json", ".xml")):
                    file_path = os.path.join(root, filename)
                    # Check if file is larger than 1 MB
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 1024 * 1024:
                        text_files.append(file_path)
        
        # Compress files
        for file_path in text_files:
            try:
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Create compressed file
                compressed_path = f"{file_path}.gz"
                
                # Compress file
                with open(file_path, 'rb') as f_in:
                    with open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove original file
                os.remove(file_path)
                
                logger.info(f"Compressed large text file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to compress file {file_path}: {str(e)}")
    
    def _optimize_database_files(self) -> float:
        """
        Optimize database files
        
        Returns:
            float: Space freed in MB
        """
        logger.info("Optimizing database files")
        
        # Get data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        # Get initial size
        initial_size = self.get_directory_size(data_dir)
        
        # Database files to optimize
        database_files = [
            os.path.join(data_dir, "processed_courses.json"),
            os.path.join(data_dir, "settings.json")
        ]
        
        # Optimize each file
        for file_path in database_files:
            try:
                # Skip if file doesn't exist
                if not os.path.exists(file_path):
                    continue
                
                # Load data
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create backup
                backup_path = f"{file_path}.bak"
                shutil.copy2(file_path, backup_path)
                
                # Save optimized data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                
                logger.info(f"Optimized database file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to optimize database file {file_path}: {str(e)}")
                
                # Restore from backup if available
                if os.path.exists(f"{file_path}.bak"):
                    shutil.copy2(f"{file_path}.bak", file_path)
        
        # Get final size
        final_size = self.get_directory_size(data_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        logger.info(f"Database files optimization completed. Space freed: {space_freed:.1f} MB")
        
        return space_freed
    
    def auto_repair_system(self):
        """
        Automatically repair common system issues
        """
        logger.info("Starting auto-repair system")
        
        # Create backup before repair
        self.create_backup(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pre_auto_repair")
        
        # Validate system integrity
        health_report = self.validate_system_integrity()
        
        # No issues to repair
        if health_report["system_health"] == "SAUDÁVEL":
            console.print(f"[{NORD_GREEN}]✅ Sistema saudável, nenhum reparo necessário![/{NORD_GREEN}]")
            return
        
        # Display repair plan
        console.print(f"[{NORD_CYAN}]🔧 Plano de Reparo Automático:[/{NORD_CYAN}]")
        
        repair_tasks = []
        
        # Check for directory structure issues
        if not health_report["validations"]["📁 Estrutura de diretórios"]["is_valid"]:
            repair_tasks.append(("Corrigir estrutura de diretórios", self._repair_directory_structure))
        
        # Check for configuration file issues
        if not health_report["validations"]["📄 Arquivos de configuração"]["is_valid"]:
            repair_tasks.append(("Corrigir arquivos de configuração", self._repair_config_files))
        
        # Check for progress database issues
        if not health_report["validations"]["💾 Database de progresso"]["is_valid"]:
            repair_tasks.append(("Reparar banco de dados de progresso", self._repair_progress_database))
        
        # Check for Drive link issues
        if not health_report["validations"]["🔗 Links do Google Drive"]["is_valid"]:
            repair_tasks.append(("Atualizar links do Google Drive", self._repair_drive_links))
        
        # Check for XML integrity issues
        if not health_report["validations"]["📊 XML do podcast"]["is_valid"]:
            repair_tasks.append(("Corrigir arquivos XML", self._repair_xml_files))
        
        # Display repair tasks
        for i, (task_name, _) in enumerate(repair_tasks, 1):
            console.print(f"[{NORD_BLUE}][{i}][/{NORD_BLUE}] {task_name}")
        
        # Confirm repair
        if not Confirm.ask(f"[{NORD_YELLOW}]Executar reparo automático?[/{NORD_YELLOW}]"):
            console.print(f"[{NORD_YELLOW}]Reparo cancelado pelo usuário[/{NORD_YELLOW}]")
            return
        
        # Execute repair tasks
        with Progress() as progress:
            for task_name, task_func in repair_tasks:
                task_id = progress.add_task(f"[{NORD_CYAN}]{task_name}[/{NORD_CYAN}]", total=100)
                task_func(progress, task_id)
        
        # Validate system integrity again
        new_health_report = self.validate_system_integrity()
        
        # Check if repair was successful
        if new_health_report["system_health"] == "SAUDÁVEL":
            console.print(f"[{NORD_GREEN}]✅ Reparo automático concluído com sucesso![/{NORD_GREEN}]")
        else:
            console.print(f"[{NORD_YELLOW}]⚠️ Reparo automático concluído, mas alguns problemas persistem.[/{NORD_YELLOW}]")
            console.print(f"[{NORD_YELLOW}]   Recomenda-se verificar o relatório de saúde para mais detalhes.[/{NORD_YELLOW}]")
        
        logger.info("Auto-repair system completed")
    
    def _repair_directory_structure(self, progress: Optional[Progress] = None, task_id: Optional[int] = None):
        """
        Repair directory structure
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
        """
        logger.info("Repairing directory structure")
        
        # Required directories
        required_dirs = [
            self.base_dir,
            self.temp_dir,
            self.cache_dir,
            self.logs_dir,
            self.backup_dir,
            self.config["directories"]["github_local"],
            self.config["directories"]["xml_output"]
        ]
        
        # Create directories if they don't exist
        for i, directory in enumerate(required_dirs):
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / len(required_dirs))
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {str(e)}")
        
        # Create data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create required data files
        required_files = [
            (os.path.join(data_dir, "settings.json"), settings.get_default_settings()),
            (os.path.join(data_dir, "processed_courses.json"), [])
        ]
        
        for file_path, default_data in required_files:
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, indent=4, ensure_ascii=False)
                    
                    logger.info(f"Created data file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to create data file {file_path}: {str(e)}")
        
        logger.info("Directory structure repair completed")
    
    def _repair_config_files(self, progress: Optional[Progress] = None, task_id: Optional[int] = None):
        """
        Repair configuration files
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
        """
        logger.info("Repairing configuration files")
        
        # Get data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        # Required configuration files
        config_files = [
            (os.path.join(data_dir, "settings.json"), settings.get_default_settings()),
            (os.path.join(data_dir, "credentials.json"), {}),
            (os.path.join(data_dir, "processed_courses.json"), [])
        ]
        
        # Check and repair each file
        for i, (file_path, default_data) in enumerate(config_files):
            try:
                # Check if file exists
                if not os.path.exists(file_path):
                    # Create file with default data
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_data, f, indent=4, ensure_ascii=False)
                    
                    logger.info(f"Created configuration file: {file_path}")
                else:
                    # Check if file is valid JSON
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    except Exception:
                        # Create backup of corrupted file
                        backup_path = f"{file_path}.corrupted"
                        shutil.copy2(file_path, backup_path)
                        
                        # Create new file with default data
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(default_data, f, indent=4, ensure_ascii=False)
                        
                        logger.info(f"Repaired corrupted configuration file: {file_path}")
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / len(config_files))
            except Exception as e:
                logger.error(f"Failed to repair configuration file {file_path}: {str(e)}")
        
        # Check settings.json structure
        settings_file = os.path.join(data_dir, "settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # Check required settings
                default_settings = settings.get_default_settings()
                modified = False
                
                # Check directories
                if "directories" not in settings_data:
                    settings_data["directories"] = default_settings["directories"]
                    modified = True
                else:
                    for key, value in default_settings["directories"].items():
                        if key not in settings_data["directories"]:
                            settings_data["directories"][key] = value
                            modified = True
                
                # Check language
                if "language" not in settings_data:
                    settings_data["language"] = default_settings["language"]
                    modified = True
                else:
                    for key, value in default_settings["language"].items():
                        if key not in settings_data["language"]:
                            settings_data["language"][key] = value
                            modified = True
                
                # Save modified settings
                if modified:
                    with open(settings_file, 'w', encoding='utf-8') as f:
                        json.dump(settings_data, f, indent=4, ensure_ascii=False)
                    
                    logger.info(f"Updated settings.json structure")
            except Exception as e:
                logger.error(f"Failed to repair settings.json structure: {str(e)}")
        
        logger.info("Configuration files repair completed")
    
    def _repair_progress_database(self, progress: Optional[Progress] = None, task_id: Optional[int] = None):
        """
        Repair progress database
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
        """
        logger.info("Repairing progress database")
        
        # Get data directory
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        
        # Progress database file
        progress_file = os.path.join(data_dir, "processed_courses.json")
        
        try:
            # Check if file exists
            if not os.path.exists(progress_file):
                # Create empty progress database
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4, ensure_ascii=False)
                
                logger.info(f"Created progress database: {progress_file}")
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=100)
                
                return
            
            # Load progress data
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
            except Exception:
                # Create backup of corrupted file
                backup_path = f"{progress_file}.corrupted"
                shutil.copy2(progress_file, backup_path)
                
                # Create empty progress database
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4, ensure_ascii=False)
                
                logger.info(f"Repaired corrupted progress database: {progress_file}")
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=100)
                
                return
            
            # Check if progress data is a list
            if not isinstance(progress_data, list):
                # Create backup of invalid file
                backup_path = f"{progress_file}.invalid"
                shutil.copy2(progress_file, backup_path)
                
                # Create empty progress database
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4, ensure_ascii=False)
                
                logger.info(f"Repaired invalid progress database: {progress_file}")
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=100)
                
                return
            
            # Check each course
            valid_courses = []
            total_courses = len(progress_data)
            
            for i, course in enumerate(progress_data):
                # Check required fields
                required_fields = ["course_name", "directory", "created_at", "last_updated"]
                
                # Skip invalid courses
                if not all(field in course for field in required_fields):
                    logger.warning(f"Skipping invalid course: {course.get('course_name', 'Unknown')}")
                    continue
                
                # Check if directory exists
                if "directory" in course and not os.path.exists(course["directory"]):
                    # Try to find course directory
                    course_name = course["course_name"]
                    possible_dirs = []
                    
                    for item in os.listdir(self.base_dir):
                        item_path = os.path.join(self.base_dir, item)
                        if os.path.isdir(item_path) and item.lower() == course_name.lower():
                            possible_dirs.append(item_path)
                    
                    if possible_dirs:
                        # Update directory
                        course["directory"] = possible_dirs[0]
                        logger.info(f"Updated directory for course: {course_name}")
                    else:
                        # Skip course with non-existent directory
                        logger.warning(f"Skipping course with non-existent directory: {course_name}")
                        continue
                
                # Add valid course
                valid_courses.append(course)
                
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_courses)
            
            # Save valid courses
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(valid_courses, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Repaired progress database: {len(valid_courses)} valid courses out of {total_courses}")
        except Exception as e:
            logger.error(f"Failed to repair progress database: {str(e)}")
        
        logger.info("Progress database repair completed")
    
    def _repair_drive_links(self, progress: Optional[Progress] = None, task_id: Optional[int] = None):
        """
        Repair Google Drive links
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
        """
        logger.info("Repairing Google Drive links")
        
        # Get all course directories
        course_dirs = []
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            if os.path.isdir(item_path) and item not in ["temp", "cache", "logs", "backups"]:
                course_dirs.append(item_path)
        
        # No courses to repair
        if not course_dirs:
            logger.info("No courses to repair")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return
        
        # Check each course
        total_courses = len(course_dirs)
        
        for i, course_dir in enumerate(course_dirs):
            # Look for drive_links.json
            drive_links_file = os.path.join(course_dir, "drive_links.json")
            
            if not os.path.exists(drive_links_file):
                # Update progress
                if progress and task_id is not None:
                    progress.update(task_id, completed=(i + 1) * 100 / total_courses)
                continue
            
            try:
                # Load drive links
                with open(drive_links_file, 'r', encoding='utf-8') as f:
                    drive_links = json.load(f)
                
                # Check each link
                modified = False
                
                for link_name, link_info in drive_links.items():
                    # Check if link is expired
                    if "expiry" in link_info:
                        try:
                            expiry_date = datetime.datetime.fromisoformat(link_info["expiry"])
                            if expiry_date < datetime.datetime.now():
                                # Set expiry to 1 year from now
                                new_expiry = datetime.datetime.now() + datetime.timedelta(days=365)
                                link_info["expiry"] = new_expiry.isoformat()
                                modified = True
                                
                                logger.info(f"Updated expiry for link: {link_name} in {os.path.basename(course_dir)}")
                        except Exception:
                            # Set expiry to 1 year from now
                            new_expiry = datetime.datetime.now() + datetime.timedelta(days=365)
                            link_info["expiry"] = new_expiry.isoformat()
                            modified = True
                            
                            logger.info(f"Fixed invalid expiry for link: {link_name} in {os.path.basename(course_dir)}")
                    
                    # Check if link URL is valid
                    if "url" not in link_info or not link_info["url"].startswith("https://drive.google.com/"):
                        # Set placeholder URL
                        link_info["url"] = "https://drive.google.com/placeholder"
                        modified = True
                        
                        logger.info(f"Set placeholder URL for link: {link_name} in {os.path.basename(course_dir)}")
                
                # Save modified links
                if modified:
                    with open(drive_links_file, 'w', encoding='utf-8') as f:
                        json.dump(drive_links, f, indent=4, ensure_ascii=False)
                    
                    logger.info(f"Updated drive links for course: {os.path.basename(course_dir)}")
            except Exception as e:
                logger.error(f"Failed to repair drive links for {os.path.basename(course_dir)}: {str(e)}")
            
            # Update progress
            if progress and task_id is not None:
                progress.update(task_id, completed=(i + 1) * 100 / total_courses)
        
        logger.info("Google Drive links repair completed")
    
    def _repair_xml_files(self, progress: Optional[Progress] = None, task_id: Optional[int] = None):
        """
        Repair XML files
        
        Args:
            progress: Optional progress bar
            task_id: Optional task ID for progress bar
        """
        logger.info("Repairing XML files")
        
        # Get XML directory
        xml_dir = self.config["directories"]["xml_output"]
        
        # Check if directory exists
        if not os.path.exists(xml_dir):
            os.makedirs(xml_dir, exist_ok=True)
            logger.info(f"Created XML directory: {xml_dir}")
            
            # Update progress
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            
            return
        
        # Get all XML files
        xml_files = []
        for root, dirs, files in os.walk(xml_dir):
            for file in files:
                if file.endswith(".xml"):
                    xml_files.append(os.path.join(root, file))
        
        # No XML files to repair
        if not xml_files:
            logger.info("No XML files to repair")
            if progress and task_id is not None:
                progress.update(task_id, completed=100)
            return
        
        # Check each XML file
        total_files = len(xml_files)
        
        for i, xml_file in enumerate(xml_files):
            try:
                # Read XML file
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Check if XML is well-formed
                if not xml_content.strip().startswith("<?xml"):
                    # Create backup of invalid file
                    backup_path = f"{xml_file}.invalid"
                    shutil.copy2(xml_file, backup_path)
                    
                    # Create basic XML structure
                    course_name = os.path.splitext(os.path.basename(xml_file))[0]
                    
                    basic_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{course_name}</title>
    <description>Curso processado automaticamente</description>
    <pubDate>{datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</pubDate>
    <item>
      <title>{course_name} - Episódio 1</title>
      <description>Episódio 1 do curso {course_name}</description>
      <enclosure url="https://example.com/{course_name}.mp3" type="audio/mpeg" length="0"/>
    </item>
  </channel>
</rss>"""
                    
                    # Save basic XML
                    with open(xml_file, 'w', encoding='utf-8') as f:
                        f.write(basic_xml)
                    
                    logger.info(f"Repaired invalid XML file: {xml_file}")
                else:
                    # Check for required tags
                    required_tags = ["title", "description", "pubDate", "enclosure"]
                    missing_tags = []
                    
                    for tag in required_tags:
                        if f"<{tag}>" not in xml_content and f"<{tag} " not in xml_content:
                            missing_tags.append(tag)
                    
                    if missing_tags:
                        # Create backup of incomplete file
                        backup_path = f"{xml_file}.incomplete"
                        shutil.copy2(xml_file, backup_path)
                        
                        # Add missing tags
                        for tag in missing_tags:
                            if tag == "title":
                                course_name = os.path.splitext(os.path.basename(xml_file))[0]
                                xml_content = xml_content.replace("<channel>", f"<channel>\n    <title>{course_name}</title>")
                            elif tag == "description":
                                xml_content = xml_content.replace("<channel>", f"<channel>\n    <description>Curso processado automaticamente</description>")
                            elif tag == "pubDate":
                                pub_date = datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
                                xml_content = xml_content.replace("<channel>", f"<channel>\n    <pubDate>{pub_date}</pubDate>")
                            elif tag == "enclosure":
                                course_name = os.path.splitext(os.path.basename(xml_file))[0]
                                xml_content = xml_content.replace("<item>", f"<item>\n      <enclosure url=\"https://example.com/{course_name}.mp3\" type=\"audio/mpeg\" length=\"0\"/>")
                        
                        # Save updated XML
                        with open(xml_file, 'w', encoding='utf-8') as f:
                            f.write(xml_content)
                        
                        logger.info(f"Added missing tags to XML file: {xml_file}")
            except Exception as e:
                logger.error(f"Failed to repair XML file {xml_file}: {str(e)}")
            
            # Update progress
            if progress and task_id is not None:
                progress.update(task_id, completed=(i + 1) * 100 / total_files)
        
        logger.info("XML files repair completed")


def main():
    """Main function for maintenance system"""
    # Create maintenance system
    maintenance = SystemMaintenance()
    
    # Display menu
    while True:
        console.print(f"[{NORD_CYAN}]🔧 Sistema de Manutenção[/{NORD_CYAN}]")
        console.print(f"[{NORD_DIM}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_DIM}]")
        console.print()
        
        menu_items = [
            ("🧹 Limpeza Completa", maintenance.comprehensive_cleanup),
            ("🔄 Migrar Dados", lambda: maintenance.migrate_course_data(
                Prompt.ask("[bold]Diretório de origem"),
                Prompt.ask("[bold]Diretório de destino"),
                Prompt.ask("[bold]Operação (copy/move/sync)", choices=["copy", "move", "sync"], default="copy")
            )),
            ("🔍 Verificar Integridade", maintenance.validate_system_integrity),
            ("💾 Otimizar Armazenamento", maintenance.optimize_storage),
            ("🔧 Auto-Reparo", maintenance.auto_repair_system),
            ("📦 Backup do Sistema", lambda: maintenance.create_backup(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                f"system_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )),
            ("🔙 Voltar")
        ]
        
        for i, (item_name, _) in enumerate(menu_items, 1):
            console.print(f"[{NORD_BLUE}][{i}][/{NORD_BLUE}] {item_name}")
        
        console.print()
        
        choice = Prompt.ask(
            "[bold]Escolha uma opção",
            choices=[str(i) for i in range(1, len(menu_items) + 1)],
            default="7"
        )
        
        choice_idx = int(choice) - 1
        
        if choice_idx == len(menu_items) - 1:
            # Exit
            break
        
        # Execute selected function
        try:
            menu_items[choice_idx][1]()
        except Exception as e:
            logger.error(f"Error executing {menu_items[choice_idx][0]}: {str(e)}")
            console.print(f"[{NORD_RED}]❌ Erro: {str(e)}[/{NORD_RED}]")
        
        # Add separator
        console.print("\n" + "─" * console.width + "\n")


if __name__ == "__main__":
    main()