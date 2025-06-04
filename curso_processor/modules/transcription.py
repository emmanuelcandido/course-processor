"""
Transcription module for Curso Processor
Supports both OpenAI Whisper API and Docker local transcription
"""

import os
import time
import json
import yaml
import logging
import tempfile
import subprocess
import datetime
import requests
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import math
import random

from rich.progress import Progress, TaskID
from rich.console import Console
from openai import OpenAI, RateLimitError, APIError, APITimeoutError

from utils import file_manager, ui_components
from config import settings, credentials

# Configure logging
logger = logging.getLogger("transcription")

# Constants
WHISPER_API_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
DOCKER_IMAGE = "onerahmet/openai-whisper-asr-webservice"
DOCKER_CONTAINER_NAME = "whisper-service"
DOCKER_PORT = 9000
MAX_OPENAI_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes
SUPPORTED_AUDIO_FORMATS = [".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"]
SUPPORTED_LANGUAGES = {
    "en": "English",
    "pt": "Portuguese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "nl": "Dutch",
    "ja": "Japanese",
    "zh": "Chinese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "ko": "Korean",
    "tr": "Turkish",
    "pl": "Polish",
    "auto": "Auto-detect"
}

class WhisperTranscriber:
    """Class for transcribing audio files using Whisper"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "auto",
        temperature: float = 0.0,
        console: Optional[Console] = None
    ):
        """
        Initialize WhisperTranscriber
        
        Args:
            api_key: OpenAI API key (if None, will try to get from credentials)
            model: Whisper model to use
            language: Language code (e.g., "en", "pt", "auto" for auto-detection)
            temperature: Sampling temperature (0.0 to 1.0)
            console: Rich console for output
        """
        self.api_key = api_key or credentials.get_openai_api_key()
        self.model = model
        self.language = language
        self.temperature = temperature
        self.console = console or Console()
        
        # Initialize OpenAI client if API key is available
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        
        # Cache for transcriptions
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache" / "transcriptions"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def transcribe_openai_api(
        self,
        audio_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
        prompt: Optional[str] = None,
        response_format: str = "verbose_json"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Transcribe audio using OpenAI Whisper API
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcription
            progress: Rich progress object
            task_id: Task ID for progress tracking
            prompt: Optional prompt to guide transcription
            response_format: Format of the response ("json", "text", "srt", "verbose_json", "vtt")
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and transcription data
        """
        if not self.api_key or not self.client:
            error_message = "OpenAI API key not available"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Convert paths to Path objects
        audio_path = Path(audio_path)
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists
        if not audio_path.exists():
            error_message = f"Audio file not found: {audio_path}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Check if file format is supported
        if audio_path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
            error_message = f"Unsupported audio format: {audio_path.suffix}. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Check cache
        cache_key = self._get_cache_key(audio_path, "openai_api", self.model, self.language)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached transcription for {audio_path}")
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, advance=1, description=f"Cached: {audio_path.name}")
            
            # Save transcription if output_dir is provided
            if output_dir:
                self.save_transcription(cached_result, audio_path, output_dir)
            
            return True, cached_result
        
        # Check file size
        file_size = audio_path.stat().st_size
        if file_size > MAX_OPENAI_FILE_SIZE:
            logger.warning(f"File size ({file_size} bytes) exceeds OpenAI limit ({MAX_OPENAI_FILE_SIZE} bytes). Splitting file...")
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, description=f"Splitting {audio_path.name}")
            
            # Split file and transcribe chunks
            return self._transcribe_large_file(
                audio_path=audio_path,
                output_dir=output_dir,
                progress=progress,
                task_id=task_id,
                prompt=prompt,
                response_format=response_format
            )
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Transcribing {audio_path.name}")
        
        # Prepare parameters
        params = {
            "model": self.model,
            "temperature": self.temperature,
            "response_format": response_format
        }
        
        # Add language if specified (not auto)
        if self.language != "auto":
            params["language"] = self.language
        
        # Add prompt if provided
        if prompt:
            params["prompt"] = prompt
        
        # Transcribe with retry logic
        max_retries = 5
        retry_delay = 1  # Initial delay in seconds
        
        for attempt in range(max_retries):
            try:
                with open(audio_path, "rb") as audio_file:
                    # Call OpenAI API
                    response = self.client.audio.transcriptions.create(
                        file=audio_file,
                        **params
                    )
                
                # Process response
                if response_format == "verbose_json":
                    result = response.model_dump()
                elif response_format == "json":
                    result = {"text": response.text}
                else:
                    result = {"text": response}
                
                # Add metadata
                result["source_file"] = str(audio_path)
                result["transcription_method"] = "openai_api"
                result["model_used"] = self.model
                
                # Get audio duration
                try:
                    duration = file_manager.get_audio_duration(audio_path)
                    result["duration"] = duration
                    result["duration_formatted"] = file_manager.format_duration(duration)
                except Exception as e:
                    logger.warning(f"Error getting audio duration: {str(e)}")
                    result["duration"] = 0
                    result["duration_formatted"] = "00:00:00"
                
                # Add timestamp
                result["transcribed_at"] = datetime.datetime.now().isoformat()
                
                # Add language
                if self.language != "auto":
                    result["language"] = self.language
                elif "language" in result:
                    pass  # Language already in result
                else:
                    result["language"] = "auto"
                
                # Cache result
                self._cache_result(cache_key, result)
                
                # Save transcription if output_dir is provided
                if output_dir:
                    self.save_transcription(result, audio_path, output_dir)
                
                # Update progress if provided
                if progress and task_id is not None:
                    progress.update(task_id, advance=1)
                
                return True, result
            
            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                # Update progress if provided
                if progress and task_id is not None:
                    progress.update(task_id, description=f"Rate limit exceeded, retrying... ({attempt+1}/{max_retries})")
                
                # Exponential backoff with jitter
                sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            
            except (APIError, APITimeoutError) as e:
                logger.warning(f"API error (attempt {attempt+1}/{max_retries}): {str(e)}")
                
                # Update progress if provided
                if progress and task_id is not None:
                    progress.update(task_id, description=f"API error, retrying... ({attempt+1}/{max_retries})")
                
                # Exponential backoff with jitter
                sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(sleep_time)
            
            except Exception as e:
                error_message = f"Error transcribing {audio_path}: {str(e)}"
                logger.error(error_message)
                return False, {"error": error_message}
        
        # If we get here, all retries failed
        error_message = f"Failed to transcribe {audio_path} after {max_retries} attempts"
        logger.error(error_message)
        return False, {"error": error_message}
    
    def _transcribe_large_file(
        self,
        audio_path: Path,
        output_dir: Optional[Path] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
        prompt: Optional[str] = None,
        response_format: str = "verbose_json"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Split and transcribe large audio files
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcription
            progress: Rich progress object
            task_id: Task ID for progress tracking
            prompt: Optional prompt to guide transcription
            response_format: Format of the response
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and transcription data
        """
        try:
            # Create temporary directory for chunks
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                
                # Get audio duration
                duration = file_manager.get_audio_duration(audio_path)
                
                # Calculate number of chunks needed
                file_size = audio_path.stat().st_size
                num_chunks = math.ceil(file_size / (MAX_OPENAI_FILE_SIZE * 0.9))  # 90% of max size to be safe
                chunk_duration = duration / num_chunks
                
                # Update progress if provided
                if progress and task_id is not None:
                    progress.update(task_id, description=f"Splitting {audio_path.name} into {num_chunks} chunks")
                
                # Split audio file into chunks
                chunk_paths = []
                for i in range(num_chunks):
                    start_time = i * chunk_duration
                    end_time = min((i + 1) * chunk_duration, duration)
                    
                    chunk_path = temp_dir_path / f"chunk_{i:03d}{audio_path.suffix}"
                    
                    # Use ffmpeg to extract chunk
                    cmd = [
                        "ffmpeg",
                        "-i", str(audio_path),
                        "-ss", str(start_time),
                        "-to", str(end_time),
                        "-c", "copy",
                        str(chunk_path),
                        "-y"
                    ]
                    
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    chunk_paths.append(chunk_path)
                
                # Create a new progress bar for chunks if provided
                chunk_progress = None
                chunk_task = None
                if progress:
                    chunk_task = progress.add_task(f"Transcribing chunks of {audio_path.name}", total=len(chunk_paths))
                
                # Transcribe each chunk
                transcriptions = []
                for i, chunk_path in enumerate(chunk_paths):
                    # Update progress if provided
                    if progress and chunk_task is not None:
                        progress.update(chunk_task, description=f"Chunk {i+1}/{len(chunk_paths)}")
                    
                    # Transcribe chunk
                    success, result = self.transcribe_openai_api(
                        audio_path=chunk_path,
                        output_dir=None,  # Don't save individual chunks
                        progress=progress,
                        task_id=chunk_task,
                        prompt=prompt,
                        response_format=response_format
                    )
                    
                    if not success:
                        logger.error(f"Error transcribing chunk {i+1}/{len(chunk_paths)}: {result.get('error', 'Unknown error')}")
                        continue
                    
                    transcriptions.append(result)
                
                # Combine transcriptions
                combined_text = " ".join(t.get("text", "") for t in transcriptions)
                
                # Create combined result
                combined_result = {
                    "text": combined_text,
                    "source_file": str(audio_path),
                    "transcription_method": "openai_api_chunked",
                    "model_used": self.model,
                    "duration": duration,
                    "duration_formatted": file_manager.format_duration(duration),
                    "transcribed_at": datetime.datetime.now().isoformat(),
                    "language": transcriptions[0].get("language", "auto") if transcriptions else "auto",
                    "num_chunks": num_chunks
                }
                
                # Save transcription if output_dir is provided
                if output_dir:
                    self.save_transcription(combined_result, audio_path, output_dir)
                
                # Update progress if provided
                if progress and task_id is not None:
                    progress.update(task_id, advance=1)
                
                return True, combined_result
        
        except Exception as e:
            error_message = f"Error transcribing large file {audio_path}: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    def transcribe_docker_local(
        self,
        audio_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
        model_size: str = "base"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Transcribe audio using local Docker container
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save transcription
            progress: Rich progress object
            task_id: Task ID for progress tracking
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and transcription data
        """
        # Convert paths to Path objects
        audio_path = Path(audio_path)
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists
        if not audio_path.exists():
            error_message = f"Audio file not found: {audio_path}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Check if file format is supported
        if audio_path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
            error_message = f"Unsupported audio format: {audio_path.suffix}. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Check cache
        cache_key = self._get_cache_key(audio_path, "docker_local", model_size, self.language)
        cached_result = self._check_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached transcription for {audio_path}")
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, advance=1, description=f"Cached: {audio_path.name}")
            
            # Save transcription if output_dir is provided
            if output_dir:
                self.save_transcription(cached_result, audio_path, output_dir)
            
            return True, cached_result
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Transcribing {audio_path.name}")
        
        # Check if Docker is installed
        if not self._check_docker_installed():
            error_message = "Docker is not installed or not accessible"
            logger.error(error_message)
            return False, {"error": error_message}
        
        # Check if Docker container is running, start if not
        container_running = self._ensure_docker_container_running(progress, task_id)
        if not container_running:
            error_message = "Failed to start Docker container"
            logger.error(error_message)
            return False, {"error": error_message}
        
        try:
            # Prepare API request
            api_url = f"http://localhost:{DOCKER_PORT}/asr"
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, description=f"Uploading {audio_path.name}")
            
            # Prepare files and data
            files = {
                "audio_file": (audio_path.name, open(audio_path, "rb"), f"audio/{audio_path.suffix[1:]}")
            }
            
            data = {
                "model_size": model_size
            }
            
            # Add language if specified (not auto)
            if self.language != "auto":
                data["language"] = self.language
            
            # Send request
            response = requests.post(api_url, files=files, data=data)
            
            # Close file
            files["audio_file"][1].close()
            
            # Check response
            if response.status_code != 200:
                error_message = f"Error from Docker API: {response.text}"
                logger.error(error_message)
                return False, {"error": error_message}
            
            # Parse response
            result = response.json()
            
            # Add metadata
            result["source_file"] = str(audio_path)
            result["transcription_method"] = "docker_local"
            result["model_used"] = f"whisper-{model_size}"
            
            # Get audio duration
            try:
                duration = file_manager.get_audio_duration(audio_path)
                result["duration"] = duration
                result["duration_formatted"] = file_manager.format_duration(duration)
            except Exception as e:
                logger.warning(f"Error getting audio duration: {str(e)}")
                result["duration"] = 0
                result["duration_formatted"] = "00:00:00"
            
            # Add timestamp
            result["transcribed_at"] = datetime.datetime.now().isoformat()
            
            # Add language
            if self.language != "auto":
                result["language"] = self.language
            elif "language" in result:
                pass  # Language already in result
            else:
                result["language"] = "auto"
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Save transcription if output_dir is provided
            if output_dir:
                self.save_transcription(result, audio_path, output_dir)
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
            
            return True, result
        
        except requests.RequestException as e:
            error_message = f"Error connecting to Docker API: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
        
        except Exception as e:
            error_message = f"Error transcribing {audio_path}: {str(e)}"
            logger.error(error_message)
            return False, {"error": error_message}
    
    def batch_transcribe(
        self,
        audio_paths: List[Union[str, Path]],
        output_dir: Union[str, Path],
        method: str = "auto",
        model: Optional[str] = None,
        language: Optional[str] = None,
        console: Optional[Console] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Transcribe multiple audio files
        
        Args:
            audio_paths: List of audio file paths
            output_dir: Directory to save transcriptions
            method: Transcription method ("openai_api", "docker_local", "auto")
            model: Model to use (overrides instance model)
            language: Language code (overrides instance language)
            console: Rich console for output
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Success status and results
        """
        # Convert paths to Path objects
        audio_paths = [Path(p) for p in audio_paths]
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided console or instance console
        console = console or self.console
        
        # Override model and language if provided
        if model:
            self.model = model
        if language:
            self.language = language
        
        # Determine transcription method if auto
        if method == "auto":
            method = self.auto_detect_method()
        
        # Create progress bar
        progress = ui_components.create_progress_bar("Transcrevendo áudios")
        
        results = {
            "success": True,
            "transcribed": [],
            "failed": [],
            "total": len(audio_paths),
            "method": method
        }
        
        with progress:
            # Add task
            task = progress.add_task("Iniciando transcrição...", total=len(audio_paths))
            
            # Process each audio file
            for audio_path in audio_paths:
                # Update progress
                progress.update(task, description=f"Transcrevendo {audio_path.name}")
                
                # Transcribe audio
                if method == "openai_api":
                    success, result = self.transcribe_openai_api(
                        audio_path=audio_path,
                        output_dir=output_dir,
                        progress=progress,
                        task_id=task
                    )
                elif method == "docker_local":
                    success, result = self.transcribe_docker_local(
                        audio_path=audio_path,
                        output_dir=output_dir,
                        progress=progress,
                        task_id=task
                    )
                else:
                    error_message = f"Invalid transcription method: {method}"
                    logger.error(error_message)
                    return False, {"error": error_message}
                
                # Store result
                if success:
                    results["transcribed"].append({
                        "audio_path": str(audio_path),
                        "output_path": str(output_dir / f"{audio_path.stem}.txt")
                    })
                else:
                    results["failed"].append({
                        "audio_path": str(audio_path),
                        "error": result.get("error", "Unknown error")
                    })
                    results["success"] = False
        
        # Print summary
        successful = len(results["transcribed"])
        console.print(f"[green]Transcrição concluída: {successful}/{len(audio_paths)} arquivos transcritos com sucesso[/green]")
        
        if results["failed"]:
            console.print(f"[red]Falhas: {len(results['failed'])} arquivos[/red]")
            
            # Print failed files
            for item in results["failed"]:
                console.print(f"[red]  {Path(item['audio_path']).name}: {item['error']}[/red]")
        
        return results["success"], results
    
    def auto_detect_method(self) -> str:
        """
        Auto-detect the best transcription method
        
        Returns:
            str: Transcription method ("openai_api" or "docker_local")
        """
        # Check if OpenAI API key is available
        if self.api_key:
            logger.info("Using OpenAI API for transcription")
            return "openai_api"
        
        # Check if Docker is installed and container can be started
        if self._check_docker_installed() and self._ensure_docker_container_running():
            logger.info("Using Docker local for transcription")
            return "docker_local"
        
        # Default to OpenAI API (will fail if no API key)
        logger.warning("No valid transcription method detected, defaulting to OpenAI API")
        return "openai_api"
    
    def save_transcription(
        self,
        transcription: Dict[str, Any],
        audio_path: Path,
        output_dir: Path
    ) -> Tuple[Path, Path]:
        """
        Save transcription to text and markdown files
        
        Args:
            transcription: Transcription data
            audio_path: Path to audio file
            output_dir: Directory to save transcription
            
        Returns:
            Tuple[Path, Path]: Paths to text and markdown files
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract text
        text = transcription.get("text", "")
        
        # Create YAML header
        yaml_header = {
            "source_file": str(audio_path),
            "transcription_method": transcription.get("transcription_method", "unknown"),
            "model_used": transcription.get("model_used", "unknown"),
            "duration": transcription.get("duration_formatted", "00:00:00"),
            "language": transcription.get("language", "auto"),
            "confidence": transcription.get("confidence", 0.0),
            "transcribed_at": transcription.get("transcribed_at", datetime.datetime.now().isoformat())
        }
        
        # Save text file
        txt_path = output_dir / f"{audio_path.stem}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        # Save markdown file with YAML header
        md_path = output_dir / f"{audio_path.stem}.md"
        file_manager.write_yaml_header(md_path, yaml_header, text)
        
        return txt_path, md_path
    
    def validate_transcription(self, transcription: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate transcription quality
        
        Args:
            transcription: Transcription data
            
        Returns:
            Tuple[bool, Dict[str, Any]]: Validation status and results
        """
        # Extract text
        text = transcription.get("text", "")
        
        # Check if text is empty
        if not text.strip():
            return False, {"error": "Empty transcription"}
        
        # Check text length
        if len(text) < 10:
            return False, {"error": "Transcription too short"}
        
        # Check for common error patterns
        error_patterns = [
            "I couldn't transcribe",
            "Unable to transcribe",
            "Failed to transcribe",
            "Error transcribing"
        ]
        
        for pattern in error_patterns:
            if pattern.lower() in text.lower():
                return False, {"error": f"Error pattern detected: {pattern}"}
        
        # Check confidence if available
        confidence = transcription.get("confidence", 0.0)
        if confidence < 0.5:
            return False, {"error": f"Low confidence: {confidence}"}
        
        return True, {"status": "valid"}
    
    def estimate_cost(self, audio_paths: List[Union[str, Path]], method: str = "openai_api") -> Dict[str, Any]:
        """
        Estimate cost of transcribing audio files
        
        Args:
            audio_paths: List of audio file paths
            method: Transcription method
            
        Returns:
            Dict[str, Any]: Cost estimate
        """
        # Convert paths to Path objects
        audio_paths = [Path(p) for p in audio_paths]
        
        # Calculate total duration
        total_duration = 0.0
        for audio_path in audio_paths:
            try:
                duration = file_manager.get_audio_duration(audio_path)
                total_duration += duration
            except Exception as e:
                logger.warning(f"Error getting duration for {audio_path}: {str(e)}")
        
        # Calculate cost
        cost_estimate = {
            "total_files": len(audio_paths),
            "total_duration": total_duration,
            "total_duration_formatted": file_manager.format_duration(total_duration)
        }
        
        if method == "openai_api":
            # OpenAI Whisper API pricing (as of 2023)
            # $0.006 per minute (rounded to the nearest second)
            cost_per_minute = 0.006
            total_minutes = total_duration / 60
            estimated_cost = total_minutes * cost_per_minute
            
            cost_estimate["method"] = "openai_api"
            cost_estimate["cost_per_minute"] = cost_per_minute
            cost_estimate["estimated_cost_usd"] = round(estimated_cost, 2)
        elif method == "docker_local":
            # Local processing is free
            cost_estimate["method"] = "docker_local"
            cost_estimate["cost_per_minute"] = 0
            cost_estimate["estimated_cost_usd"] = 0
        
        return cost_estimate
    
    def _check_docker_installed(self) -> bool:
        """
        Check if Docker is installed
        
        Returns:
            bool: True if Docker is installed, False otherwise
        """
        try:
            subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception:
            return False
    
    def _ensure_docker_container_running(
        self,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None
    ) -> bool:
        """
        Ensure Docker container is running
        
        Args:
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            bool: True if container is running, False otherwise
        """
        try:
            # Check if container is already running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={DOCKER_CONTAINER_NAME}", "--format", "{{.Names}}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if DOCKER_CONTAINER_NAME in result.stdout:
                logger.info(f"Docker container {DOCKER_CONTAINER_NAME} is already running")
                return True
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, description="Starting Docker container")
            
            # Check if container exists but is not running
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={DOCKER_CONTAINER_NAME}", "--format", "{{.Names}}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if DOCKER_CONTAINER_NAME in result.stdout:
                # Start existing container
                subprocess.run(
                    ["docker", "start", DOCKER_CONTAINER_NAME],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for container to start
                time.sleep(5)
                
                logger.info(f"Started existing Docker container {DOCKER_CONTAINER_NAME}")
                return True
            
            # Pull image if needed
            result = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if f"{DOCKER_IMAGE}:latest" not in result.stdout:
                # Update progress if provided
                if progress and task_id is not None:
                    progress.update(task_id, description=f"Pulling Docker image {DOCKER_IMAGE}")
                
                # Pull image
                subprocess.run(
                    ["docker", "pull", DOCKER_IMAGE],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, description=f"Starting Docker container {DOCKER_CONTAINER_NAME}")
            
            # Run container
            subprocess.run(
                [
                    "docker", "run",
                    "-d",
                    "-p", f"{DOCKER_PORT}:9000",
                    "--name", DOCKER_CONTAINER_NAME,
                    DOCKER_IMAGE
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for container to start
            time.sleep(10)
            
            logger.info(f"Started new Docker container {DOCKER_CONTAINER_NAME}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Docker command: {e.stderr}")
            return False
        
        except Exception as e:
            logger.error(f"Error ensuring Docker container is running: {str(e)}")
            return False
    
    def _stop_docker_container(self) -> bool:
        """
        Stop Docker container
        
        Returns:
            bool: True if container was stopped, False otherwise
        """
        try:
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={DOCKER_CONTAINER_NAME}", "--format", "{{.Names}}"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if DOCKER_CONTAINER_NAME in result.stdout:
                # Stop container
                subprocess.run(
                    ["docker", "stop", DOCKER_CONTAINER_NAME],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                logger.info(f"Stopped Docker container {DOCKER_CONTAINER_NAME}")
                return True
            
            return True  # Container not running, nothing to do
        
        except Exception as e:
            logger.error(f"Error stopping Docker container: {str(e)}")
            return False
    
    def _get_cache_key(self, audio_path: Path, method: str, model: str, language: str) -> str:
        """
        Get cache key for transcription
        
        Args:
            audio_path: Path to audio file
            method: Transcription method
            model: Model used
            language: Language code
            
        Returns:
            str: Cache key
        """
        # Get file hash
        file_hash = file_manager.get_file_hash(audio_path)
        
        # Create cache key
        return f"{file_hash}_{method}_{model}_{language}"
    
    def _check_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Check if transcription is cached
        
        Args:
            cache_key: Cache key
            
        Returns:
            Optional[Dict[str, Any]]: Cached transcription or None
        """
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache file: {str(e)}")
        
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> bool:
        """
        Cache transcription result
        
        Args:
            cache_key: Cache key
            result: Transcription result
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            
            return True
        
        except Exception as e:
            logger.warning(f"Error caching result: {str(e)}")
            return False
    
    def __del__(self):
        """Cleanup when object is deleted"""
        # Stop Docker container if it was started by this instance
        self._stop_docker_container()


def transcribe_audio(
    audio_path: Union[str, Path],
    output_dir: Union[str, Path],
    method: str = "auto",
    model: str = "whisper-1",
    language: str = "auto",
    api_key: Optional[str] = None,
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Transcribe a single audio file
    
    Args:
        audio_path: Path to audio file
        output_dir: Directory to save transcription
        method: Transcription method ("openai_api", "docker_local", "auto")
        model: Model to use
        language: Language code
        api_key: OpenAI API key
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and transcription data
    """
    # Initialize transcriber
    transcriber = WhisperTranscriber(
        api_key=api_key,
        model=model,
        language=language,
        console=console
    )
    
    # Determine transcription method if auto
    if method == "auto":
        method = transcriber.auto_detect_method()
    
    # Transcribe audio
    if method == "openai_api":
        return transcriber.transcribe_openai_api(
            audio_path=audio_path,
            output_dir=output_dir
        )
    elif method == "docker_local":
        return transcriber.transcribe_docker_local(
            audio_path=audio_path,
            output_dir=output_dir
        )
    else:
        error_message = f"Invalid transcription method: {method}"
        logger.error(error_message)
        return False, {"error": error_message}


def batch_transcribe_audio(
    audio_paths: List[Union[str, Path]],
    output_dir: Union[str, Path],
    method: str = "auto",
    model: str = "whisper-1",
    language: str = "auto",
    api_key: Optional[str] = None,
    console: Optional[Console] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Transcribe multiple audio files
    
    Args:
        audio_paths: List of audio file paths
        output_dir: Directory to save transcriptions
        method: Transcription method ("openai_api", "docker_local", "auto")
        model: Model to use
        language: Language code
        api_key: OpenAI API key
        console: Rich console for output
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and results
    """
    # Initialize transcriber
    transcriber = WhisperTranscriber(
        api_key=api_key,
        model=model,
        language=language,
        console=console
    )
    
    # Batch transcribe
    return transcriber.batch_transcribe(
        audio_paths=audio_paths,
        output_dir=output_dir,
        method=method
    )


def estimate_transcription_cost(
    audio_paths: List[Union[str, Path]],
    method: str = "openai_api"
) -> Dict[str, Any]:
    """
    Estimate cost of transcribing audio files
    
    Args:
        audio_paths: List of audio file paths
        method: Transcription method
        
    Returns:
        Dict[str, Any]: Cost estimate
    """
    # Initialize transcriber
    transcriber = WhisperTranscriber()
    
    # Estimate cost
    return transcriber.estimate_cost(audio_paths, method)