"""
Settings management functions for Curso Processor
"""

import os
import time
from typing import Dict, Any, Optional, Tuple, List, Union

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm

from config import settings, credentials
from utils.ui_components import (
    console, NORD_BLUE, NORD_CYAN, NORD_GREEN, NORD_YELLOW, NORD_RED, NORD_DIM,
    display_settings_status, display_api_credentials_menu, handle_error
)

def configure_settings():
    """Configure application settings"""
    try:
        console.print(f"[{NORD_CYAN}]Configurações[/{NORD_CYAN}]")
        
        # Display current settings status
        display_settings_status()
        
        # Create settings panel
        settings_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] 📁 Gerenciar Diretórios",
                    f"[{NORD_BLUE}][2][/{NORD_BLUE}] 🗣️ Configurar Idioma/Voz",
                    f"[{NORD_BLUE}][3][/{NORD_BLUE}] 🔑 Gerenciar APIs",
                    f"[{NORD_BLUE}][4][/{NORD_BLUE}] ⚙️ Configurações Avançadas",
                    f"[{NORD_BLUE}][5][/{NORD_BLUE}] 🔄 Restaurar Padrões",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
                ])
            ),
            title="[bold]Configurações[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(settings_panel)
        
        # Get user choice
        choice = Prompt.ask("[bold]Escolha uma opção", choices=["1", "2", "3", "4", "5", "0"], default="0")
        
        if choice == "1":
            # Manage directories
            manage_directories()
        
        elif choice == "2":
            # Configure language and TTS
            configure_language_tts()
        
        elif choice == "3":
            # Manage API credentials
            manage_api_credentials()
        
        elif choice == "4":
            # Advanced settings
            configure_advanced_settings()
        
        elif choice == "5":
            # Reset to defaults
            if Confirm.ask("[bold]Tem certeza que deseja restaurar todas as configurações para os valores padrão?", default=False):
                settings.reset_to_defaults()
                console.print(f"[{NORD_GREEN}]Configurações restauradas para os valores padrão![/{NORD_GREEN}]")
        
        # Return to settings menu
        if choice != "0":
            time.sleep(1)
            return configure_settings()
    
    except Exception as e:
        handle_error("Erro ao configurar", e)

def manage_directories():
    """Manage directory settings"""
    try:
        console.print(f"[{NORD_CYAN}]Gerenciando Diretórios[/{NORD_CYAN}]")
        
        # Get current directory settings
        current_settings = settings.get_settings()
        directories = current_settings["directories"]
        
        # Create directory panel
        directory_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] Diretório de Trabalho: {directories['work_directory']}",
                    f"[{NORD_BLUE}][2][/{NORD_BLUE}] Diretório GitHub: {directories['github_local']}",
                    f"[{NORD_BLUE}][3][/{NORD_BLUE}] Diretório XML: {directories['xml_output']}",
                    f"[{NORD_BLUE}][4][/{NORD_BLUE}] Diretório de Vídeos: {directories['video_input']}",
                    f"[{NORD_BLUE}][5][/{NORD_BLUE}] Diretório de Áudios: {directories['audio_output']}",
                    f"[{NORD_BLUE}][6][/{NORD_BLUE}] Diretório de Transcrições: {directories['transcription_output']}",
                    f"[{NORD_BLUE}][7][/{NORD_BLUE}] Diretório de Processados: {directories['processed_output']}",
                    f"[{NORD_BLUE}][8][/{NORD_BLUE}] Diretório de TTS: {directories['tts_output']}",
                    f"[{NORD_BLUE}][9][/{NORD_BLUE}] Diretório de Timestamps: {directories['timestamps_output']}",
                    f"[{NORD_BLUE}][10][/{NORD_BLUE}] Diretório de Cache: {directories['audio_cache']}",
                    f"[{NORD_BLUE}][11][/{NORD_BLUE}] Verificar e Criar Diretórios",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
                ])
            ),
            title="[bold]Diretórios[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(directory_panel)
        
        # Get user choice
        choice = Prompt.ask("[bold]Escolha uma opção", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "0"], default="0")
        
        if choice == "0":
            return
        
        if choice == "11":
            # Verify and create directories
            results = settings.create_missing_directories()
            
            # Display results
            console.print(f"[{NORD_CYAN}]Resultados da verificação de diretórios:[/{NORD_CYAN}]")
            
            table = Table(show_header=True, header_style=NORD_BLUE)
            table.add_column("Diretório")
            table.add_column("Status")
            
            for name, status in results.items():
                table.add_row(
                    name,
                    f"[{NORD_GREEN}]✓ OK[/{NORD_GREEN}]" if status else f"[{NORD_RED}]❌ Falha[/{NORD_RED}]"
                )
            
            console.print(table)
        else:
            # Map choice to directory key
            dir_keys = [
                "work_directory", "github_local", "xml_output", "video_input", 
                "audio_output", "transcription_output", "processed_output", 
                "tts_output", "timestamps_output", "audio_cache"
            ]
            
            dir_key = dir_keys[int(choice) - 1]
            
            # Get new directory path
            new_path = Prompt.ask(f"[bold]Novo caminho para {dir_key}", default=directories[dir_key])
            
            # Update directory setting
            if settings.update_directory_settings(dir_key, new_path):
                console.print(f"[{NORD_GREEN}]Diretório {dir_key} atualizado com sucesso![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao atualizar diretório {dir_key}[/{NORD_RED}]")
        
        # Return to directory management
        time.sleep(1)
        return manage_directories()
    
    except Exception as e:
        handle_error("Erro ao gerenciar diretórios", e)

def configure_language_tts():
    """Configure language and TTS settings"""
    try:
        console.print(f"[{NORD_CYAN}]Configurando Idioma e Voz[/{NORD_CYAN}]")
        
        # Get current language settings
        current_settings = settings.get_settings()
        language_settings = current_settings["language"]
        tts_settings = current_settings["tts"]
        
        # Create language panel
        language_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] Idioma da Interface: {language_settings['interface']}",
                    f"[{NORD_BLUE}][2][/{NORD_BLUE}] Idioma TTS: {language_settings['tts_language']}",
                    f"[{NORD_BLUE}][3][/{NORD_BLUE}] Voz TTS: {language_settings['tts_voice']}",
                    f"[{NORD_BLUE}][4][/{NORD_BLUE}] Taxa de Fala: {tts_settings['rate']}",
                    f"[{NORD_BLUE}][5][/{NORD_BLUE}] Volume: {tts_settings['volume']}",
                    f"[{NORD_BLUE}][6][/{NORD_BLUE}] Pitch: {tts_settings['pitch']}",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
                ])
            ),
            title="[bold]Idioma e Voz[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(language_panel)
        
        # Get user choice
        choice = Prompt.ask("[bold]Escolha uma opção", choices=["1", "2", "3", "4", "5", "6", "0"], default="0")
        
        if choice == "0":
            return
        
        if choice == "1":
            # Update interface language
            new_language = Prompt.ask("[bold]Novo idioma da interface", default=language_settings["interface"])
            settings.update_language_settings(interface=new_language)
            console.print(f"[{NORD_GREEN}]Idioma da interface atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "2":
            # Update TTS language
            new_language = Prompt.ask("[bold]Novo idioma TTS", default=language_settings["tts_language"])
            settings.update_language_settings(tts_language=new_language)
            console.print(f"[{NORD_GREEN}]Idioma TTS atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "3":
            # Update TTS voice
            new_voice = Prompt.ask("[bold]Nova voz TTS", default=language_settings["tts_voice"])
            settings.update_language_settings(tts_voice=new_voice)
            console.print(f"[{NORD_GREEN}]Voz TTS atualizada com sucesso![/{NORD_GREEN}]")
        
        elif choice == "4":
            # Update speech rate
            new_rate = Prompt.ask("[bold]Nova taxa de fala", default=str(tts_settings["rate"]))
            settings.update_tts_settings(rate=int(new_rate))
            console.print(f"[{NORD_GREEN}]Taxa de fala atualizada com sucesso![/{NORD_GREEN}]")
        
        elif choice == "5":
            # Update volume
            new_volume = Prompt.ask("[bold]Novo volume", default=str(tts_settings["volume"]))
            settings.update_tts_settings(volume=float(new_volume))
            console.print(f"[{NORD_GREEN}]Volume atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "6":
            # Update pitch
            new_pitch = Prompt.ask("[bold]Novo pitch", default=str(tts_settings["pitch"]))
            settings.update_tts_settings(pitch=int(new_pitch))
            console.print(f"[{NORD_GREEN}]Pitch atualizado com sucesso![/{NORD_GREEN}]")
        
        # Return to language configuration
        time.sleep(1)
        return configure_language_tts()
    
    except Exception as e:
        handle_error("Erro ao configurar idioma e voz", e)

def manage_api_credentials():
    """Manage API credentials"""
    try:
        console.print(f"[{NORD_CYAN}]Gerenciando APIs[/{NORD_CYAN}]")
        
        # Display API credentials menu
        display_api_credentials_menu()
        
        # Get user choice
        choice = Prompt.ask("[bold]Escolha uma opção", choices=["1", "2", "3", "4", "0"], default="0")
        
        if choice == "0":
            return
        
        if choice == "1":
            # Add new API
            add_api_credentials()
        
        elif choice == "2":
            # Test existing APIs
            test_api_credentials()
        
        elif choice == "3":
            # Remove API
            remove_api_credentials()
        
        elif choice == "4":
            # View usage/limits
            view_api_usage()
        
        # Return to API management
        time.sleep(1)
        return manage_api_credentials()
    
    except Exception as e:
        handle_error("Erro ao gerenciar APIs", e)

def add_api_credentials():
    """Add new API credentials"""
    try:
        console.print(f"[{NORD_CYAN}]Adicionando Nova API[/{NORD_CYAN}]")
        
        # Create API selection panel
        api_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] OpenAI API (Whisper/ChatGPT)",
                    f"[{NORD_BLUE}][2][/{NORD_BLUE}] Anthropic API (Claude)",
                    f"[{NORD_BLUE}][3][/{NORD_BLUE}] Google Drive API",
                    f"[{NORD_BLUE}][4][/{NORD_BLUE}] GitHub API",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
                ])
            ),
            title="[bold]Selecione a API[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(api_panel)
        
        # Get user choice
        api_choice = Prompt.ask("[bold]Escolha uma API", choices=["1", "2", "3", "4", "0"], default="0")
        
        if api_choice == "0":
            return
        
        if api_choice == "1":
            # OpenAI API
            api_key = Prompt.ask("[bold]OpenAI API Key", password=True)
            organization = Prompt.ask("[bold]OpenAI Organization ID (opcional)", default="")
            
            if credentials.set_openai_api_key(api_key):
                if organization:
                    credentials.set_openai_organization(organization)
                
                # Test the API
                success, message = credentials.test_credentials("openai")
                
                if success:
                    console.print(f"[{NORD_GREEN}]Credencial da OpenAI API configurada e testada com sucesso: {message}[/{NORD_GREEN}]")
                else:
                    console.print(f"[{NORD_YELLOW}]Credencial da OpenAI API configurada, mas o teste falhou: {message}[/{NORD_YELLOW}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao configurar credencial da OpenAI API[/{NORD_RED}]")
        
        elif api_choice == "2":
            # Anthropic API
            api_key = Prompt.ask("[bold]Anthropic API Key", password=True)
            
            if credentials.set_anthropic_api_key(api_key):
                # Test the API
                success, message = credentials.test_credentials("anthropic")
                
                if success:
                    console.print(f"[{NORD_GREEN}]Credencial da Anthropic API configurada e testada com sucesso: {message}[/{NORD_GREEN}]")
                else:
                    console.print(f"[{NORD_YELLOW}]Credencial da Anthropic API configurada, mas o teste falhou: {message}[/{NORD_YELLOW}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao configurar credencial da Anthropic API[/{NORD_RED}]")
        
        elif api_choice == "3":
            # Google Drive API
            console.print(f"[{NORD_CYAN}]Para configurar a Google Drive API:[/{NORD_CYAN}]")
            console.print("1. Acesse o Google Cloud Console e crie um projeto")
            console.print("2. Ative a Google Drive API")
            console.print("3. Crie credenciais OAuth 2.0")
            console.print("4. Configure o fluxo de autenticação")
            
            client_id = Prompt.ask("[bold]Client ID", password=True)
            client_secret = Prompt.ask("[bold]Client Secret", password=True)
            refresh_token = Prompt.ask("[bold]Refresh Token (opcional)", password=True, default="")
            
            if credentials.set_google_credentials(client_id=client_id, client_secret=client_secret):
                if refresh_token:
                    credentials.set_google_credentials(refresh_token=refresh_token)
                
                console.print(f"[{NORD_GREEN}]Credenciais do Google Drive configuradas com sucesso![/{NORD_GREEN}]")
                
                # Test the API if refresh token is provided
                if refresh_token:
                    success, message = credentials.test_credentials("google")
                    
                    if success:
                        console.print(f"[{NORD_GREEN}]Credenciais do Google Drive testadas com sucesso: {message}[/{NORD_GREEN}]")
                    else:
                        console.print(f"[{NORD_YELLOW}]Credenciais do Google Drive configuradas, mas o teste falhou: {message}[/{NORD_YELLOW}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao configurar credenciais do Google Drive[/{NORD_RED}]")
        
        elif api_choice == "4":
            # GitHub API
            username = Prompt.ask("[bold]Nome de usuário do GitHub")
            token = Prompt.ask("[bold]GitHub Personal Access Token", password=True)
            
            if credentials.set_github_credentials(username=username, token=token):
                # Test the API
                success, message = credentials.test_credentials("github")
                
                if success:
                    console.print(f"[{NORD_GREEN}]Credenciais do GitHub configuradas e testadas com sucesso: {message}[/{NORD_GREEN}]")
                else:
                    console.print(f"[{NORD_YELLOW}]Credenciais do GitHub configuradas, mas o teste falhou: {message}[/{NORD_YELLOW}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao configurar credenciais do GitHub[/{NORD_RED}]")
    
    except Exception as e:
        handle_error("Erro ao adicionar API", e)

def test_api_credentials():
    """Test existing API credentials"""
    try:
        console.print(f"[{NORD_CYAN}]Testando APIs Existentes[/{NORD_CYAN}]")
        
        # Get API status
        api_status = credentials.get_service_status()
        
        # Filter configured APIs
        configured_apis = [api for api in api_status if api["configured"]]
        
        if not configured_apis:
            console.print(f"[{NORD_YELLOW}]Nenhuma API configurada para testar.[/{NORD_YELLOW}]")
            return
        
        # Create API selection panel
        api_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][{i+1}][/{NORD_BLUE}] {api['name'].capitalize()}"
                    for i, api in enumerate(configured_apis)
                ] + [f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"])
            ),
            title="[bold]Selecione a API para testar[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(api_panel)
        
        # Get user choice
        choices = [str(i+1) for i in range(len(configured_apis))] + ["0"]
        api_choice = Prompt.ask("[bold]Escolha uma API", choices=choices, default="0")
        
        if api_choice == "0":
            return
        
        # Test selected API
        selected_api = configured_apis[int(api_choice) - 1]
        
        with Progress(
            TextColumn(f"[{NORD_BLUE}]{{task.description}}[/{NORD_BLUE}]"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Testando {selected_api['name'].capitalize()}...[/{NORD_CYAN}]", total=1)
            
            # Test API
            success, message = credentials.test_credentials(selected_api["name"])
            
            progress.update(task, advance=1)
        
        if success:
            console.print(f"[{NORD_GREEN}]Teste bem-sucedido: {message}[/{NORD_GREEN}]")
        else:
            console.print(f"[{NORD_RED}]Teste falhou: {message}[/{NORD_RED}]")
    
    except Exception as e:
        handle_error("Erro ao testar APIs", e)

def remove_api_credentials():
    """Remove API credentials"""
    try:
        console.print(f"[{NORD_CYAN}]Removendo API[/{NORD_CYAN}]")
        
        # Get API status
        api_status = credentials.get_service_status()
        
        # Filter configured APIs
        configured_apis = [api for api in api_status if api["configured"]]
        
        if not configured_apis:
            console.print(f"[{NORD_YELLOW}]Nenhuma API configurada para remover.[/{NORD_YELLOW}]")
            return
        
        # Create API selection panel
        api_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][{i+1}][/{NORD_BLUE}] {api['name'].capitalize()}"
                    for i, api in enumerate(configured_apis)
                ] + [f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"])
            ),
            title="[bold]Selecione a API para remover[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(api_panel)
        
        # Get user choice
        choices = [str(i+1) for i in range(len(configured_apis))] + ["0"]
        api_choice = Prompt.ask("[bold]Escolha uma API", choices=choices, default="0")
        
        if api_choice == "0":
            return
        
        # Remove selected API
        selected_api = configured_apis[int(api_choice) - 1]
        
        # Ask for confirmation
        if Confirm.ask(f"[bold]Tem certeza que deseja remover as credenciais da API {selected_api['name'].capitalize()}?", default=False):
            if credentials.delete_credential(selected_api["name"]):
                console.print(f"[{NORD_GREEN}]Credenciais da API {selected_api['name'].capitalize()} removidas com sucesso![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao remover credenciais da API {selected_api['name'].capitalize()}[/{NORD_RED}]")
    
    except Exception as e:
        handle_error("Erro ao remover API", e)

def view_api_usage():
    """View API usage statistics"""
    try:
        console.print(f"[{NORD_CYAN}]Visualizando Uso/Limites de APIs[/{NORD_CYAN}]")
        
        # Get API status
        api_status = credentials.get_service_status()
        
        # Filter configured APIs
        configured_apis = [api for api in api_status if api["configured"]]
        
        if not configured_apis:
            console.print(f"[{NORD_YELLOW}]Nenhuma API configurada para visualizar uso.[/{NORD_YELLOW}]")
            return
        
        # Create API selection panel
        api_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][{i+1}][/{NORD_BLUE}] {api['name'].capitalize()}"
                    for i, api in enumerate(configured_apis)
                ] + [f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"])
            ),
            title="[bold]Selecione a API para visualizar uso[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(api_panel)
        
        # Get user choice
        choices = [str(i+1) for i in range(len(configured_apis))] + ["0"]
        api_choice = Prompt.ask("[bold]Escolha uma API", choices=choices, default="0")
        
        if api_choice == "0":
            return
        
        # View usage for selected API
        selected_api = configured_apis[int(api_choice) - 1]
        
        # Get usage statistics
        usage_stats = credentials.get_usage_stats(selected_api["name"])
        
        if not usage_stats:
            console.print(f"[{NORD_YELLOW}]Nenhuma estatística de uso disponível para {selected_api['name'].capitalize()}.[/{NORD_YELLOW}]")
            return
        
        # Display usage statistics
        usage_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_CYAN}]Estatísticas de Uso - {selected_api['name'].capitalize()}[/{NORD_CYAN}]",
                    f"[{NORD_DIM}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_DIM}]",
                    "",
                    f"Total de tokens: {usage_stats.get('total_tokens', 0)}",
                    f"Último reset: {usage_stats.get('last_reset', 'Nunca')}",
                    "",
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] Resetar estatísticas",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
                ])
            ),
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(usage_panel)
        
        # Get user choice
        reset_choice = Prompt.ask("[bold]Escolha uma opção", choices=["1", "0"], default="0")
        
        if reset_choice == "1":
            # Reset usage statistics
            if Confirm.ask(f"[bold]Tem certeza que deseja resetar as estatísticas de uso da API {selected_api['name'].capitalize()}?", default=False):
                if credentials.reset_usage_stats(selected_api["name"]):
                    console.print(f"[{NORD_GREEN}]Estatísticas de uso da API {selected_api['name'].capitalize()} resetadas com sucesso![/{NORD_GREEN}]")
                else:
                    console.print(f"[{NORD_RED}]Erro ao resetar estatísticas de uso da API {selected_api['name'].capitalize()}[/{NORD_RED}]")
    
    except Exception as e:
        handle_error("Erro ao visualizar uso de APIs", e)

def configure_advanced_settings():
    """Configure advanced settings"""
    try:
        console.print(f"[{NORD_CYAN}]Configurações Avançadas[/{NORD_CYAN}]")
        
        # Get current settings
        current_settings = settings.get_settings()
        processing_settings = current_settings["processing"]
        xml_settings = current_settings["xml"]
        
        # Create advanced settings panel
        advanced_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] Qualidade de Áudio: {processing_settings['audio_quality']} kbps",
                    f"[{NORD_BLUE}][2][/{NORD_BLUE}] Máximo de Tokens por Requisição: {processing_settings['max_tokens_per_request']}",
                    f"[{NORD_BLUE}][3][/{NORD_BLUE}] Tamanho do Lote: {processing_settings['batch_size']}",
                    f"[{NORD_BLUE}][4][/{NORD_BLUE}] Auto-limpeza: {'Ativada' if processing_settings['auto_cleanup'] else 'Desativada'}",
                    f"[{NORD_BLUE}][5][/{NORD_BLUE}] Nome do Feed XML: {xml_settings['feed_name']}",
                    f"[{NORD_BLUE}][6][/{NORD_BLUE}] Título do Feed XML: {xml_settings['feed_title']}",
                    f"[{NORD_BLUE}][7][/{NORD_BLUE}] Descrição do Feed XML: {xml_settings['feed_description']}",
                    f"[{NORD_BLUE}][8][/{NORD_BLUE}] Exportar Configurações",
                    f"[{NORD_BLUE}][9][/{NORD_BLUE}] Importar Configurações",
                    f"[{NORD_BLUE}][10][/{NORD_BLUE}] Listar Backups",
                    f"[{NORD_BLUE}][11][/{NORD_BLUE}] Restaurar de Backup",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
                ])
            ),
            title="[bold]Configurações Avançadas[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        console.print(advanced_panel)
        
        # Get user choice
        choice = Prompt.ask("[bold]Escolha uma opção", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "0"], default="0")
        
        if choice == "0":
            return
        
        if choice == "1":
            # Update audio quality
            new_quality = Prompt.ask("[bold]Nova qualidade de áudio (kbps)", default=str(processing_settings["audio_quality"]))
            settings.update_processing_settings(audio_quality=int(new_quality))
            console.print(f"[{NORD_GREEN}]Qualidade de áudio atualizada com sucesso![/{NORD_GREEN}]")
        
        elif choice == "2":
            # Update max tokens per request
            new_max_tokens = Prompt.ask("[bold]Novo máximo de tokens por requisição", default=str(processing_settings["max_tokens_per_request"]))
            settings.update_processing_settings(max_tokens_per_request=int(new_max_tokens))
            console.print(f"[{NORD_GREEN}]Máximo de tokens por requisição atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "3":
            # Update batch size
            new_batch_size = Prompt.ask("[bold]Novo tamanho do lote", default=str(processing_settings["batch_size"]))
            settings.update_processing_settings(batch_size=int(new_batch_size))
            console.print(f"[{NORD_GREEN}]Tamanho do lote atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "4":
            # Update auto cleanup
            new_auto_cleanup = Confirm.ask("[bold]Ativar auto-limpeza?", default=processing_settings["auto_cleanup"])
            settings.update_processing_settings(auto_cleanup=new_auto_cleanup)
            console.print(f"[{NORD_GREEN}]Auto-limpeza {'ativada' if new_auto_cleanup else 'desativada'} com sucesso![/{NORD_GREEN}]")
        
        elif choice == "5":
            # Update XML feed name
            new_feed_name = Prompt.ask("[bold]Novo nome do feed XML", default=xml_settings["feed_name"])
            settings.update_xml_settings(feed_name=new_feed_name)
            console.print(f"[{NORD_GREEN}]Nome do feed XML atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "6":
            # Update XML feed title
            new_feed_title = Prompt.ask("[bold]Novo título do feed XML", default=xml_settings["feed_title"])
            settings.update_xml_settings(feed_title=new_feed_title)
            console.print(f"[{NORD_GREEN}]Título do feed XML atualizado com sucesso![/{NORD_GREEN}]")
        
        elif choice == "7":
            # Update XML feed description
            new_feed_description = Prompt.ask("[bold]Nova descrição do feed XML", default=xml_settings["feed_description"])
            settings.update_xml_settings(feed_description=new_feed_description)
            console.print(f"[{NORD_GREEN}]Descrição do feed XML atualizada com sucesso![/{NORD_GREEN}]")
        
        elif choice == "8":
            # Export settings
            export_path = Prompt.ask("[bold]Caminho para exportar configurações", default=os.path.join(os.getcwd(), "curso_processor_settings.json"))
            
            if settings.export_settings(export_path):
                console.print(f"[{NORD_GREEN}]Configurações exportadas com sucesso para {export_path}![/{NORD_GREEN}]")
            else:
                console.print(f"[{NORD_RED}]Erro ao exportar configurações[/{NORD_RED}]")
        
        elif choice == "9":
            # Import settings
            import_path = Prompt.ask("[bold]Caminho para importar configurações")
            
            if os.path.exists(import_path):
                if settings.import_settings(import_path):
                    console.print(f"[{NORD_GREEN}]Configurações importadas com sucesso de {import_path}![/{NORD_GREEN}]")
                else:
                    console.print(f"[{NORD_RED}]Erro ao importar configurações[/{NORD_RED}]")
            else:
                console.print(f"[{NORD_RED}]Arquivo não encontrado: {import_path}[/{NORD_RED}]")
        
        elif choice == "10":
            # List backups
            backups = settings.list_backups()
            
            if not backups:
                console.print(f"[{NORD_YELLOW}]Nenhum backup encontrado.[/{NORD_YELLOW}]")
            else:
                console.print(f"[{NORD_CYAN}]Backups disponíveis:[/{NORD_CYAN}]")
                
                table = Table(show_header=True, header_style=NORD_BLUE)
                table.add_column("Data")
                table.add_column("Arquivo")
                table.add_column("Tamanho")
                
                for backup in backups:
                    table.add_row(
                        backup["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                        os.path.basename(backup["file"]),
                        f"{backup['size'] / 1024:.1f} KB"
                    )
                
                console.print(table)
        
        elif choice == "11":
            # Restore from backup
            backups = settings.list_backups()
            
            if not backups:
                console.print(f"[{NORD_YELLOW}]Nenhum backup encontrado.[/{NORD_YELLOW}]")
            else:
                console.print(f"[{NORD_CYAN}]Backups disponíveis:[/{NORD_CYAN}]")
                
                for i, backup in enumerate(backups):
                    console.print(f"[{NORD_BLUE}][{i+1}][/{NORD_BLUE}] {backup['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {os.path.basename(backup['file'])}")
                
                # Get user choice
                backup_choices = [str(i+1) for i in range(len(backups))] + ["0"]
                backup_choice = Prompt.ask("[bold]Escolha um backup para restaurar (0 para cancelar)", choices=backup_choices, default="0")
                
                if backup_choice != "0":
                    selected_backup = backups[int(backup_choice) - 1]
                    
                    if Confirm.ask(f"[bold]Tem certeza que deseja restaurar o backup de {selected_backup['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}?", default=False):
                        if settings.restore_from_backup(selected_backup["file"]):
                            console.print(f"[{NORD_GREEN}]Configurações restauradas com sucesso do backup de {selected_backup['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}![/{NORD_GREEN}]")
                        else:
                            console.print(f"[{NORD_RED}]Erro ao restaurar configurações do backup[/{NORD_RED}]")
        
        # Return to advanced settings
        time.sleep(1)
        return configure_advanced_settings()
    
    except Exception as e:
        handle_error("Erro ao configurar avançadas", e)