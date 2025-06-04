"""
Text-to-Speech generator module for Curso Processor
"""

import os
import re
import json
import asyncio
import tempfile
from pathlib import Path
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Union
import time
import shutil

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from pydantic import BaseModel

from utils import ui_components
from config import settings

# Default voices for Edge TTS
DEFAULT_VOICES = {
    "pt-BR": {
        "female": "pt-BR-FranciscaNeural",
        "male": "pt-BR-AntonioNeural"
    },
    "en-US": {
        "female": "en-US-AriaNeural",
        "male": "en-US-DavisNeural"
    }
}

# Voice settings model for Edge TTS
class VoiceSettings(BaseModel):
    voice: str
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: str = "+0Hz"


class EdgeTTSGenerator:
    """
    Class for generating TTS audio from markdown files using Edge TTS
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the TTS generator
        
        Args:
            console: Rich console for output
        """
        self.console = console or Console()
        self.temp_dir = tempfile.mkdtemp()
        self.available_voices = None
        self.progress = None
        self.current_task = None
        self.resume_data = {}
        self.resume_file = None
    
    async def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices from Edge TTS
        
        Returns:
            List of voice dictionaries
        """
        try:
            # Import edge_tts (only when needed to avoid unnecessary dependencies)
            import edge_tts
            
            if self.available_voices is None:
                self.available_voices = await edge_tts.list_voices()
            return self.available_voices
        except ImportError:
            self.console.print("[bold red]edge-tts não está instalado. Execute 'pip install edge-tts' para instalar.[/bold red]")
            return []
    
    async def preview_voice(self, voice_settings: VoiceSettings, text: str = "Este é um exemplo de texto para demonstrar como esta voz soa.") -> str:
        """
        Generate a preview of the voice
        
        Args:
            voice_settings: Voice settings
            text: Text to preview
            
        Returns:
            Path to the preview audio file
        """
        try:
            # Import edge_tts (only when needed to avoid unnecessary dependencies)
            import edge_tts
            
            communicate = edge_tts.Communicate(
                text,
                voice_settings.voice,
                rate=voice_settings.rate,
                volume=voice_settings.volume,
                pitch=voice_settings.pitch
            )
            
            preview_file = os.path.join(self.temp_dir, "preview.mp3")
            await communicate.save(preview_file)
            return preview_file
        except ImportError:
            self.console.print("[bold red]edge-tts não está instalado. Execute 'pip install edge-tts' para instalar.[/bold red]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]Erro ao gerar preview: {str(e)}[/bold red]")
            return None
    
    def clean_markdown_for_tts(self, content: str) -> str:
        """
        Clean markdown content for TTS processing
        
        Args:
            content: Markdown content
            
        Returns:
            Cleaned text
        """
        # Remove YAML header
        content = re.sub(r'---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # Remove markdown formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)      # Italic
        content = re.sub(r'__(.*?)__', r'\1', content)      # Bold
        content = re.sub(r'_(.*?)_', r'\1', content)        # Italic
        content = re.sub(r'~~(.*?)~~', r'\1', content)      # Strikethrough
        content = re.sub(r'`(.*?)`', r'\1', content)        # Inline code
        
        # Remove code blocks
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # Remove links but keep text
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
        
        # Remove HTML tags
        content = re.sub(r'<.*?>', '', content)
        
        # Remove emojis and special symbols
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE
        )
        content = emoji_pattern.sub(r'', content)
        
        # Convert headers to plain text
        content = re.sub(r'#{1,6}\s+(.*?)$', r'\1.', content, flags=re.MULTILINE)
        
        # Convert lists to text
        content = re.sub(r'^\s*[-*+]\s+(.*?)$', r'\1.', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s+(.*?)$', r'\1.', content, flags=re.MULTILINE)
        
        # Preserve paragraph breaks (convert double newlines to a special token)
        content = re.sub(r'\n\n+', ' PARAGRAPH_BREAK ', content)
        
        # Remove remaining newlines
        content = re.sub(r'\n', ' ', content)
        
        # Restore paragraph breaks
        content = re.sub(r'PARAGRAPH_BREAK', '\n\n', content)
        
        # Fix multiple spaces
        content = re.sub(r' +', ' ', content)
        
        # Fix multiple periods
        content = re.sub(r'\.+', '.', content)
        content = re.sub(r'\. \.', '.', content)
        
        return content.strip()
    
    def split_long_content(self, content: str, max_chars: int = 5000) -> List[str]:
        """
        Split long content into smaller segments
        
        Args:
            content: Text content
            max_chars: Maximum characters per segment
            
        Returns:
            List of text segments
        """
        segments = []
        paragraphs = content.split('\n\n')
        
        current_segment = ""
        for paragraph in paragraphs:
            # If adding this paragraph would exceed max_chars, start a new segment
            if len(current_segment) + len(paragraph) > max_chars and current_segment:
                segments.append(current_segment.strip())
                current_segment = paragraph
            else:
                if current_segment:
                    current_segment += '\n\n' + paragraph
                else:
                    current_segment = paragraph
        
        # Add the last segment if it's not empty
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    async def generate_audio_segment(self, text: str, output_path: str, voice_settings: VoiceSettings) -> str:
        """
        Generate audio for a text segment
        
        Args:
            text: Text segment
            output_path: Output file path
            voice_settings: Voice settings
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Import edge_tts (only when needed to avoid unnecessary dependencies)
            import edge_tts
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Make sure text is not empty
            if not text or text.isspace():
                text = "Conteúdo vazio."
            
            # Create communicate object
            communicate = edge_tts.Communicate(
                text,
                voice_settings.voice,
                rate=voice_settings.rate,
                volume=voice_settings.volume,
                pitch=voice_settings.pitch
            )
            
            # Save audio to file
            await communicate.save(output_path)
            
            # Verify file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                self.console.print(f"[bold yellow]Aviso: Arquivo de áudio vazio ou não criado: {output_path}[/bold yellow]")
                return None
                
        except ImportError:
            self.console.print("[bold red]edge-tts não está instalado. Execute 'pip install edge-tts' para instalar.[/bold red]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]Erro ao gerar segmento de áudio: {str(e)}[/bold red]")
            return None
    
    async def merge_audio_segments(self, segment_files: List[str], output_path: str) -> str:
        """
        Merge multiple audio segments into a single file
        
        Args:
            segment_files: List of audio segment files
            output_path: Output file path
            
        Returns:
            Path to the merged audio file
        """
        try:
            # Check if any segment files exist
            existing_files = [f for f in segment_files if os.path.exists(f)]
            if not existing_files:
                self.console.print("[bold red]Nenhum arquivo de segmento encontrado para mesclar[/bold red]")
                return None
            
            # If only one segment, just copy it
            if len(existing_files) == 1:
                shutil.copy2(existing_files[0], output_path)
                return output_path
            
            # Use ffmpeg to concatenate audio files
            self.console.print(f"[bold cyan]Mesclando {len(existing_files)} segmentos de áudio...[/bold cyan]")
            
            # Create a temporary directory for the merge operation
            merge_temp_dir = tempfile.mkdtemp()
            
            # Create a file list for ffmpeg
            list_file = os.path.join(merge_temp_dir, "file_list.txt")
            with open(list_file, "w") as f:
                for file in existing_files:
                    f.write(f"file '{os.path.abspath(file)}'\n")
            
            # Run ffmpeg to concatenate files
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                "-i", list_file, "-c", "copy", output_path
            ]
            
            self.console.print(f"[dim]Executando: {' '.join(cmd)}[/dim]")
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                self.console.print(f"[bold red]Erro ao mesclar segmentos de áudio: {stderr.decode()}[/bold red]")
                return None
            
            return output_path
            
        except Exception as e:
            self.console.print(f"[bold red]Erro ao mesclar segmentos de áudio: {str(e)}[/bold red]")
            return None
    
    def estimate_audio_duration(self, text: str, words_per_minute: int = 150) -> float:
        """
        Estimate audio duration based on text length
        
        Args:
            text: Text content
            words_per_minute: Words per minute rate
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        minutes = word_count / words_per_minute
        return minutes * 60
    
    def create_resume_file(self, markdown_path: str, output_path: str) -> str:
        """
        Create a resume file for tracking progress
        
        Args:
            markdown_path: Path to markdown file
            output_path: Output audio path
            
        Returns:
            Path to resume file
        """
        resume_dir = os.path.dirname(output_path)
        resume_file = os.path.join(resume_dir, f".{os.path.basename(output_path)}.resume")
        
        self.resume_file = resume_file
        self.resume_data = {
            "markdown_path": markdown_path,
            "output_path": output_path,
            "segments_completed": 0,
            "segments_total": 0,
            "segment_files": [],
            "start_time": time.time()
        }
        
        self._save_resume_data()
        return resume_file
    
    def _save_resume_data(self):
        """Save resume data to file"""
        if self.resume_file:
            with open(self.resume_file, "w") as f:
                json.dump(self.resume_data, f)
    
    def _load_resume_data(self, resume_file: str) -> Dict:
        """Load resume data from file"""
        if os.path.exists(resume_file):
            with open(resume_file, "r") as f:
                return json.load(f)
        return None
    
    async def generate_audio_from_markdown(
        self, 
        markdown_path: str, 
        output_path: str, 
        voice_settings: Optional[VoiceSettings] = None,
        resume: bool = True
    ) -> Tuple[bool, str]:
        """
        Generate audio from markdown file
        
        Args:
            markdown_path: Path to markdown file
            output_path: Output audio path
            voice_settings: Voice settings
            resume: Whether to resume from previous run
            
        Returns:
            Tuple of (success, result)
        """
        try:
            # Import edge_tts (only when needed to avoid unnecessary dependencies)
            import edge_tts
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Check for resume file
            resume_file = os.path.join(
                os.path.dirname(output_path), 
                f".{os.path.basename(output_path)}.resume"
            )
            
            resumed = False
            if resume and os.path.exists(resume_file):
                resume_data = self._load_resume_data(resume_file)
                if resume_data and resume_data["markdown_path"] == markdown_path:
                    self.resume_file = resume_file
                    self.resume_data = resume_data
                    self.console.print(f"[bold green]Retomando geração de TTS de execução anterior[/bold green]")
                    resumed = True
            
            # Read markdown file
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Clean markdown
            cleaned_text = self.clean_markdown_for_tts(content)
            
            # Split into segments
            segments = self.split_long_content(cleaned_text)
            
            # Set default voice if not provided
            if voice_settings is None:
                # Detect language (simple heuristic)
                if any(word in cleaned_text.lower() for word in ["the", "and", "is", "are", "was", "were"]):
                    language = "en-US"
                else:
                    language = "pt-BR"
                
                voice_settings = VoiceSettings(
                    voice=DEFAULT_VOICES[language]["female"]
                )
            
            # Create resume file if not resuming
            if not resumed:
                self.create_resume_file(markdown_path, output_path)
                self.resume_data["segments_total"] = len(segments)
                self.resume_data["segment_files"] = []
                self._save_resume_data()
            
            # Create progress bar
            total_segments = len(segments)
            completed_segments = self.resume_data["segments_completed"]
            
            # Estimate total duration
            total_duration = sum(self.estimate_audio_duration(segment) for segment in segments)
            
            # Generate audio segments
            segment_files = self.resume_data.get("segment_files", [])
            
            # Create a dedicated directory for this TTS job
            job_temp_dir = os.path.join(self.temp_dir, f"tts_job_{int(time.time())}")
            os.makedirs(job_temp_dir, exist_ok=True)
            
            # Process each segment without using Rich Progress
            # This avoids the "Only one live display may be active at once" error
            # when called from a context that already has a progress bar
            for i, segment in enumerate(segments[completed_segments:], start=completed_segments):
                segment_file = os.path.join(job_temp_dir, f"segment_{i:03d}.mp3")
                
                # Generate audio for this segment
                result = await self.generate_audio_segment(segment, segment_file, voice_settings)
                
                if result:
                    # Update progress
                    segment_files.append(segment_file)
                    self.resume_data["segments_completed"] = i + 1
                    self.resume_data["segment_files"] = segment_files
                    self._save_resume_data()
                    self.console.print(f"[dim]Segmento {i+1}/{total_segments} gerado com sucesso[/dim]")
                else:
                    self.console.print(f"[bold yellow]Aviso: Falha ao gerar segmento {i+1}/{total_segments}[/bold yellow]")
                
            # Verify we have segment files
            existing_files = [f for f in segment_files if os.path.exists(f)]
            if not existing_files:
                return False, "Nenhum arquivo de segmento gerado"
            
            # Merge segments
            self.console.print(f"[bold cyan]Mesclando {len(existing_files)} segmentos de áudio...[/bold cyan]")
            result = await self.merge_audio_segments(existing_files, output_path)
            
            if result:
                # Clean up
                if os.path.exists(self.resume_file):
                    os.remove(self.resume_file)
                
                self.console.print(f"[bold green]Áudio gerado com sucesso: {output_path}[/bold green]")
                return True, output_path
            else:
                self.console.print(f"[bold red]Falha ao mesclar segmentos de áudio[/bold red]")
                return False, "Falha ao mesclar segmentos de áudio"
        
        except ImportError:
            self.console.print("[bold red]edge-tts não está instalado. Execute 'pip install edge-tts' para instalar.[/bold red]")
            return False, "edge-tts não está instalado"
        
        except Exception as e:
            self.console.print(f"[bold red]Erro ao gerar áudio: {str(e)}[/bold red]")
            return False, str(e)


def run_async(coroutine):
    """Run an async function in a synchronous context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coroutine)


# Legacy function for backward compatibility
def generate_tts(markdown_path: str, output_path: str, voice: str = None) -> Tuple[bool, str]:
    """
    Generate TTS audio from markdown file
    
    Args:
        markdown_path: Path to markdown file
        output_path: Output audio path
        voice: Voice name (if None, use default)
        
    Returns:
        Tuple of (success, result)
    """
    tts = EdgeTTSGenerator()
    
    voice_settings = None
    if voice:
        voice_settings = VoiceSettings(voice=voice)
    
    return run_async(tts.generate_audio_from_markdown(markdown_path, output_path, voice_settings))