#!/usr/bin/env python3
"""
Curso Processor - Main CLI Interface
A complete course processing system with Nord Theme styling
"""

# Import credentials conditionally to avoid keyring issues
try:
    from config import credentials
    HAS_CREDENTIALS = True
except Exception:
    HAS_CREDENTIALS = False
import os
import sys
import time
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.traceback import install

# Import modules
from config import settings
from utils import file_manager, progress_tracker, ui_components
from process_course import process_complete_course
# Import prompt manager conditionally to avoid import errors
try:
    from utils import prompt_manager
    HAS_PROMPT_MANAGER = True
except Exception:
    HAS_PROMPT_MANAGER = False
# Import maintenance conditionally to avoid keyring issues
try:
    import maintenance
    HAS_MAINTENANCE = True
except Exception:
    HAS_MAINTENANCE = False

# Install rich traceback handler
install(show_locals=True)

# Initialize typer app
app = typer.Typer(help="Curso Processor - A complete course processing system")

# Initialize rich console with Nord Theme colors
console = Console()

# Nord Theme colors
NORD_WHITE = "bright_white"
NORD_BLUE = "bright_blue"
NORD_CYAN = "bright_cyan"
NORD_GREEN = "bright_green"
NORD_YELLOW = "bright_yellow"
NORD_RED = "bright_red"
NORD_DIM = "dim white"

# Import UI components
from utils.ui_components import (
    console, NORD_BLUE, NORD_CYAN, NORD_GREEN, NORD_YELLOW, NORD_RED, NORD_DIM,
    show_welcome, display_ascii_art, create_progress_bar, handle_error, display_system_status
)

# Import settings manager
from utils.settings_manager import configure_settings

def display_menu():
    """Display the main menu with Nord Theme styling"""
    # Display system status
    display_system_status()
    
    # Create menu panel with all options
    menu_panel = Panel(
        Text.from_markup(
            "\n".join([
                f"[{NORD_BLUE}][1][/{NORD_BLUE}] 🎬 Converter Vídeos para Áudio",
                f"[{NORD_BLUE}][2][/{NORD_BLUE}] 📝 Transcrever Áudios (Whisper/Local)",
                f"[{NORD_BLUE}][3][/{NORD_BLUE}] 🤖 Processar com IA (Claude/ChatGPT)",
                f"[{NORD_BLUE}][4][/{NORD_BLUE}] ⏱️ Gerar Timestamps",
                f"[{NORD_BLUE}][5][/{NORD_BLUE}] 🎙️ Criar Áudio TTS",
                f"[{NORD_BLUE}][6][/{NORD_BLUE}] 📊 Gerar XML Podcast",
                f"[{NORD_BLUE}][7][/{NORD_BLUE}] ☁️ Upload Google Drive",
                f"[{NORD_BLUE}][8][/{NORD_BLUE}] 🔗 Atualizar GitHub",
                f"[{NORD_BLUE}][9][/{NORD_BLUE}] 🔄 Processar Curso Completo",
                f"[{NORD_BLUE}][10][/{NORD_BLUE}] ⚙️ Configurações",
                f"[{NORD_BLUE}][11][/{NORD_BLUE}] 🔧 Manutenção do Sistema",
                f"[{NORD_BLUE}][12][/{NORD_BLUE}] 📝 Gerenciador de Prompts",
                f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Sair"
            ])
        ),
        title="[bold]Menu Principal[/bold]",
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    console.print(menu_panel)

def convert_videos():
    """Convert videos to audio"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando conversão de vídeos para áudio...[/{NORD_CYAN}]")
        
        # Get input directory
        input_dir = Prompt.ask("[bold]Diretório com vídeos", default=settings.get_default_video_dir())
        
        # Get output directory
        output_dir = Prompt.ask("[bold]Diretório para salvar áudios", default=settings.get_default_audio_dir())
        
        # Get file extension filter
        extensions = Prompt.ask("[bold]Extensões de vídeo (separadas por vírgula)", default="mp4,mkv,avi,mov")
        ext_list = [ext.strip() for ext in extensions.split(",")]
        
        # Ensure directories exist
        file_manager.ensure_directory_exists(input_dir)
        file_manager.ensure_directory_exists(output_dir)
        
        # Import audio converter module
        from modules import audio_converter
        
        # Get video files
        video_files = file_manager.get_files_by_extensions(input_dir, ext_list)
        
        if not video_files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo de vídeo encontrado em {input_dir}[/{NORD_YELLOW}]")
            return
        
        # Display files to be converted
        console.print(f"[{NORD_GREEN}]Encontrados {len(video_files)} arquivos de vídeo[/{NORD_GREEN}]")
        
        # Ask for confirmation
        if not Confirm.ask("[bold]Deseja converter todos os arquivos?"):
            console.print(f"[{NORD_YELLOW}]Operação cancelada pelo usuário[/{NORD_YELLOW}]")
            return
        
        # Convert videos to audio
        converter = audio_converter.AudioConverter(console=console)
        
        results = converter.batch_convert(
            video_files=video_files,
            output_dir=output_dir,
            audio_format="mp3",
            audio_quality="192k"
        )
        
        # Display results
        if results["converted"]:
            console.print(f"[{NORD_GREEN}]Conversão concluída com sucesso![/{NORD_GREEN}]")
            
            # Display converted files
            console.print(f"[{NORD_CYAN}]Arquivos convertidos:[/{NORD_CYAN}]")
            
            table = Table(show_header=True, header_style=NORD_BLUE)
            table.add_column("Arquivo de Vídeo")
            table.add_column("Arquivo de Áudio")
            
            for item in results["converted"]:
                table.add_row(
                    os.path.basename(item["video_path"]),
                    os.path.basename(item["audio_path"])
                )
            
            console.print(table)
        
        # Display failed conversions
        if results["failed"]:
            console.print(f"[{NORD_RED}]Falhas na conversão:[/{NORD_RED}]")
            
            table = Table(show_header=True, header_style=NORD_RED)
            table.add_column("Arquivo de Vídeo")
            table.add_column("Erro")
            
            for item in results["failed"]:
                table.add_row(
                    os.path.basename(item["video_path"]),
                    item["error"]
                )
            
            console.print(table)
        
    except Exception as e:
        handle_error("Erro ao converter vídeos", e)

def transcribe_audio():
    """Transcribe audio files"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando transcrição de áudios...[/{NORD_CYAN}]")
        
        # Get input directory
        input_dir = Prompt.ask("[bold]Diretório com áudios", default=settings.get_default_audio_dir())
        
        # Get output directory
        output_dir = Prompt.ask("[bold]Diretório para salvar transcrições", default=settings.get_default_transcription_dir())
        
        # Get file extension filter
        extensions = Prompt.ask("[bold]Extensões de áudio (separadas por vírgula)", default="mp3,wav,m4a,ogg")
        ext_list = [ext.strip() for ext in extensions.split(",")]
        
        # Ensure directories exist
        file_manager.ensure_directory_exists(input_dir)
        file_manager.ensure_directory_exists(output_dir)
        
        # Import transcription module
        from modules import transcription
        
        # Get audio files
        audio_files = file_manager.get_files_by_extensions(input_dir, ext_list)
        
        if not audio_files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo de áudio encontrado em {input_dir}[/{NORD_YELLOW}]")
            return
        
        # Display files to be transcribed
        console.print(f"[{NORD_GREEN}]Encontrados {len(audio_files)} arquivos de áudio[/{NORD_GREEN}]")
        
        # Ask for confirmation
        if not Confirm.ask("[bold]Deseja transcrever todos os arquivos?"):
            console.print(f"[{NORD_YELLOW}]Operação cancelada pelo usuário[/{NORD_YELLOW}]")
            return
        
        # Ask for transcription method
        method_choices = ["openai_api", "docker_local", "auto"]
        method = Prompt.ask("[bold]Método de transcrição", choices=method_choices, default="auto")
        
        # Ask for model
        model_choices = ["tiny", "base", "small", "medium", "large"]
        model = Prompt.ask("[bold]Modelo Whisper", choices=model_choices, default="medium")
        
        # Ask for language
        language_choices = ["pt", "en", "auto"]
        language = Prompt.ask("[bold]Idioma", choices=language_choices, default="pt")
        
        # Check if method is available
        if method == "docker_local" or method == "auto":
            # Check if Docker is available
            docker_available = transcription.check_docker_available()
            
            if not docker_available:
                console.print(f"[{NORD_YELLOW}]Docker não está disponível para transcrição local.[/{NORD_YELLOW}]")
                
                if method == "docker_local":
                    if Confirm.ask("[bold]Deseja usar a API OpenAI como alternativa?"):
                        method = "openai_api"
                    else:
                        return
                else:  # method == "auto"
                    method = "openai_api"
                    console.print(f"[{NORD_YELLOW}]Usando API OpenAI como alternativa.[/{NORD_YELLOW}]")
        
        # Initialize transcriber
        transcriber = transcription.WhisperTranscriber(
            model=model,
            language=language,
            console=console
        )
        
        # Batch transcribe audio files
        success, results = transcriber.batch_transcribe(
            audio_paths=audio_files,
            output_dir=output_dir,
            method=method
        )
        
        # Display results
        if success:
            console.print(f"[{NORD_GREEN}]Transcrição concluída com sucesso![/{NORD_GREEN}]")
            
            # Display transcribed files
            if results["transcribed"]:
                console.print(f"[{NORD_CYAN}]Arquivos transcritos:[/{NORD_CYAN}]")
                
                table = Table(show_header=True, header_style=NORD_BLUE)
                table.add_column("Arquivo de Áudio")
                table.add_column("Arquivo de Transcrição")
                
                for item in results["transcribed"]:
                    table.add_row(
                        os.path.basename(item["audio_path"]),
                        os.path.basename(item["output_path"])
                    )
                
                console.print(table)
        else:
            console.print(f"[{NORD_RED}]Erro na transcrição: {results.get('error', 'Erro desconhecido')}[/{NORD_RED}]")
            
            # Display failed files
            if results.get("failed"):
                console.print(f"[{NORD_RED}]Arquivos com erro:[/{NORD_RED}]")
                
                table = Table(show_header=True, header_style=NORD_RED)
                table.add_column("Arquivo de Áudio")
                table.add_column("Erro")
                
                for item in results["failed"]:
                    table.add_row(
                        os.path.basename(item["audio_path"]),
                        item["error"]
                    )
                
                console.print(table)
        
    except Exception as e:
        handle_error("Erro ao transcrever áudios", e)

def process_with_ai():
    """Process transcriptions with AI"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando processamento com IA...[/{NORD_CYAN}]")
        
        # Get input directory
        input_dir = Prompt.ask("[bold]Diretório com transcrições", default=settings.get_default_transcription_dir())
        
        # Get output directory
        output_dir = Prompt.ask("[bold]Diretório para salvar processados", default=settings.get_default_processed_dir())
        
        # Ensure directories exist
        file_manager.ensure_directory_exists(input_dir)
        file_manager.ensure_directory_exists(output_dir)
        
        # Import AI processor module
        from modules import ai_processor
        
        # Get text files
        text_files = file_manager.get_text_files(input_dir)
        
        if not text_files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo de texto encontrado em {input_dir}[/{NORD_YELLOW}]")
            return
        
        # Display files to be processed
        console.print(f"[{NORD_GREEN}]Encontrados {len(text_files)} arquivos de texto[/{NORD_GREEN}]")
        
        # Ask for AI model
        model_choices = ["claude", "chatgpt", "auto"]
        model = Prompt.ask("[bold]Modelo de IA", choices=model_choices, default="auto")
        
        # Ask for prompt template
        from pathlib import Path
        prompt_dir = Path("prompts")
        prompt_files = list(prompt_dir.glob("*.txt"))
        
        if not prompt_files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo de prompt encontrado em {prompt_dir}[/{NORD_YELLOW}]")
            return
        
        prompt_choices = [f.stem for f in prompt_files]
        prompt_template = Prompt.ask("[bold]Template de prompt", choices=prompt_choices, default="default_prompt")
        
        # Initialize AI processor
        processor = ai_processor.AIProcessor(
            model=model,
            console=console
        )
        
        # Load prompt template
        prompt_path = prompt_dir / f"{prompt_template}.txt"
        processor.load_prompt_template(prompt_path)
        
        # Process each file
        results = {"success": [], "failed": []}
        
        with Progress(
            TextColumn(f"[{NORD_BLUE}]{{task.description}}[/{NORD_BLUE}]"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Processando arquivos...[/{NORD_CYAN}]", total=len(text_files))
            
            for text_file in text_files:
                # Generate output path
                output_filename = os.path.splitext(os.path.basename(text_file))[0] + ".md"
                output_path = os.path.join(output_dir, output_filename)
                
                # Process file
                success, result = processor.process_file(
                    input_path=text_file,
                    output_path=output_path
                )
                
                if success:
                    results["success"].append((text_file, output_path))
                else:
                    results["failed"].append((text_file, result))
                
                progress.update(task, advance=1)
        
        # Display results
        if results["success"]:
            console.print(f"[{NORD_GREEN}]Processamento concluído com sucesso para {len(results['success'])} arquivos![/{NORD_GREEN}]")
            
            # Display processed files
            console.print(f"[{NORD_CYAN}]Arquivos processados:[/{NORD_CYAN}]")
            
            table = Table(show_header=True, header_style=NORD_BLUE)
            table.add_column("Arquivo de Texto")
            table.add_column("Arquivo Processado")
            
            for text_file, output_path in results["success"]:
                table.add_row(
                    os.path.basename(text_file),
                    os.path.basename(output_path)
                )
            
            console.print(table)
        
        if results["failed"]:
            console.print(f"[{NORD_RED}]Falha no processamento para {len(results['failed'])} arquivos:[/{NORD_RED}]")
            
            table = Table(show_header=True, header_style=NORD_RED)
            table.add_column("Arquivo de Texto")
            table.add_column("Erro")
            
            for text_file, error in results["failed"]:
                table.add_row(
                    os.path.basename(text_file),
                    str(error)
                )
            
            console.print(table)
        
    except Exception as e:
        handle_error("Erro ao processar com IA", e)

def generate_timestamps():
    """Generate timestamps for transcriptions"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando geração de timestamps...[/{NORD_CYAN}]")
        
        # Ask for source type
        source_choices = ["markdown", "whisper", "text"]
        source_type = Prompt.ask("[bold]Tipo de fonte", choices=source_choices, default="markdown")
        
        if source_type == "markdown":
            # Get input directory
            input_dir = Prompt.ask("[bold]Diretório com arquivos markdown", default=settings.get_default_processed_dir())
            
            # Get output directory
            output_dir = Prompt.ask("[bold]Diretório para salvar timestamps", default=input_dir)
            
            # Ask for format type
            format_choices = ["json", "csv", "txt"]
            format_type = Prompt.ask("[bold]Formato de saída", choices=format_choices, default="json")
            
            # Ask if recursive
            recursive = Confirm.ask("[bold]Buscar arquivos recursivamente?", default=True)
            
            # Ensure directories exist
            file_manager.ensure_directory_exists(input_dir)
            file_manager.ensure_directory_exists(output_dir)
            
            # Import timestamp generator module
            from modules import timestamp_generator
            
            # Generate timestamps
            success, results = timestamp_generator.batch_generate_timestamps_from_markdown(
                markdown_dir=input_dir,
                output_dir=output_dir,
                format_type=format_type,
                recursive=recursive,
                console=console
            )
            
            # Display results
            if success:
                console.print(f"[{NORD_GREEN}]Geração de timestamps concluída com sucesso![/{NORD_GREEN}]")
                
                # Display processed files
                if results["processed"]:
                    console.print(f"[{NORD_CYAN}]Arquivos processados:[/{NORD_CYAN}]")
                    
                    table = Table(show_header=True, header_style=NORD_BLUE)
                    table.add_column("Arquivo Markdown")
                    table.add_column("Arquivo de Timestamps")
                    
                    for item in results["processed"]:
                        table.add_row(
                            os.path.basename(item["markdown_path"]),
                            os.path.basename(item["output_path"])
                        )
                    
                    console.print(table)
            else:
                console.print(f"[{NORD_RED}]Erro na geração de timestamps: {results.get('error', 'Erro desconhecido')}[/{NORD_RED}]")
        
        elif source_type == "whisper":
            # Get input directory
            input_dir = Prompt.ask("[bold]Diretório com arquivos JSON do Whisper", default=settings.get_default_transcription_dir())
            
            # Get output directory
            output_dir = Prompt.ask("[bold]Diretório para salvar timestamps", default=input_dir)
            
            # Ensure directories exist
            file_manager.ensure_directory_exists(input_dir)
            file_manager.ensure_directory_exists(output_dir)
            
            # Get JSON files
            json_files = list(Path(input_dir).glob("*.json"))
            
            if not json_files:
                console.print(f"[{NORD_YELLOW}]Nenhum arquivo JSON encontrado em {input_dir}[/{NORD_YELLOW}]")
                return
            
            # Display files to be processed
            console.print(f"[{NORD_GREEN}]Encontrados {len(json_files)} arquivos JSON[/{NORD_GREEN}]")
            
            # Import timestamp generator module
            from modules import timestamp_generator
            
            # Generate timestamps
            results = timestamp_generator.batch_generate_timestamps(
                file_paths=[str(f) for f in json_files],
                output_dir=output_dir,
                is_whisper_json=True
            )
            
            # Count successful generations
            successful = sum(1 for result in results if result[0])
            
            # Display results
            console.print(f"[{NORD_GREEN}]Geração de timestamps concluída: {successful}/{len(json_files)} arquivos processados com sucesso[/{NORD_GREEN}]")
        
        elif source_type == "text":
            # Get input directory
            input_dir = Prompt.ask("[bold]Diretório com arquivos de texto", default=settings.get_default_transcription_dir())
            
            # Get output directory
            output_dir = Prompt.ask("[bold]Diretório para salvar timestamps", default=input_dir)
            
            # Ensure directories exist
            file_manager.ensure_directory_exists(input_dir)
            file_manager.ensure_directory_exists(output_dir)
            
            # Get text files
            text_files = file_manager.get_text_files(input_dir)
            
            if not text_files:
                console.print(f"[{NORD_YELLOW}]Nenhum arquivo de texto encontrado em {input_dir}[/{NORD_YELLOW}]")
                return
            
            # Display files to be processed
            console.print(f"[{NORD_GREEN}]Encontrados {len(text_files)} arquivos de texto[/{NORD_GREEN}]")
            
            # Import timestamp generator module
            from modules import timestamp_generator
            
            # Generate timestamps
            results = timestamp_generator.batch_generate_timestamps(
                file_paths=[str(f) for f in text_files],
                output_dir=output_dir,
                is_whisper_json=False
            )
            
            # Count successful generations
            successful = sum(1 for result in results if result[0])
            
            # Display results
            console.print(f"[{NORD_GREEN}]Geração de timestamps concluída: {successful}/{len(text_files)} arquivos processados com sucesso[/{NORD_GREEN}]")
        
    except Exception as e:
        handle_error("Erro ao gerar timestamps", e)

def create_tts_audio():
    """Create TTS audio from processed text"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando geração de áudio TTS...[/{NORD_CYAN}]")
        
        # Get input directory or file
        input_path = Prompt.ask("[bold]Arquivo ou diretório com arquivos markdown", default=settings.get_default_processed_dir())
        
        # Get output directory
        output_dir = Prompt.ask("[bold]Diretório para salvar arquivos de áudio", default=settings.get_default_audio_dir())
        
        # Ensure directories exist
        file_manager.ensure_directory_exists(output_dir)
        
        # Import TTS generator module
        from modules.tts_generator import EdgeTTSGenerator, VoiceSettings, run_async
        
        # Create TTS generator
        tts = EdgeTTSGenerator(console=console)
        
        # Check if input is a file or directory
        if os.path.isfile(input_path):
            markdown_files = [input_path]
        else:
            # Get markdown files
            markdown_files = file_manager.get_markdown_files(input_path)
        
        if not markdown_files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo markdown encontrado em {input_path}[/{NORD_YELLOW}]")
            return
        
        # Display files to be processed
        console.print(f"[{NORD_GREEN}]Encontrados {len(markdown_files)} arquivos markdown[/{NORD_GREEN}]")
        
        # List available voices
        voices = run_async(tts.get_available_voices())
        
        # Group voices by language
        voices_by_language = {}
        for voice in voices:
            lang = voice.get("Locale", "unknown")
            if lang not in voices_by_language:
                voices_by_language[lang] = []
            voices_by_language[lang].append(voice)
        
        # Display available languages
        console.print(f"[{NORD_CYAN}]Idiomas disponíveis:[/{NORD_CYAN}]")
        languages = sorted(voices_by_language.keys())
        
        for i, lang in enumerate(languages):
            console.print(f"[{NORD_BLUE}]{i+1}.[/{NORD_BLUE}] {lang} ({len(voices_by_language[lang])} vozes)")
        
        # Select language
        lang_idx = int(Prompt.ask("[bold]Selecione o idioma (número)", default="1")) - 1
        selected_language = languages[lang_idx]
        
        # Display voices for selected language
        console.print(f"[{NORD_CYAN}]Vozes disponíveis para {selected_language}:[/{NORD_CYAN}]")
        
        voices_in_language = voices_by_language[selected_language]
        for i, voice in enumerate(voices_in_language):
            gender = "Feminina" if "Female" in voice.get("Gender", "") else "Masculina"
            console.print(f"[{NORD_BLUE}]{i+1}.[/{NORD_BLUE}] {voice.get('ShortName')} - {voice.get('DisplayName')} ({gender})")
        
        # Select voice
        voice_idx = int(Prompt.ask("[bold]Selecione a voz (número)", default="1")) - 1
        selected_voice = voices_in_language[voice_idx]["ShortName"]
        
        # Create voice settings
        voice_settings = VoiceSettings(
            voice=selected_voice,
            rate=Prompt.ask("[bold]Taxa de fala (ex: +0%, -10%, +20%)", default="+0%"),
            volume=Prompt.ask("[bold]Volume (ex: +0%, -10%, +20%)", default="+0%"),
            pitch=Prompt.ask("[bold]Tom (ex: +0Hz, -10Hz, +20Hz)", default="+0Hz")
        )
        
        # Preview voice
        console.print(f"[{NORD_CYAN}]Gerando preview da voz...[/{NORD_CYAN}]")
        preview_text = "Este é um exemplo de como esta voz soa. Será utilizada para gerar o áudio do seu curso."
        preview_path = run_async(tts.preview_voice(voice_settings, preview_text))
        
        if preview_path:
            console.print(f"[{NORD_GREEN}]Preview gerado: {preview_path}[/{NORD_GREEN}]")
            
            # Ask to play preview
            if Confirm.ask("[bold]Deseja reproduzir o preview?", default=True):
                # Try to play with different commands based on OS
                try:
                    if sys.platform == "darwin":  # macOS
                        os.system(f"afplay {preview_path}")
                    elif sys.platform == "win32":  # Windows
                        os.system(f"start {preview_path}")
                    else:  # Linux
                        os.system(f"ffplay -nodisp -autoexit {preview_path} 2>/dev/null")
                except:
                    console.print(f"[{NORD_YELLOW}]Não foi possível reproduzir o áudio automaticamente.[/{NORD_YELLOW}]")
        
        # Confirm voice selection
        if not Confirm.ask("[bold]Deseja continuar com esta voz?", default=True):
            console.print(f"[{NORD_YELLOW}]Operação cancelada pelo usuário.[/{NORD_YELLOW}]")
            return
        
        # Process each markdown file
        results = {"success": [], "failed": []}
        
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Processando arquivos...[/{NORD_CYAN}]", total=len(markdown_files))
            
            for markdown_file in markdown_files:
                # Generate output path
                output_filename = os.path.splitext(os.path.basename(markdown_file))[0] + ".mp3"
                output_path = os.path.join(output_dir, output_filename)
                
                # Generate audio
                success, result = run_async(tts.generate_audio_from_markdown(
                    markdown_path=markdown_file,
                    output_path=output_path,
                    voice_settings=voice_settings
                ))
                
                if success:
                    results["success"].append((markdown_file, output_path))
                else:
                    results["failed"].append((markdown_file, result))
                
                progress.update(task, advance=1)
        
        # Display results
        if results["success"]:
            console.print(f"[{NORD_GREEN}]Geração de áudio concluída com sucesso para {len(results['success'])} arquivos![/{NORD_GREEN}]")
            
            # Display processed files
            console.print(f"[{NORD_CYAN}]Arquivos processados:[/{NORD_CYAN}]")
            
            table = Table(show_header=True, header_style=NORD_BLUE)
            table.add_column("Arquivo Markdown")
            table.add_column("Arquivo de Áudio")
            
            for markdown_file, audio_file in results["success"]:
                table.add_row(
                    os.path.basename(markdown_file),
                    os.path.basename(audio_file)
                )
            
            console.print(table)
        
        if results["failed"]:
            console.print(f"[{NORD_RED}]Falha na geração de áudio para {len(results['failed'])} arquivos:[/{NORD_RED}]")
            
            table = Table(show_header=True, header_style=NORD_RED)
            table.add_column("Arquivo Markdown")
            table.add_column("Erro")
            
            for markdown_file, error in results["failed"]:
                table.add_row(
                    os.path.basename(markdown_file),
                    str(error)
                )
            
            console.print(table)
        
    except Exception as e:
        handle_error("Erro ao gerar áudio TTS", e)

def generate_xml():
    """Generate XML podcast feed"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando geração de XML para podcast...[/{NORD_CYAN}]")
        
        # Import XML generator module
        from modules import xml_generator
        
        # Get course information
        course_title = Prompt.ask("[bold]Título do curso")
        course_description = Prompt.ask("[bold]Descrição do curso")
        course_author = Prompt.ask("[bold]Autor do curso")
        course_language = Prompt.ask("[bold]Idioma do curso (ex: pt-br)", default="pt-br")
        course_category = Prompt.ask("[bold]Categoria do curso", default="Education")
        course_image_url = Prompt.ask("[bold]URL da imagem do curso (opcional)")
        
        # Get audio directory
        audio_dir = Prompt.ask("[bold]Diretório com arquivos de áudio", default=settings.get_default_audio_dir())
        
        # Get output directory
        output_dir = Prompt.ask("[bold]Diretório para salvar XML", default=settings.get_default_xml_dir())
        
        # Get output filename
        output_filename = Prompt.ask("[bold]Nome do arquivo XML", default="podcast.xml")
        
        # Ensure directories exist
        file_manager.ensure_directory_exists(audio_dir)
        file_manager.ensure_directory_exists(output_dir)
        
        # Get audio files
        audio_files = file_manager.get_files_by_extensions(audio_dir, ["mp3"])
        
        if not audio_files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo de áudio encontrado em {audio_dir}[/{NORD_YELLOW}]")
            return
        
        # Display files to be included
        console.print(f"[{NORD_GREEN}]Encontrados {len(audio_files)} arquivos de áudio[/{NORD_GREEN}]")
        
        # Ask for base URL
        base_url = Prompt.ask("[bold]URL base para os arquivos de áudio")
        
        # Create XML generator
        generator = xml_generator.PodcastXMLGenerator(
            title=course_title,
            description=course_description,
            author=course_author,
            language=course_language,
            category=course_category,
            image_url=course_image_url if course_image_url else None
        )
        
        # Add episodes
        with Progress(
            TextColumn(f"[{NORD_BLUE}]{{task.description}}[/{NORD_BLUE}]"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Adicionando episódios...[/{NORD_CYAN}]", total=len(audio_files))
            
            for audio_file in audio_files:
                # Get episode title from filename
                episode_title = os.path.splitext(os.path.basename(audio_file))[0]
                
                # Look for corresponding markdown file
                markdown_path = os.path.join(
                    settings.get_default_processed_dir(),
                    f"{episode_title}.md"
                )
                
                episode_description = ""
                if os.path.exists(markdown_path):
                    with open(markdown_path, 'r', encoding='utf-8') as f:
                        # Read first 500 characters as description
                        episode_description = f.read(500) + "..."
                
                # Look for corresponding timestamp file
                timestamp_path = os.path.join(
                    os.path.dirname(audio_file),
                    f"{episode_title}.json"
                )
                
                timestamps = None
                if os.path.exists(timestamp_path):
                    try:
                        import json
                        with open(timestamp_path, 'r', encoding='utf-8') as f:
                            timestamps = json.load(f)
                    except:
                        pass
                
                # Generate episode URL
                episode_url = f"{base_url.rstrip('/')}/{os.path.basename(audio_file)}"
                
                # Add episode
                generator.add_episode(
                    title=episode_title,
                    audio_url=episode_url,
                    description=episode_description,
                    timestamps=timestamps
                )
                
                progress.update(task, advance=1)
        
        # Generate XML
        output_path = os.path.join(output_dir, output_filename)
        generator.generate_xml(output_path)
        
        console.print(f"[{NORD_GREEN}]XML gerado com sucesso: {output_path}[/{NORD_GREEN}]")
        
        # Generate timestamps markdown
        timestamps_md_path = os.path.join(output_dir, "timestamps.md")
        generator.generate_timestamps_markdown(timestamps_md_path)
        
        console.print(f"[{NORD_GREEN}]Markdown de timestamps gerado: {timestamps_md_path}[/{NORD_GREEN}]")
        
    except Exception as e:
        handle_error("Erro ao gerar XML", e)

def upload_to_drive():
    """Upload files to Google Drive"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando upload para Google Drive...[/{NORD_CYAN}]")
        
        # Import Drive uploader module
        from modules import drive_uploader
        
        # Get input directory
        input_dir = Prompt.ask("[bold]Diretório com arquivos para upload", default=settings.get_default_audio_dir())
        
        # Get file extensions
        extensions = Prompt.ask("[bold]Extensões de arquivo (separadas por vírgula)", default="mp3,xml,md")
        ext_list = [ext.strip() for ext in extensions.split(",")]
        
        # Ensure directory exists
        file_manager.ensure_directory_exists(input_dir)
        
        # Get files
        files = file_manager.get_files_by_extensions(input_dir, ext_list)
        
        if not files:
            console.print(f"[{NORD_YELLOW}]Nenhum arquivo encontrado em {input_dir} com as extensões {', '.join(ext_list)}[/{NORD_YELLOW}]")
            return
        
        # Display files to be uploaded
        console.print(f"[{NORD_GREEN}]Encontrados {len(files)} arquivos para upload[/{NORD_GREEN}]")
        
        # Ask for Drive folder name
        folder_name = Prompt.ask("[bold]Nome da pasta no Google Drive")
        
        # Ask for sharing options
        share_publicly = Confirm.ask("[bold]Compartilhar pasta publicamente?", default=True)
        
        # Create Drive uploader
        uploader = drive_uploader.GoogleDriveManager(console=console)
        
        # Authenticate
        if not uploader.authenticate():
            console.print(f"[{NORD_RED}]Falha na autenticação com o Google Drive[/{NORD_RED}]")
            return
        
        # Create folder
        folder_id = uploader.create_folder(folder_name)
        
        if not folder_id:
            console.print(f"[{NORD_RED}]Falha ao criar pasta no Google Drive[/{NORD_RED}]")
            return
        
        console.print(f"[{NORD_GREEN}]Pasta criada no Google Drive: {folder_name} (ID: {folder_id})[/{NORD_GREEN}]")
        
        # Upload files
        results = {"success": [], "failed": []}
        
        with Progress(
            TextColumn(f"[{NORD_BLUE}]{{task.description}}[/{NORD_BLUE}]"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Fazendo upload de arquivos...[/{NORD_CYAN}]", total=len(files))
            
            for file_path in files:
                # Upload file
                file_id = uploader.upload_file(
                    file_path=file_path,
                    folder_id=folder_id
                )
                
                if file_id:
                    results["success"].append((file_path, file_id))
                else:
                    results["failed"].append(file_path)
                
                progress.update(task, advance=1)
        
        # Share folder if requested
        if share_publicly and folder_id:
            share_link = uploader.share_folder(folder_id)
            
            if share_link:
                console.print(f"[{NORD_GREEN}]Pasta compartilhada publicamente: {share_link}[/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Falha ao compartilhar pasta[/{NORD_RED}]")
        
        # Display results
        if results["success"]:
            console.print(f"[{NORD_GREEN}]Upload concluído com sucesso para {len(results['success'])} arquivos![/{NORD_GREEN}]")
            
            # Display uploaded files
            console.print(f"[{NORD_CYAN}]Arquivos enviados:[/{NORD_CYAN}]")
            
            table = Table(show_header=True, header_style=NORD_BLUE)
            table.add_column("Arquivo")
            table.add_column("ID no Google Drive")
            
            for file_path, file_id in results["success"]:
                table.add_row(
                    os.path.basename(file_path),
                    file_id
                )
            
            console.print(table)
        
        if results["failed"]:
            console.print(f"[{NORD_RED}]Falha no upload para {len(results['failed'])} arquivos:[/{NORD_RED}]")
            
            table = Table(show_header=True, header_style=NORD_RED)
            table.add_column("Arquivo")
            
            for file_path in results["failed"]:
                table.add_row(os.path.basename(file_path))
            
            console.print(table)
        
    except Exception as e:
        handle_error("Erro ao fazer upload para o Google Drive", e)

def update_github():
    """Update GitHub repository"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando atualização do GitHub...[/{NORD_CYAN}]")
        
        # Import GitHub manager module
        from modules import github_manager_fixed as github_manager
        
        # Get local repository path
        repo_path = Prompt.ask("[bold]Caminho do repositório local", default=settings.get_default_github_dir())
        
        # Ensure directory exists
        file_manager.ensure_directory_exists(repo_path)
        
        # Create GitHub manager
        # Get GitHub credentials
        github_credentials = credentials.get_github_credentials()
        
        # Create GitHub manager
        manager = github_manager.GitHubManager(
            repo_path=repo_path,
            credentials=github_credentials
        )
        
        # Check if repository is valid
        if not manager.is_valid_repository():
            console.print(f"[{NORD_RED}]O diretório {repo_path} não é um repositório Git válido[/{NORD_RED}]")
            
            # Ask if user wants to clone a repository
            if Confirm.ask("[bold]Deseja clonar um repositório?"):
                repo_url = Prompt.ask("[bold]URL do repositório")
                
                # Clone repository
                success, message = manager.clone_repository(repo_url, repo_path)
                if success:
                    console.print(f"[{NORD_GREEN}]Repositório clonado com sucesso![/{NORD_GREEN}]")
                else:
                    console.print(f"[{NORD_RED}]Falha ao clonar repositório: {message}[/{NORD_RED}]")
                    return
            else:
                return
        
        # Get repository status
        status = manager.get_status()
        
        console.print(f"[{NORD_CYAN}]Status do repositório:[/{NORD_CYAN}]")
        
        if "error" in status:
            console.print(f"[{NORD_RED}]{status['error']}[/{NORD_RED}]")
            return
            
        # Display repository information
        console.print(f"Branch atual: [{NORD_GREEN}]{status.get('current_branch', 'N/A')}[/{NORD_GREEN}]")
        
        # Display remotes
        if status.get('remotes'):
            console.print(f"[{NORD_CYAN}]Remotes:[/{NORD_CYAN}]")
            for name, url in status.get('remotes', {}).items():
                console.print(f"  {name}: [{NORD_BLUE}]{url}[/{NORD_BLUE}]")
        
        # Display modified files
        if status.get('modified_files'):
            console.print(f"[{NORD_YELLOW}]Arquivos modificados:[/{NORD_YELLOW}]")
            for file in status.get('modified_files', []):
                console.print(f"  [{NORD_YELLOW}]{file}[/{NORD_YELLOW}]")
                
        # Display untracked files
        if status.get('untracked_files'):
            console.print(f"[{NORD_RED}]Arquivos não rastreados:[/{NORD_RED}]")
            for file in status.get('untracked_files', []):
                console.print(f"  [{NORD_RED}]{file}[/{NORD_RED}]")
        
        # Ask what to do
        action_choices = ["commit", "push", "pull", "status"]
        action = Prompt.ask("[bold]Ação", choices=action_choices, default="status")
        
        if action == "commit":
            # Get files to add
            files_to_add = Prompt.ask("[bold]Arquivos para adicionar (separados por espaço, ou '.' para todos)")
            
            # Get commit message
            commit_message = Prompt.ask("[bold]Mensagem do commit")
            
            # Add files
            if files_to_add == ".":
                success = manager.add_all()
            else:
                file_list = files_to_add.split()
                success = manager.add_files(file_list)
            
            if not success:
                console.print(f"[{NORD_RED}]Falha ao adicionar arquivos[/{NORD_RED}]")
                return
            
            # Commit changes
            if manager.commit(commit_message):
                console.print(f"[{NORD_GREEN}]Alterações commitadas com sucesso![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Falha ao commitar alterações[/{NORD_RED}]")
        
        elif action == "push":
            # Get branch name
            branch = Prompt.ask("[bold]Nome da branch", default="main")
            
            # Push changes
            if manager.push(branch):
                console.print(f"[{NORD_GREEN}]Alterações enviadas com sucesso![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Falha ao enviar alterações[/{NORD_RED}]")
        
        elif action == "pull":
            # Get branch name
            branch = Prompt.ask("[bold]Nome da branch", default="main")
            
            # Pull changes
            if manager.pull(branch):
                console.print(f"[{NORD_GREEN}]Alterações baixadas com sucesso![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Falha ao baixar alterações[/{NORD_RED}]")
        
        elif action == "status":
            # Already displayed status above
            pass
        
    except Exception as e:
        handle_error("Erro ao atualizar GitHub", e)



@app.command()
def main():
    """Main CLI interface"""
    try:
        # Display welcome screen with ASCII art
        show_welcome()
        
        while True:
            # Display menu with system status
            display_menu()
            
            # Get user choice
            choice = Prompt.ask("[bold]Escolha uma opção", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"], default="0")
            
            if choice == "0":
                console.print(f"[{NORD_GREEN}]Saindo... Até logo![/{NORD_GREEN}]")
                break
            elif choice == "1":
                convert_videos()
            elif choice == "2":
                transcribe_audio()
            elif choice == "3":
                process_with_ai()
            elif choice == "4":
                generate_timestamps()
            elif choice == "5":
                create_tts_audio()
            elif choice == "6":
                generate_xml()
            elif choice == "7":
                upload_to_drive()
            elif choice == "8":
                update_github()
            elif choice == "9":
                process_complete_course()
            elif choice == "10":
                configure_settings()
            elif choice == "11":
                if HAS_MAINTENANCE:
                    maintenance.main()
                else:
                    console.print(f"[{NORD_RED}]Sistema de manutenção não disponível[/{NORD_RED}]")
            elif choice == "12":
                # Run prompt manager
                if HAS_PROMPT_MANAGER:
                    prompt_manager.main()
                else:
                    console.print(f"[{NORD_RED}]Gerenciador de prompts não disponível[/{NORD_RED}]")
            
            # Add a separator between operations
            console.print("\n" + "─" * console.width + "\n")
    
    except KeyboardInterrupt:
        console.print(f"\n[{NORD_YELLOW}]Operação interrompida pelo usuário[/{NORD_YELLOW}]")
    except Exception as e:
        handle_error("Erro na aplicação", e)

if __name__ == "__main__":
    app()