"""
Enhanced course processing functionality for Curso Processor
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.prompt import Prompt, Confirm

# Import modules
from config import settings
from utils import file_manager
from utils.ui_components import (
    console, NORD_BLUE, NORD_CYAN, NORD_GREEN, NORD_YELLOW, NORD_RED, NORD_DIM,
    create_progress_bar, handle_error
)

def process_complete_course():
    """Process a complete course from start to finish with robust error handling and progress tracking"""
    try:
        console.print(f"[{NORD_CYAN}]Iniciando processamento completo de curso...[/{NORD_CYAN}]")
        
        # Get course name
        course_name = Prompt.ask("[bold]Nome do curso")
        
        # Create course directory structure
        course_dir = os.path.join(settings.get_default_base_dir(), course_name)
        
        # Create progress tracker
        from utils.progress_tracker import CourseProgressTracker
        tracker = CourseProgressTracker(course_name, course_dir)
        
        # Create file manager
        from utils.file_manager import CourseFileManager
        course_manager = CourseFileManager(
            course_name=course_name,
            base_dir=settings.get_default_base_dir(),
            console=console
        )
        
        # Check if course was previously processed
        if tracker.is_course_complete():
            if Confirm.ask(f"[bold]O curso '{course_name}' já foi processado anteriormente. Deseja reiniciar o processamento?"):
                tracker.reset_progress()
                console.print(f"[{NORD_YELLOW}]Progresso anterior resetado. Iniciando novo processamento.[/{NORD_YELLOW}]")
            else:
                # Ask which steps to reprocess
                steps_to_reprocess = []
                for step in tracker.get_completed_steps():
                    if Confirm.ask(f"[bold]Reprocessar etapa: {step}?"):
                        steps_to_reprocess.append(step)
                
                if steps_to_reprocess:
                    tracker.reset_steps(steps_to_reprocess)
                    console.print(f"[{NORD_YELLOW}]Etapas selecionadas serão reprocessadas.[/{NORD_YELLOW}]")
                else:
                    console.print(f"[{NORD_YELLOW}]Nenhuma etapa selecionada para reprocessamento. Operação cancelada.[/{NORD_YELLOW}]")
                    return
        
        # Create course structure if needed
        if not os.path.exists(course_dir):
            if course_manager.create_course_structure():
                console.print(f"[{NORD_GREEN}]Estrutura do curso criada com sucesso![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Falha ao criar estrutura do curso[/{NORD_RED}]")
                return
        
        # Ask for video directory if not already processed
        if not tracker.is_step_complete("audio_converted"):
            video_dir = Prompt.ask("[bold]Diretório com vídeos do curso")
            
            if not os.path.exists(video_dir):
                console.print(f"[{NORD_RED}]Diretório de vídeos não encontrado: {video_dir}[/{NORD_RED}]")
                return
            
            # Get video files
            video_files = file_manager.get_files_by_extensions(video_dir, ["mp4", "mkv", "avi", "mov"])
            
            if not video_files:
                console.print(f"[{NORD_YELLOW}]Nenhum arquivo de vídeo encontrado em {video_dir}[/{NORD_YELLOW}]")
                return
            
            # Display files to be processed
            console.print(f"[{NORD_GREEN}]Encontrados {len(video_files)} arquivos de vídeo[/{NORD_GREEN}]")
            
            # Ask for confirmation
            if not Confirm.ask("[bold]Deseja processar todos os arquivos?"):
                console.print(f"[{NORD_YELLOW}]Operação cancelada pelo usuário[/{NORD_YELLOW}]")
                return
            
            # Update tracker with total files
            tracker.update_metadata("total_files", len(video_files))
        else:
            console.print(f"[{NORD_GREEN}]Etapa de conversão de áudio já concluída. Pulando...[/{NORD_GREEN}]")
        
        # STEP 1: Convert videos to audio
        if not tracker.is_step_complete("audio_converted"):
            console.print(f"[{NORD_CYAN}]Etapa 1: Convertendo vídeos para áudio...[/{NORD_CYAN}]")
            
            # Import audio converter
            from modules.audio_converter import AudioConverter
            
            # Create audio converter
            converter = AudioConverter(console=console)
            
            # Convert videos to audio
            audio_files = []
            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Convertendo vídeos...", total=len(video_files))
                
                for video_file in video_files:
                    # Get output path
                    output_path = os.path.join(course_dir, "audio", os.path.basename(video_file).replace(".mp4", ".mp3"))
                    
                    # Convert video to audio
                    result = converter.convert_video_to_audio(video_file, output_path)
                    
                    if result:
                        audio_files.append(output_path)
                        # Add file to tracker
                        tracker.add_file("audio_files", output_path)
                    
                    # Update progress
                    progress.update(task, advance=1)
            
            if not audio_files:
                console.print(f"[{NORD_RED}]Falha ao converter vídeos para áudio[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("audio_converted")
            console.print(f"[{NORD_GREEN}]Conversão de vídeos concluída com sucesso![/{NORD_GREEN}]")
        else:
            # Get audio files from tracker
            audio_files = tracker.get_files("audio_files")
            console.print(f"[{NORD_GREEN}]Usando {len(audio_files)} arquivos de áudio já convertidos.[/{NORD_GREEN}]")
        
        # STEP 2: Transcribe audio
        if not tracker.is_step_complete("transcribed"):
            console.print(f"[{NORD_CYAN}]Etapa 2: Transcrevendo áudios...[/{NORD_CYAN}]")
            
            # Import transcription module
            from modules.transcription import Transcriber
            
            # Create transcriber
            transcriber = Transcriber(console=console)
            
            # Transcribe audio files
            transcription_files = []
            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Transcrevendo áudios...", total=len(audio_files))
                
                for audio_file in audio_files:
                    # Get output path
                    output_path = os.path.join(course_dir, "transcriptions", os.path.basename(audio_file).replace(".mp3", ".txt"))
                    
                    # Transcribe audio
                    result = transcriber.transcribe_audio(audio_file, output_path)
                    
                    if result:
                        transcription_files.append(output_path)
                        # Add file to tracker
                        tracker.add_file("transcriptions", output_path)
                    
                    # Update progress
                    progress.update(task, advance=1)
            
            if not transcription_files:
                console.print(f"[{NORD_RED}]Falha ao transcrever áudios[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("transcribed")
            console.print(f"[{NORD_GREEN}]Transcrição de áudios concluída com sucesso![/{NORD_GREEN}]")
        else:
            # Get transcription files from tracker
            transcription_files = tracker.get_files("transcriptions")
            console.print(f"[{NORD_GREEN}]Usando {len(transcription_files)} transcrições já existentes.[/{NORD_GREEN}]")
        
        # STEP 3: Process with AI
        if not tracker.is_step_complete("ai_processed"):
            console.print(f"[{NORD_CYAN}]Etapa 3: Processando com IA...[/{NORD_CYAN}]")
            
            # Import AI processor
            from modules.ai_processor import AIProcessor
            
            # Create AI processor
            ai_processor = AIProcessor(console=console)
            
            # Process transcriptions with AI
            processed_files = []
            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Processando com IA...", total=len(transcription_files))
                
                for transcription_file in transcription_files:
                    # Get output path
                    output_path = os.path.join(course_dir, "processed", os.path.basename(transcription_file))
                    
                    # Process transcription with AI
                    result = ai_processor.process_transcription(transcription_file, output_path)
                    
                    if result:
                        processed_files.append(output_path)
                        # Add file to tracker
                        tracker.add_file("processed_files", output_path)
                    
                    # Update progress
                    progress.update(task, advance=1)
            
            if not processed_files:
                console.print(f"[{NORD_RED}]Falha ao processar transcrições com IA[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("ai_processed")
            console.print(f"[{NORD_GREEN}]Processamento com IA concluído com sucesso![/{NORD_GREEN}]")
        else:
            # Get processed files from tracker
            processed_files = tracker.get_files("processed_files")
            console.print(f"[{NORD_GREEN}]Usando {len(processed_files)} arquivos já processados com IA.[/{NORD_GREEN}]")
        
        # STEP 4: Generate timestamps
        if not tracker.is_step_complete("timestamps_generated"):
            console.print(f"[{NORD_CYAN}]Etapa 4: Gerando timestamps...[/{NORD_CYAN}]")
            
            # Import timestamp generator
            from modules.timestamp_generator import TimestampGenerator
            
            # Create timestamp generator
            timestamp_generator = TimestampGenerator(console=console)
            
            # Generate timestamps
            timestamp_files = []
            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Gerando timestamps...", total=len(processed_files))
                
                for processed_file in processed_files:
                    # Get output path
                    output_path = os.path.join(course_dir, "timestamps", os.path.basename(processed_file))
                    
                    # Generate timestamps
                    result = timestamp_generator.generate_timestamps(processed_file, output_path)
                    
                    if result:
                        timestamp_files.append(output_path)
                        # Add file to tracker
                        tracker.add_file("timestamp_files", output_path)
                    
                    # Update progress
                    progress.update(task, advance=1)
            
            if not timestamp_files:
                console.print(f"[{NORD_RED}]Falha ao gerar timestamps[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("timestamps_generated")
            console.print(f"[{NORD_GREEN}]Geração de timestamps concluída com sucesso![/{NORD_GREEN}]")
        else:
            # Get timestamp files from tracker
            timestamp_files = tracker.get_files("timestamp_files")
            console.print(f"[{NORD_GREEN}]Usando {len(timestamp_files)} arquivos de timestamps já gerados.[/{NORD_GREEN}]")
        
        # STEP 5: Generate TTS audio
        if not tracker.is_step_complete("tts_created"):
            console.print(f"[{NORD_CYAN}]Etapa 5: Gerando áudio TTS...[/{NORD_CYAN}]")
            
            # Import TTS generator
            from modules.tts_generator import TTSGenerator
            
            # Create TTS generator
            tts_generator = TTSGenerator(console=console)
            
            # Generate TTS audio
            tts_files = []
            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Gerando áudio TTS...", total=len(processed_files))
                
                for processed_file in processed_files:
                    # Get output path
                    output_path = os.path.join(course_dir, "tts", os.path.basename(processed_file).replace(".txt", ".mp3"))
                    
                    # Generate TTS audio
                    result = tts_generator.generate_tts(processed_file, output_path)
                    
                    if result:
                        tts_files.append(output_path)
                        # Add file to tracker
                        tracker.add_file("tts_files", output_path)
                    
                    # Update progress
                    progress.update(task, advance=1)
            
            if not tts_files:
                console.print(f"[{NORD_RED}]Falha ao gerar áudio TTS[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("tts_created")
            console.print(f"[{NORD_GREEN}]Geração de áudio TTS concluída com sucesso![/{NORD_GREEN}]")
        else:
            # Get TTS files from tracker
            tts_files = tracker.get_files("tts_files")
            console.print(f"[{NORD_GREEN}]Usando {len(tts_files)} arquivos de áudio TTS já gerados.[/{NORD_GREEN}]")
        
        # STEP 6: Generate XML
        if not tracker.is_step_complete("xml_updated"):
            console.print(f"[{NORD_CYAN}]Etapa 6: Gerando XML...[/{NORD_CYAN}]")
            
            # Import XML generator
            from modules.xml_generator import XMLGenerator
            
            # Create XML generator
            xml_generator = XMLGenerator(console=console)
            
            # Generate XML
            xml_file = os.path.join(course_dir, "xml", f"{course_name}.xml")
            
            # Generate XML
            result = xml_generator.generate_xml(
                course_name=course_name,
                timestamp_files=timestamp_files,
                tts_files=tts_files,
                output_path=xml_file
            )
            
            if not result:
                console.print(f"[{NORD_RED}]Falha ao gerar XML[/{NORD_RED}]")
                return
            
            # Add file to tracker
            tracker.add_file("xml_files", xml_file)
            
            # Mark step as complete
            tracker.complete_step("xml_updated")
            console.print(f"[{NORD_GREEN}]Geração de XML concluída com sucesso![/{NORD_GREEN}]")
        else:
            # Get XML file from tracker
            xml_files = tracker.get_files("xml_files")
            xml_file = xml_files[0] if xml_files else os.path.join(course_dir, "xml", f"{course_name}.xml")
            console.print(f"[{NORD_GREEN}]Usando arquivo XML já gerado.[/{NORD_GREEN}]")
        
        # STEP 7: Upload to Google Drive
        if not tracker.is_step_complete("uploaded_to_drive"):
            console.print(f"[{NORD_CYAN}]Etapa 7: Enviando para o Google Drive...[/{NORD_CYAN}]")
            
            # Import Drive uploader
            from modules.drive_uploader import DriveUploader
            
            # Create Drive uploader
            drive_uploader = DriveUploader(console=console)
            
            # Upload to Google Drive
            result = drive_uploader.upload_course(
                course_name=course_name,
                course_dir=course_dir
            )
            
            if not result:
                console.print(f"[{NORD_RED}]Falha ao enviar para o Google Drive[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("uploaded_to_drive")
            console.print(f"[{NORD_GREEN}]Envio para o Google Drive concluído com sucesso![/{NORD_GREEN}]")
        else:
            console.print(f"[{NORD_GREEN}]Arquivos já enviados para o Google Drive.[/{NORD_GREEN}]")
        
        # STEP 8: Update GitHub
        if not tracker.is_step_complete("github_pushed"):
            console.print(f"[{NORD_CYAN}]Etapa 8: Atualizando GitHub...[/{NORD_CYAN}]")
            
            # Import GitHub manager
            from modules.github_manager import GitHubManager
            
            # Create GitHub manager
            github_manager = GitHubManager(console=console)
            
            # Update GitHub
            result = github_manager.update_repository(
                course_name=course_name,
                xml_file=xml_file
            )
            
            if not result:
                console.print(f"[{NORD_RED}]Falha ao atualizar GitHub[/{NORD_RED}]")
                return
            
            # Mark step as complete
            tracker.complete_step("github_pushed")
            console.print(f"[{NORD_GREEN}]Atualização do GitHub concluída com sucesso![/{NORD_GREEN}]")
        else:
            console.print(f"[{NORD_GREEN}]GitHub já atualizado.[/{NORD_GREEN}]")
        
        # Calculate and update course statistics
        tracker.update_course_statistics()
        
        # Display course summary
        tracker.display_course_summary()
        
        # Final message
        console.print(f"[{NORD_GREEN}]Processamento completo do curso finalizado com sucesso![/{NORD_GREEN}]")
        
    except KeyboardInterrupt:
        console.print(f"\n[{NORD_YELLOW}]Processamento interrompido pelo usuário. O progresso foi salvo e pode ser retomado posteriormente.[/{NORD_YELLOW}]")
    except Exception as e:
        handle_error("Erro ao processar curso completo", e)
        console.print(f"[{NORD_YELLOW}]O progresso foi salvo e pode ser retomado posteriormente.[/{NORD_YELLOW}]")