"""
Progress tracking utilities for Curso Processor

This module provides functionality to track the progress of course processing,
including state management, recovery, and migration tools.
"""

import json
import time
import os
import shutil
import glob
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set, Union

from rich.console import Console
from rich.panel import Panel

def get_processed_courses_stats() -> Dict[str, Any]:
    """
    Get statistics about processed courses
    
    Returns:
        Dict with statistics about processed courses
    """
    courses_file = Path(__file__).parent.parent / "data" / "processed_courses.json"
    
    if not os.path.exists(courses_file):
        return {
            "total_courses": 0,
            "total_files": 0,
            "total_size": 0,
            "total_size_formatted": "0 MB",
            "courses": []
        }
    
    try:
        with open(courses_file, 'r', encoding='utf-8') as f:
            courses_data = json.load(f)
    except Exception:
        return {
            "total_courses": 0,
            "total_files": 0,
            "total_size": 0,
            "total_size_formatted": "0 MB",
            "courses": []
        }
    
    # Calculate total size
    total_size = 0
    total_files = 0
    
    for course in courses_data:
        if "size" in course:
            total_size += course["size"]
        if "files" in course:
            total_files += len(course["files"])
    
    # Format size
    if total_size < 1024:
        total_size_formatted = f"{total_size} B"
    elif total_size < 1024 * 1024:
        total_size_formatted = f"{total_size / 1024:.1f} KB"
    elif total_size < 1024 * 1024 * 1024:
        total_size_formatted = f"{total_size / (1024 * 1024):.1f} MB"
    else:
        total_size_formatted = f"{total_size / (1024 * 1024 * 1024):.1f} GB"
    
    return {
        "total_courses": len(courses_data),
        "total_files": total_files,
        "total_size": total_size,
        "total_size_formatted": total_size_formatted,
        "courses": courses_data
    }
from rich.table import Table
from rich import box

# Configure console
console = Console()

# Define processing steps
PROCESSING_STEPS = [
    "audio_converted",
    "transcribed",
    "ai_processed",
    "timestamps_generated",
    "tts_created",
    "uploaded_to_drive",
    "xml_updated",
    "github_pushed"
]

class ProgressTracker:
    """Basic progress tracker for individual operations"""
    
    def __init__(self, course_name: str):
        """
        Initialize progress tracker
        
        Args:
            course_name: Name of the course being processed
        """
        self.course_name = course_name
        self.start_time = time.time()
        self.steps_completed = []
        self.current_step = None
        self.step_start_time = None
        self.progress_file = Path(__file__).parent.parent / "data" / f"{course_name}_progress.json"
        
        # Initialize progress file
        self._save_progress()
    
    def start_step(self, step_name: str):
        """
        Start a new processing step
        
        Args:
            step_name: Name of the step
        """
        self.current_step = step_name
        self.step_start_time = time.time()
        self._save_progress()
    
    def complete_step(self, metadata: Optional[Dict[str, Any]] = None):
        """
        Mark current step as completed
        
        Args:
            metadata: Optional metadata about the step
        """
        if self.current_step is None:
            return
        
        step_data = {
            "name": self.current_step,
            "start_time": self.step_start_time,
            "end_time": time.time(),
            "duration": time.time() - self.step_start_time,
            "metadata": metadata or {}
        }
        
        self.steps_completed.append(step_data)
        self.current_step = None
        self.step_start_time = None
        
        self._save_progress()
    
    def _save_progress(self):
        """Save progress to file"""
        progress_data = {
            "course_name": self.course_name,
            "start_time": self.start_time,
            "current_time": time.time(),
            "elapsed_time": time.time() - self.start_time,
            "steps_completed": self.steps_completed,
            "current_step": self.current_step,
            "step_start_time": self.step_start_time
        }
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=4)
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress
        
        Returns:
            Dict[str, Any]: Progress data
        """
        with open(self.progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_completed_steps(self) -> List[str]:
        """
        Get names of completed steps
        
        Returns:
            List[str]: Names of completed steps
        """
        return [step["name"] for step in self.steps_completed]
    
    def is_step_completed(self, step_name: str) -> bool:
        """
        Check if a step is completed
        
        Args:
            step_name: Name of the step
            
        Returns:
            bool: True if step is completed, False otherwise
        """
        return step_name in self.get_completed_steps()
    
    def get_total_duration(self) -> float:
        """
        Get total duration of processing
        
        Returns:
            float: Total duration in seconds
        """
        return time.time() - self.start_time
    
    def get_step_duration(self, step_name: str) -> Optional[float]:
        """
        Get duration of a specific step
        
        Args:
            step_name: Name of the step
            
        Returns:
            Optional[float]: Duration in seconds, or None if step not found
        """
        for step in self.steps_completed:
            if step["name"] == step_name:
                return step["duration"]
        return None


class CourseProgressTracker:
    """
    Comprehensive course progress tracker with state management,
    recovery, and migration capabilities.
    """
    
    def __init__(self, course_name: str, directory: str):
        """
        Initialize course progress tracker
        
        Args:
            course_name: Name of the course
            directory: Base directory for the course
        """
        self.course_name = course_name
        self.directory = os.path.abspath(os.path.expanduser(directory))
        self.courses_file = Path(__file__).parent.parent / "data" / "processed_courses.json"
        self.state_file = os.path.join(self.directory, f"{self.course_name.lower().replace(' ', '_')}_state.json")
        
        # Create directory if it doesn't exist
        os.makedirs(self.directory, exist_ok=True)
        
        # Initialize or load state
        self._initialize_state()
        
        # Register course in the global courses file
        self._register_course()
    
    def _initialize_state(self):
        """Initialize or load course state"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
                
            # Update current time
            self.state["metadata"]["last_updated"] = datetime.now().isoformat()
        else:
            # Create new state
            self.state = {
                "course_name": self.course_name,
                "directory": self.directory,
                "progress": {step: False for step in PROCESSING_STEPS},
                "metadata": {
                    "total_files": 0,
                    "total_duration": "00:00:00",
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat()
                },
                "files": {
                    "audio_files": [],
                    "transcriptions": [],
                    "processed_files": [],
                    "timestamp_files": [],
                    "tts_files": [],
                    "xml_files": []
                }
            }
            
            self.save_course_state()
    
    def _register_course(self):
        """Register course in the global courses file"""
        # Create courses file if it doesn't exist
        if not os.path.exists(self.courses_file):
            with open(self.courses_file, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=4)
        
        # Load existing courses
        with open(self.courses_file, 'r', encoding='utf-8') as f:
            courses = json.load(f)
        
        # Check if course already exists
        course_exists = False
        for course in courses:
            if course.get("course_name") == self.course_name:
                course_exists = True
                # Update directory if changed
                if course.get("directory") != self.directory:
                    course["directory"] = self.directory
                    course["last_updated"] = datetime.now().isoformat()
                break
        
        # Add course if it doesn't exist
        if not course_exists:
            courses.append({
                "course_name": self.course_name,
                "directory": self.directory,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "state_file": self.state_file
            })
        
        # Save courses
        with open(self.courses_file, 'w', encoding='utf-8') as f:
            json.dump(courses, f, indent=4)
    
    def save_course_state(self):
        """Save course state to file"""
        # Update last updated timestamp
        self.state["metadata"]["last_updated"] = datetime.now().isoformat()
        
        # Create backup of existing state file
        if os.path.exists(self.state_file):
            backup_file = f"{self.state_file}.bak"
            shutil.copy2(self.state_file, backup_file)
        
        # Save state
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4)
    
    def load_course_state(self) -> Dict[str, Any]:
        """
        Load course state from file
        
        Returns:
            Dict[str, Any]: Course state
        """
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
        
        return self.state
    
    def mark_step_completed(self, step: str, files: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Mark a processing step as completed
        
        Args:
            step: Processing step name
            files: List of files associated with the step
            metadata: Additional metadata for the step
        """
        if step not in PROCESSING_STEPS:
            raise ValueError(f"Invalid step: {step}")
        
        # Mark step as completed
        self.state["progress"][step] = True
        
        # Update files if provided
        if files:
            if step == "audio_converted":
                self.state["files"]["audio_files"] = files
            elif step == "transcribed":
                self.state["files"]["transcriptions"] = files
            elif step == "ai_processed":
                self.state["files"]["processed_files"] = files
            elif step == "timestamps_generated":
                self.state["files"]["timestamp_files"] = files
            elif step == "tts_created":
                self.state["files"]["tts_files"] = files
            elif step == "xml_updated":
                self.state["files"]["xml_files"] = files
        
        # Update metadata if provided
        if metadata:
            for key, value in metadata.items():
                self.state["metadata"][key] = value
        
        # Save state
        self.save_course_state()
    
    def get_next_pending_step(self) -> Optional[str]:
        """
        Get the next pending processing step
        
        Returns:
            Optional[str]: Next pending step, or None if all steps are completed
        """
        for step in PROCESSING_STEPS:
            if not self.state["progress"].get(step, False):
                return step
        
        return None
    
    def auto_detect_completed_steps(self) -> Dict[str, bool]:
        """
        Automatically detect completed steps based on file existence
        
        Returns:
            Dict[str, bool]: Dictionary of steps and their detected completion status
        """
        detected_steps = {}
        
        # Check for audio files
        audio_files = glob.glob(os.path.join(self.directory, "**", "*.mp3"), recursive=True)
        audio_files += glob.glob(os.path.join(self.directory, "**", "*.wav"), recursive=True)
        detected_steps["audio_converted"] = len(audio_files) > 0
        
        # Check for transcription files
        transcription_files = glob.glob(os.path.join(self.directory, "**", "*.txt"), recursive=True)
        transcription_files += glob.glob(os.path.join(self.directory, "**", "*.md"), recursive=True)
        detected_steps["transcribed"] = len(transcription_files) > 0
        
        # Check for processed files (markdown with specific patterns)
        processed_files = []
        for file in transcription_files:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if "## " in content or "# " in content:  # Simple heuristic for processed markdown
                    processed_files.append(file)
        detected_steps["ai_processed"] = len(processed_files) > 0
        
        # Check for timestamp files
        timestamp_files = []
        for file in transcription_files:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if re.search(r'\d{2}:\d{2}:\d{2}', content):  # Look for timestamp patterns
                    timestamp_files.append(file)
        detected_steps["timestamps_generated"] = len(timestamp_files) > 0
        
        # Check for TTS files
        tts_files = glob.glob(os.path.join(self.directory, "**", "tts_*.mp3"), recursive=True)
        detected_steps["tts_created"] = len(tts_files) > 0
        
        # Check for XML files
        xml_files = glob.glob(os.path.join(self.directory, "**", "*.xml"), recursive=True)
        detected_steps["xml_updated"] = len(xml_files) > 0
        
        # Check for GitHub repository
        git_dir = os.path.join(self.directory, ".git")
        detected_steps["github_pushed"] = os.path.exists(git_dir) and os.path.isdir(git_dir)
        
        # Update state with detected files
        if detected_steps["audio_converted"]:
            self.state["files"]["audio_files"] = audio_files
        if detected_steps["transcribed"]:
            self.state["files"]["transcriptions"] = transcription_files
        if detected_steps["ai_processed"]:
            self.state["files"]["processed_files"] = processed_files
        if detected_steps["timestamps_generated"]:
            self.state["files"]["timestamp_files"] = timestamp_files
        if detected_steps["tts_created"]:
            self.state["files"]["tts_files"] = tts_files
        if detected_steps["xml_updated"]:
            self.state["files"]["xml_files"] = xml_files
        
        # Update metadata
        if audio_files:
            # Calculate total duration (placeholder - would need audio library to actually calculate)
            self.state["metadata"]["total_files"] = len(audio_files)
            self.state["metadata"]["total_duration"] = "00:00:00"  # Placeholder
        
        # Save state
        self.save_course_state()
        
        return detected_steps
    
    def validate_file_integrity(self) -> Dict[str, List[str]]:
        """
        Validate the integrity of course files
        
        Returns:
            Dict[str, List[str]]: Dictionary of file types and lists of invalid files
        """
        invalid_files = {
            "audio_files": [],
            "transcriptions": [],
            "processed_files": [],
            "timestamp_files": [],
            "tts_files": [],
            "xml_files": []
        }
        
        # Check audio files
        for file in self.state["files"].get("audio_files", []):
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                invalid_files["audio_files"].append(file)
        
        # Check transcription files
        for file in self.state["files"].get("transcriptions", []):
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                invalid_files["transcriptions"].append(file)
        
        # Check processed files
        for file in self.state["files"].get("processed_files", []):
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                invalid_files["processed_files"].append(file)
        
        # Check timestamp files
        for file in self.state["files"].get("timestamp_files", []):
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                invalid_files["timestamp_files"].append(file)
        
        # Check TTS files
        for file in self.state["files"].get("tts_files", []):
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                invalid_files["tts_files"].append(file)
        
        # Check XML files
        for file in self.state["files"].get("xml_files", []):
            if not os.path.exists(file) or os.path.getsize(file) == 0:
                invalid_files["xml_files"].append(file)
        
        return invalid_files
    
    def suggest_next_action(self) -> Tuple[str, str]:
        """
        Suggest the next action based on the current state
        
        Returns:
            Tuple[str, str]: Action name and description
        """
        # Check for invalid files
        invalid_files = self.validate_file_integrity()
        has_invalid_files = any(len(files) > 0 for files in invalid_files.values())
        
        if has_invalid_files:
            return "verify_integrity", "Verificar integridade dos arquivos"
        
        # Get next pending step
        next_step = self.get_next_pending_step()
        
        if next_step is None:
            return "complete", "Curso completamente processado"
        
        # Map step to action
        step_to_action = {
            "audio_converted": ("convert_audio", "Converter vídeos para áudio"),
            "transcribed": ("transcribe", "Transcrever áudios"),
            "ai_processed": ("process_ai", "Processar com IA"),
            "timestamps_generated": ("generate_timestamps", "Gerar timestamps"),
            "tts_created": ("create_tts", "Criar áudio TTS"),
            "xml_updated": ("update_xml", "Gerar XML Podcast"),
            "uploaded_to_drive": ("upload_drive", "Upload Google Drive"),
            "github_pushed": ("push_github", "Atualizar GitHub")
        }
        
        return step_to_action.get(next_step, ("unknown", "Ação desconhecida"))
    
    def cleanup_partial_processing(self) -> Dict[str, int]:
        """
        Clean up partial processing artifacts
        
        Returns:
            Dict[str, int]: Dictionary of file types and number of files removed
        """
        removed_files = {
            "audio_files": 0,
            "transcriptions": 0,
            "processed_files": 0,
            "timestamp_files": 0,
            "tts_files": 0,
            "xml_files": 0
        }
        
        # Get next pending step
        next_step = self.get_next_pending_step()
        
        if next_step is None:
            return removed_files  # All steps completed, nothing to clean up
        
        # Determine which files to clean up based on the next pending step
        step_index = PROCESSING_STEPS.index(next_step)
        
        # Clean up files from the pending step and all subsequent steps
        for i in range(step_index, len(PROCESSING_STEPS)):
            step = PROCESSING_STEPS[i]
            
            if step == "audio_converted":
                for file in self.state["files"].get("audio_files", []):
                    if os.path.exists(file):
                        os.remove(file)
                        removed_files["audio_files"] += 1
                self.state["files"]["audio_files"] = []
            
            elif step == "transcribed":
                for file in self.state["files"].get("transcriptions", []):
                    if os.path.exists(file):
                        os.remove(file)
                        removed_files["transcriptions"] += 1
                self.state["files"]["transcriptions"] = []
            
            elif step == "ai_processed":
                for file in self.state["files"].get("processed_files", []):
                    if os.path.exists(file):
                        os.remove(file)
                        removed_files["processed_files"] += 1
                self.state["files"]["processed_files"] = []
            
            elif step == "timestamps_generated":
                for file in self.state["files"].get("timestamp_files", []):
                    if os.path.exists(file):
                        os.remove(file)
                        removed_files["timestamp_files"] += 1
                self.state["files"]["timestamp_files"] = []
            
            elif step == "tts_created":
                for file in self.state["files"].get("tts_files", []):
                    if os.path.exists(file):
                        os.remove(file)
                        removed_files["tts_files"] += 1
                self.state["files"]["tts_files"] = []
            
            elif step == "xml_updated":
                for file in self.state["files"].get("xml_files", []):
                    if os.path.exists(file):
                        os.remove(file)
                        removed_files["xml_files"] += 1
                self.state["files"]["xml_files"] = []
            
            # Mark step as not completed
            self.state["progress"][step] = False
        
        # Save state
        self.save_course_state()
        
        return removed_files
    
    def display_recovery_menu(self):
        """Display recovery menu for interrupted processing"""
        # Get current status
        next_step = self.get_next_pending_step()
        
        if next_step is None:
            next_step_name = "Processamento completo"
        else:
            step_names = {
                "audio_converted": "Conversão de Áudio",
                "transcribed": "Transcrição",
                "ai_processed": "Processamento IA",
                "timestamps_generated": "Geração de Timestamps",
                "tts_created": "Criação de TTS",
                "xml_updated": "Atualização de XML",
                "uploaded_to_drive": "Upload para Drive",
                "github_pushed": "Atualização do GitHub"
            }
            next_step_name = step_names.get(next_step, next_step)
        
        # Display menu
        console.print("\n🔄 Sistema de Recuperação", style="bright_cyan bold")
        console.print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n", style="bright_cyan")
        
        console.print(f"Curso encontrado: [bright_white]{self.course_name}[/bright_white]")
        console.print(f"Status: [bright_yellow]Processamento interrompido em \"{next_step_name}\"[/bright_yellow]\n")
        
        console.print("[1] 🔄 Continuar de onde parou")
        console.print("[2] 🔍 Verificar integridade dos arquivos")
        console.print("[3] 🗑️ Limpar e recomeçar")
        console.print("[4] 📋 Ver detalhes completos")
        console.print("[0] ← Voltar\n")
        
        choice = input("Escolha uma opção [0-4]: ")
        
        if choice == "1":
            # Continue from where it left off
            action, description = self.suggest_next_action()
            console.print(f"\nContinuando com: [bright_green]{description}[/bright_green]")
            return action
        
        elif choice == "2":
            # Verify file integrity
            console.print("\nVerificando integridade dos arquivos...", style="bright_blue")
            invalid_files = self.validate_file_integrity()
            
            has_invalid_files = any(len(files) > 0 for files in invalid_files.values())
            
            if has_invalid_files:
                console.print("\n[bright_red]Problemas encontrados:[/bright_red]")
                
                for file_type, files in invalid_files.items():
                    if len(files) > 0:
                        console.print(f"\n[bright_yellow]{file_type}:[/bright_yellow]")
                        for file in files:
                            console.print(f"  - {file}")
                
                console.print("\nDeseja limpar arquivos inválidos? [s/N]: ", end="")
                clean_choice = input().lower()
                
                if clean_choice == "s":
                    self.cleanup_partial_processing()
                    console.print("\n[bright_green]Arquivos inválidos removidos.[/bright_green]")
            else:
                console.print("\n[bright_green]Todos os arquivos estão íntegros.[/bright_green]")
            
            # Recursively display menu again
            return self.display_recovery_menu()
        
        elif choice == "3":
            # Clean up and restart
            console.print("\nTem certeza que deseja limpar e recomeçar? [s/N]: ", end="")
            clean_choice = input().lower()
            
            if clean_choice == "s":
                removed_files = self.cleanup_partial_processing()
                total_removed = sum(removed_files.values())
                
                console.print(f"\n[bright_green]{total_removed} arquivos removidos.[/bright_green]")
                console.print("Processamento reiniciado.")
                
                # Reset progress
                for step in PROCESSING_STEPS:
                    self.state["progress"][step] = False
                
                self.save_course_state()
                
                return "restart"
            else:
                # Recursively display menu again
                return self.display_recovery_menu()
        
        elif choice == "4":
            # Show detailed information
            self._display_detailed_info()
            
            # Recursively display menu again
            return self.display_recovery_menu()
        
        else:
            # Go back
            return "back"
    
    def _display_detailed_info(self):
        """Display detailed information about the course"""
        console.print("\n📋 Detalhes do Curso", style="bright_cyan bold")
        console.print("━━━━━━━━━━━━━━━━━━━━━━", style="bright_cyan")
        
        # Create table for course information
        table = Table(box=box.ROUNDED, show_header=True, header_style="bright_cyan")
        table.add_column("Propriedade", style="bright_white")
        table.add_column("Valor", style="bright_yellow")
        
        # Add course information
        table.add_row("Nome do Curso", self.course_name)
        table.add_row("Diretório", self.directory)
        table.add_row("Criado em", self.state["metadata"]["created_at"])
        table.add_row("Última atualização", self.state["metadata"]["last_updated"])
        table.add_row("Total de arquivos", str(self.state["metadata"]["total_files"]))
        table.add_row("Duração total", self.state["metadata"]["total_duration"])
        
        console.print(table)
        
        # Create table for progress information
        progress_table = Table(box=box.ROUNDED, show_header=True, header_style="bright_cyan")
        progress_table.add_column("Etapa", style="bright_white")
        progress_table.add_column("Status", style="bright_green")
        
        # Add progress information
        step_names = {
            "audio_converted": "Conversão de Áudio",
            "transcribed": "Transcrição",
            "ai_processed": "Processamento IA",
            "timestamps_generated": "Geração de Timestamps",
            "tts_created": "Criação de TTS",
            "xml_updated": "Atualização de XML",
            "uploaded_to_drive": "Upload para Drive",
            "github_pushed": "Atualização do GitHub"
        }
        
        for step, completed in self.state["progress"].items():
            status = "[bright_green]✓ Concluído[/bright_green]" if completed else "[bright_red]✗ Pendente[/bright_red]"
            progress_table.add_row(step_names.get(step, step), status)
        
        console.print("\n🔄 Progresso", style="bright_cyan bold")
        console.print("━━━━━━━━━━━━━", style="bright_cyan")
        console.print(progress_table)
        
        # Display file counts
        file_table = Table(box=box.ROUNDED, show_header=True, header_style="bright_cyan")
        file_table.add_column("Tipo de Arquivo", style="bright_white")
        file_table.add_column("Quantidade", style="bright_yellow")
        
        for file_type, files in self.state["files"].items():
            file_table.add_row(file_type, str(len(files)))
        
        console.print("\n📁 Arquivos", style="bright_cyan bold")
        console.print("━━━━━━━━━━━", style="bright_cyan")
        console.print(file_table)
        
        # Wait for user to continue
        input("\nPressione Enter para continuar...")


def migrate_course_data(source_dir: str, target_dir: str, course_name: str) -> Tuple[bool, str, Dict[str, int]]:
    """
    Migrate course data from one directory to another
    
    Args:
        source_dir: Source directory
        target_dir: Target directory
        course_name: Course name
        
    Returns:
        Tuple[bool, str, Dict[str, int]]: Success status, message, and file counts
    """
    # Expand paths
    source_dir = os.path.abspath(os.path.expanduser(source_dir))
    target_dir = os.path.abspath(os.path.expanduser(target_dir))
    
    # Check if source directory exists
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        return False, f"Source directory does not exist: {source_dir}", {}
    
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Initialize file counts
    file_counts = {
        "audio_files": 0,
        "transcriptions": 0,
        "processed_files": 0,
        "timestamp_files": 0,
        "tts_files": 0,
        "xml_files": 0,
        "other_files": 0
    }
    
    # Create backup of target directory
    backup_dir = f"{target_dir}_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if os.path.exists(target_dir) and os.listdir(target_dir):
        shutil.copytree(target_dir, backup_dir)
    
    # Copy files
    try:
        # Copy audio files
        audio_files = glob.glob(os.path.join(source_dir, "**", "*.mp3"), recursive=True)
        audio_files += glob.glob(os.path.join(source_dir, "**", "*.wav"), recursive=True)
        
        for file in audio_files:
            rel_path = os.path.relpath(file, source_dir)
            target_file = os.path.join(target_dir, rel_path)
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Copy file
            shutil.copy2(file, target_file)
            file_counts["audio_files"] += 1
        
        # Copy transcription files
        transcription_files = glob.glob(os.path.join(source_dir, "**", "*.txt"), recursive=True)
        transcription_files += glob.glob(os.path.join(source_dir, "**", "*.md"), recursive=True)
        
        for file in transcription_files:
            rel_path = os.path.relpath(file, source_dir)
            target_file = os.path.join(target_dir, rel_path)
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Copy file
            shutil.copy2(file, target_file)
            
            # Determine file type based on content
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if "## " in content or "# " in content:
                    file_counts["processed_files"] += 1
                elif re.search(r'\d{2}:\d{2}:\d{2}', content):
                    file_counts["timestamp_files"] += 1
                else:
                    file_counts["transcriptions"] += 1
        
        # Copy TTS files
        tts_files = glob.glob(os.path.join(source_dir, "**", "tts_*.mp3"), recursive=True)
        
        for file in tts_files:
            rel_path = os.path.relpath(file, source_dir)
            target_file = os.path.join(target_dir, rel_path)
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Copy file
            shutil.copy2(file, target_file)
            file_counts["tts_files"] += 1
        
        # Copy XML files
        xml_files = glob.glob(os.path.join(source_dir, "**", "*.xml"), recursive=True)
        
        for file in xml_files:
            rel_path = os.path.relpath(file, source_dir)
            target_file = os.path.join(target_dir, rel_path)
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Copy file
            shutil.copy2(file, target_file)
            file_counts["xml_files"] += 1
        
        # Copy other files
        other_files = glob.glob(os.path.join(source_dir, "**", "*.*"), recursive=True)
        
        for file in other_files:
            # Skip already copied files
            if file in audio_files or file in transcription_files or file in tts_files or file in xml_files:
                continue
            
            rel_path = os.path.relpath(file, source_dir)
            target_file = os.path.join(target_dir, rel_path)
            
            # Create target directory if it doesn't exist
            os.makedirs(os.path.dirname(target_file), exist_ok=True)
            
            # Copy file
            shutil.copy2(file, target_file)
            file_counts["other_files"] += 1
        
        # Create or update course state
        tracker = CourseProgressTracker(course_name, target_dir)
        
        # Auto-detect completed steps
        tracker.auto_detect_completed_steps()
        
        return True, f"Course data migrated successfully from {source_dir} to {target_dir}", file_counts
    
    except Exception as e:
        # Restore from backup if migration failed
        if os.path.exists(backup_dir):
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            shutil.copytree(backup_dir, target_dir)
        
        return False, f"Error migrating course data: {str(e)}", file_counts