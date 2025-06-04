"""
UI components for Curso Processor using Rich
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
from rich.prompt import Prompt, Confirm
from rich.align import Align
from pyfiglet import Figlet

# Nord Theme colors
NORD_WHITE = "bright_white"
NORD_BLUE = "bright_blue"
NORD_CYAN = "bright_cyan"
NORD_GREEN = "bright_green"
NORD_YELLOW = "bright_yellow"
NORD_RED = "bright_red"
NORD_DIM = "dim white"

# Initialize console
console = Console()

def create_header(title: str):
    """
    Create a header panel with Nord Theme styling
    
    Args:
        title: Title text
    """
    return Panel(
        Text(title, style=NORD_WHITE),
        border_style=NORD_BLUE,
        title="Curso Processor",
        title_align="center"
    )

def create_progress_bar(description: str):
    """
    Create a Nord Theme styled progress bar
    
    Args:
        description: Progress bar description
        
    Returns:
        Progress: Rich progress bar
    """
    return Progress(
        TextColumn(f"[{NORD_BLUE}]{{task.description}}[/{NORD_BLUE}]"),
        BarColumn(complete_style=NORD_CYAN, finished_style=NORD_GREEN),
        TaskProgressColumn(),
        console=console
    )

def create_info_panel(title: str, content: str):
    """
    Create an information panel with Nord Theme styling
    
    Args:
        title: Panel title
        content: Panel content
    """
    return Panel(
        Text(content, style=NORD_WHITE),
        border_style=NORD_CYAN,
        title=title,
        title_align="center"
    )

def create_error_panel(title: str, content: str):
    """
    Create an error panel with Nord Theme styling
    
    Args:
        title: Panel title
        content: Panel content
    """
    return Panel(
        Text(content, style=NORD_RED),
        border_style=NORD_RED,
        title=title,
        title_align="center"
    )

def create_success_panel(title: str, content: str):
    """
    Create a success panel with Nord Theme styling
    
    Args:
        title: Panel title
        content: Panel content
    """
    return Panel(
        Text(content, style=NORD_GREEN),
        border_style=NORD_GREEN,
        title=title,
        title_align="center"
    )

def create_warning_panel(title: str, content: str):
    """
    Create a warning panel with Nord Theme styling
    
    Args:
        title: Panel title
        content: Panel content
    """
    return Panel(
        Text(content, style=NORD_YELLOW),
        border_style=NORD_YELLOW,
        title=title,
        title_align="center"
    )

def create_table(title: str, columns: List[str], rows: List[List[str]]):
    """
    Create a table with Nord Theme styling
    
    Args:
        title: Table title
        columns: Column names
        rows: Table rows
        
    Returns:
        Table: Rich table
    """
    table = Table(title=title, title_style=NORD_BLUE, border_style=NORD_BLUE)
    
    # Add columns
    for column in columns:
        table.add_column(column, style=NORD_WHITE)
    
    # Add rows
    for row in rows:
        table.add_row(*row)
    
    return table

def prompt_input(prompt_text: str, default: Optional[str] = None) -> str:
    """
    Prompt for user input with Nord Theme styling
    
    Args:
        prompt_text: Prompt text
        default: Default value
        
    Returns:
        str: User input
    """
    return Prompt.ask(f"[{NORD_CYAN}]{prompt_text}[/{NORD_CYAN}]", default=default)

def prompt_confirm(prompt_text: str, default: bool = False) -> bool:
    """
    Prompt for confirmation with Nord Theme styling
    
    Args:
        prompt_text: Prompt text
        default: Default value
        
    Returns:
        bool: User confirmation
    """
    return Confirm.ask(f"[{NORD_CYAN}]{prompt_text}[/{NORD_CYAN}]", default=default)

def prompt_choice(prompt_text: str, choices: List[str], default: Optional[str] = None) -> str:
    """
    Prompt for choice with Nord Theme styling
    
    Args:
        prompt_text: Prompt text
        choices: Available choices
        default: Default value
        
    Returns:
        str: User choice
    """
    return Prompt.ask(
        f"[{NORD_CYAN}]{prompt_text}[/{NORD_CYAN}]",
        choices=choices,
        default=default
    )

def display_dict(data: Dict[str, Any], title: str):
    """
    Display a dictionary as a table
    
    Args:
        data: Dictionary to display
        title: Table title
    """
    table = Table(title=title, title_style=NORD_BLUE, border_style=NORD_BLUE)
    table.add_column("Key", style=NORD_CYAN)
    table.add_column("Value", style=NORD_WHITE)
    
    for key, value in data.items():
        if isinstance(value, dict):
            nested_value = "\n".join([f"{k}: {v}" for k, v in value.items()])
            table.add_row(key, nested_value)
        else:
            table.add_row(key, str(value))
    
    console.print(table)

def print_info(message: str):
    """
    Print an info message with Nord Theme styling
    
    Args:
        message: Message to print
    """
    console.print(f"[{NORD_CYAN}]{message}[/{NORD_CYAN}]")

def print_error(message: str):
    """
    Print an error message with Nord Theme styling
    
    Args:
        message: Message to print
    """
    console.print(f"[{NORD_RED}]ERROR: {message}[/{NORD_RED}]")

def print_success(message: str):
    """
    Print a success message with Nord Theme styling
    
    Args:
        message: Message to print
    """
    console.print(f"[{NORD_GREEN}]{message}[/{NORD_GREEN}]")

def print_warning(message: str):
    """
    Print a warning message with Nord Theme styling
    
    Args:
        message: Message to print
    """
    console.print(f"[{NORD_YELLOW}]WARNING: {message}[/{NORD_YELLOW}]")

def show_welcome():
    """Display the welcome screen with Figlet ASCII art centered"""
    figlet = Figlet(font="ogre")
    title_art = figlet.renderText("CURSO PROCESSOR")
    centered_title = Align.center(Text(title_art, style=f"bold {NORD_CYAN}"))
    console.print(centered_title)
    console.print()

def display_ascii_art():
    """Display the ASCII art title centered (legacy function)"""
    # Call the new function for compatibility
    show_welcome()

def handle_error(title: str, exception: Exception):
    """Handle and display errors"""
    console.print(f"[{NORD_RED}]{title}: {str(exception)}[/{NORD_RED}]")
    console.print_exception()

def display_system_status():
    """Display current system status for the main menu"""
    # Import settings and credentials modules
    from config import settings, credentials
    from utils.progress_tracker import get_processed_courses_stats
    
    # Get current settings
    current_settings = settings.get_settings()
    
    # Get API status
    api_status = credentials.get_service_status()
    
    # Get processed courses stats
    stats = {
        'total_courses': 0,
        'total_size_formatted': '0 MB'
    }
    
    try:
        stats = get_processed_courses_stats()
    except Exception:
        pass
    
    # Format API status
    api_status_text = " | ".join([
        f"{service['name'].upper()} {'✓' if service['configured'] else '❌'}"
        for service in api_status
    ])
    
    # Format directory status
    dir_status_text = " | ".join([
        f"{name} {'✓' if os.path.exists(path) else '❌'}"
        for name, path in [
            ("Trabalho", current_settings['directories']['work_directory']),
            ("GitHub", current_settings['directories']['github_local']),
            ("XML", current_settings['directories']['xml_output'])
        ]
    ])
    
    # Format cache status
    cache_status = f"{stats['total_courses']} cursos processados | {stats['total_size_formatted']} usado"
    
    # Create status panel
    status_panel = Panel(
        Text.from_markup(
            "\n".join([
                f"[{NORD_CYAN}]🎓 CURSO PROCESSOR v2.0[/{NORD_CYAN}]",
                f"[{NORD_DIM}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_DIM}]",
                "",
                f"[{NORD_CYAN}]📊 Status do Sistema:[/{NORD_CYAN}]",
                f"   🔑 APIs: {api_status_text}",
                f"   📁 Dirs: {dir_status_text}",
                f"   💾 Cache: {cache_status}",
            ])
        ),
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    
    console.print(status_panel)

def display_settings_status():
    """Display current settings status"""
    # Import settings and credentials modules
    from config import settings, credentials
    
    # Get current settings
    current_settings = settings.get_settings()
    
    # Get API status
    api_status = credentials.get_service_status()
    
    # Create status panel
    status_panel = Panel(
        Text.from_markup(
            "\n".join([
                f"[{NORD_CYAN}]⚙️ Configurações do Sistema[/{NORD_CYAN}]",
                f"[{NORD_DIM}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_DIM}]",
                "",
                f"[{NORD_CYAN}]📁 Diretórios:[/{NORD_CYAN}]",
                f"   • Trabalho: {current_settings['directories']['work_directory']} {'✓' if os.path.exists(current_settings['directories']['work_directory']) else '❌'}",
                f"   • GitHub: {current_settings['directories']['github_local']} {'✓' if os.path.exists(current_settings['directories']['github_local']) else '❌'}",
                f"   • XML: {current_settings['directories']['xml_output']} {'✓' if os.path.exists(current_settings['directories']['xml_output']) else '❌'}",
                "",
                f"[{NORD_CYAN}]🗣️ Idioma e Voz:[/{NORD_CYAN}]",
                f"   • Interface: {current_settings['language']['interface']}",
                f"   • TTS: {current_settings['language']['tts_voice']}",
                "",
                f"[{NORD_CYAN}]🔑 APIs Configuradas:[/{NORD_CYAN}]"
            ] + [
                f"   • {service['name'].capitalize()}: {'✓ Configurada' if service['configured'] else '❌ Não configurada'}" 
                for service in api_status
            ])
        ),
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    
    console.print(status_panel)

def display_api_credentials_menu():
    """Display API credentials management menu"""
    # Import credentials module
    from config import credentials
    
    # Get API status
    api_status = credentials.get_service_status()
    
    # Create status panel
    status_panel = Panel(
        Text.from_markup(
            "\n".join([
                f"[{NORD_CYAN}]🔑 Gerenciamento de APIs[/{NORD_CYAN}]",
                f"[{NORD_DIM}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_DIM}]",
                "",
                f"[{NORD_CYAN}]Status atual:[/{NORD_CYAN}]"
            ] + [
                f"{'✅' if service['configured'] and service['status'] == 'valid' else '❌'} "
                f"{service['name'].capitalize()} "
                f"({service['status'] if service['configured'] else 'não configurada'}"
                f"{' - ' + service['last_validated'].split('T')[0] if service['last_validated'] else ''})"
                for service in api_status
            ])
        ),
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    console.print(status_panel)
    
    # Create credentials panel
    credentials_panel = Panel(
        Text.from_markup(
            "\n".join([
                f"[{NORD_BLUE}][1][/{NORD_BLUE}] ➕ Adicionar Nova API",
                f"[{NORD_BLUE}][2][/{NORD_BLUE}] 🔧 Testar APIs Existentes",
                f"[{NORD_BLUE}][3][/{NORD_BLUE}] 🗑️ Remover API",
                f"[{NORD_BLUE}][4][/{NORD_BLUE}] 📊 Ver Uso/Limites",
                f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
            ])
        ),
        title="[bold]Gerenciamento de APIs[/bold]",
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    console.print(credentials_panel)