"""
Prompt Manager - Advanced prompt management and versioning system
"""

import os
import json
import shutil
import re
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown

# Import modules
# Import settings conditionally to avoid keyring issues
try:
    from config import settings
    HAS_SETTINGS = True
except Exception:
    HAS_SETTINGS = False
    
    # Define fallback settings
    class FallbackSettings:
        @staticmethod
        def get_default_transcription_dir():
            return os.path.join(os.getcwd(), "data", "transcriptions")
from utils.ui_components import (
    console, NORD_BLUE, NORD_CYAN, NORD_GREEN, NORD_YELLOW, NORD_RED, NORD_DIM,
    create_progress_bar, handle_error
)

class PromptManager:
    """
    Advanced prompt management and versioning system
    """
    def __init__(self, console: Console = None):
        """
        Initialize the PromptManager
        """
        self.console = console or Console()
        self.prompts_dir = Path("prompts")
        self.custom_dir = self.prompts_dir / "custom"
        self.versions_dir = self.prompts_dir / "versions"
        self.stats_file = self.prompts_dir / "stats.json"
        
        # Ensure directories exist
        self.prompts_dir.mkdir(exist_ok=True)
        self.custom_dir.mkdir(exist_ok=True)
        self.versions_dir.mkdir(exist_ok=True)
        
        # Initialize stats file if it doesn't exist
        if not self.stats_file.exists():
            self._initialize_stats_file()
        
        # Load prompt templates
        self.prompt_templates = self.load_prompt_templates()
    
    def _initialize_stats_file(self):
        """
        Initialize the stats file with default values
        """
        stats = {
            "prompts": {},
            "global_stats": {
                "total_uses": 0,
                "avg_tokens": 0,
                "avg_rating": 0,
                "last_updated": datetime.now().isoformat()
            }
        }
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def load_prompt_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all prompt templates from the prompts directory
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of prompt templates
        """
        templates = {}
        
        # Load prompts from main directory
        for prompt_file in self.prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            with open(prompt_file, 'r') as f:
                content = f.read()
            
            # Get stats for this prompt
            stats = self._get_prompt_stats(prompt_name)
            
            templates[prompt_name] = {
                "name": prompt_name,
                "path": str(prompt_file),
                "content": content,
                "category": self._detect_category(content),
                "custom": False,
                "version": stats.get("current_version", "v1.0"),
                "last_used": stats.get("last_used", "Never"),
                "rating": stats.get("avg_rating", 0),
                "uses": stats.get("uses", 0)
            }
        
        # Load prompts from custom directory
        for prompt_file in self.custom_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            with open(prompt_file, 'r') as f:
                content = f.read()
            
            # Get stats for this prompt
            stats = self._get_prompt_stats(prompt_name)
            
            templates[prompt_name] = {
                "name": prompt_name,
                "path": str(prompt_file),
                "content": content,
                "category": self._detect_category(content),
                "custom": True,
                "version": stats.get("current_version", "v1.0"),
                "last_used": stats.get("last_used", "Never"),
                "rating": stats.get("avg_rating", 0),
                "uses": stats.get("uses", 0)
            }
        
        return templates
    
    def _detect_category(self, content: str) -> str:
        """
        Detect the category of a prompt based on its content
        
        Args:
            content (str): The prompt content
            
        Returns:
            str: The detected category
        """
        # Simple keyword-based detection
        keywords = {
            "technical": ["code", "programming", "technical", "technology", "software", "hardware", "algorithm"],
            "business": ["business", "marketing", "sales", "finance", "management", "strategy", "company"],
            "creative": ["creative", "art", "design", "story", "narrative", "creative writing"],
            "educational": ["education", "learning", "teaching", "academic", "study", "course", "lesson"]
        }
        
        counts = {category: 0 for category in keywords}
        
        for category, words in keywords.items():
            for word in words:
                counts[category] += content.lower().count(word)
        
        # Get the category with the highest count
        max_category = max(counts, key=counts.get)
        
        # If no keywords found, return "general"
        if counts[max_category] == 0:
            return "general"
        
        return max_category
    
    def _get_prompt_stats(self, prompt_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific prompt
        
        Args:
            prompt_name (str): The name of the prompt
            
        Returns:
            Dict[str, Any]: Statistics for the prompt
        """
        if not self.stats_file.exists():
            return {}
        
        with open(self.stats_file, 'r') as f:
            stats = json.load(f)
        
        return stats.get("prompts", {}).get(prompt_name, {})
    
    def _update_prompt_stats(self, prompt_name: str, stats_update: Dict[str, Any]):
        """
        Update statistics for a specific prompt
        
        Args:
            prompt_name (str): The name of the prompt
            stats_update (Dict[str, Any]): The statistics to update
        """
        with open(self.stats_file, 'r') as f:
            stats = json.load(f)
        
        if prompt_name not in stats["prompts"]:
            stats["prompts"][prompt_name] = {
                "uses": 0,
                "avg_tokens": 0,
                "avg_rating": 0,
                "current_version": "v1.0",
                "last_used": "Never"
            }
        
        # Update prompt stats
        for key, value in stats_update.items():
            stats["prompts"][prompt_name][key] = value
        
        # Update global stats
        total_uses = sum(prompt_stats.get("uses", 0) for prompt_stats in stats["prompts"].values())
        avg_tokens = sum(prompt_stats.get("avg_tokens", 0) * prompt_stats.get("uses", 0) 
                        for prompt_stats in stats["prompts"].values()) / max(total_uses, 1)
        avg_rating = sum(prompt_stats.get("avg_rating", 0) * prompt_stats.get("uses", 0) 
                        for prompt_stats in stats["prompts"].values()) / max(total_uses, 1)
        
        stats["global_stats"] = {
            "total_uses": total_uses,
            "avg_tokens": avg_tokens,
            "avg_rating": avg_rating,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def get_prompt_content(self, prompt_name: str, **variables) -> str:
        """
        Get the content of a prompt with variables replaced
        
        Args:
            prompt_name (str): The name of the prompt
            **variables: Variables to replace in the prompt
            
        Returns:
            str: The prompt content with variables replaced
        """
        if prompt_name not in self.prompt_templates:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        content = self.prompt_templates[prompt_name]["content"]
        
        # Replace variables
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        # Update usage statistics
        self._update_prompt_stats(prompt_name, {
            "last_used": datetime.now().isoformat(),
            "uses": self.prompt_templates[prompt_name]["uses"] + 1
        })
        
        return content
    
    def create_custom_prompt(self):
        """
        Create a new custom prompt via interactive interface
        """
        self.console.print(f"[bold {NORD_BLUE}]✨ Criador de Prompt Personalizado[/]")
        
        prompt_name = Prompt.ask("Nome do prompt")
        
        # Check if prompt already exists
        if prompt_name in self.prompt_templates:
            if not Confirm.ask(f"Prompt '{prompt_name}' já existe. Deseja sobrescrever?"):
                self.console.print(f"[{NORD_YELLOW}]Operação cancelada.[/{NORD_YELLOW}]")
                return
        
        prompt_category = Prompt.ask("Categoria", 
                                    choices=["technical", "business", "creative", "educational", "general"],
                                    default="general")
        
        # Show available variables
        self.console.print(f"\n[{NORD_CYAN}]Variáveis disponíveis:[/{NORD_CYAN}]")
        variables_table = Table(show_header=True, header_style=NORD_BLUE)
        variables_table.add_column("Variável")
        variables_table.add_column("Descrição")
        
        variables = [
            ("{{TRANSCRIPTION}}", "Conteúdo da transcrição"),
            ("{{COURSE_NAME}}", "Nome do curso"),
            ("{{FILE_NAME}}", "Nome do arquivo atual"),
            ("{{DURATION}}", "Duração do áudio"),
            ("{{COURSE_CATEGORY}}", "Categoria detectada automaticamente"),
            ("{{USER_PROFILE}}", "Perfil do usuário (TDAH, analítico, etc.)"),
            ("{{LANGUAGE}}", "Idioma do conteúdo"),
            ("{{COMPLEXITY_LEVEL}}", "Nível de complexidade detectado")
        ]
        
        for var, desc in variables:
            variables_table.add_row(var, desc)
        
        self.console.print(variables_table)
        
        self.console.print(f"\n[{NORD_CYAN}]📝 Editor de Prompt (use Ctrl+D para finalizar):[/{NORD_CYAN}]")
        prompt_content = ""
        
        try:
            while True:
                line = input()
                prompt_content += line + "\n"
        except EOFError:
            pass
        
        # Preview do prompt
        preview_panel = Panel(prompt_content, title="Preview do Prompt", border_style=NORD_GREEN)
        self.console.print(preview_panel)
        
        if Confirm.ask("Salvar este prompt?"):
            # Save the prompt
            prompt_path = self.custom_dir / f"{prompt_name}.txt"
            with open(prompt_path, 'w') as f:
                f.write(prompt_content)
            
            # Create initial version
            self.save_prompt_version(prompt_name, prompt_content, "Initial version")
            
            # Update prompt templates
            self.prompt_templates[prompt_name] = {
                "name": prompt_name,
                "path": str(prompt_path),
                "content": prompt_content,
                "category": prompt_category,
                "custom": True,
                "version": "v1.0",
                "last_used": "Never",
                "rating": 0,
                "uses": 0
            }
            
            # Update stats
            self._update_prompt_stats(prompt_name, {
                "current_version": "v1.0",
                "category": prompt_category
            })
            
            self.console.print(f"[{NORD_GREEN}]✅ Prompt '{prompt_name}' criado com sucesso![/{NORD_GREEN}]")
        else:
            self.console.print(f"[{NORD_YELLOW}]Operação cancelada.[/{NORD_YELLOW}]")
    
    def edit_prompt(self, prompt_name: str):
        """
        Edit an existing prompt
        
        Args:
            prompt_name (str): The name of the prompt to edit
        """
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt '{prompt_name}' não encontrado.[/{NORD_RED}]")
            return
        
        prompt_data = self.prompt_templates[prompt_name]
        
        self.console.print(f"[bold {NORD_BLUE}]✏️ Editando Prompt: {prompt_name}[/]")
        
        # Show current content
        self.console.print(f"\n[{NORD_CYAN}]Conteúdo atual:[/{NORD_CYAN}]")
        current_panel = Panel(prompt_data["content"], title="Conteúdo Atual", border_style=NORD_BLUE)
        self.console.print(current_panel)
        
        # Show available variables
        self.console.print(f"\n[{NORD_CYAN}]Variáveis disponíveis:[/{NORD_CYAN}]")
        variables_table = Table(show_header=True, header_style=NORD_BLUE)
        variables_table.add_column("Variável")
        variables_table.add_column("Descrição")
        
        variables = [
            ("{{TRANSCRIPTION}}", "Conteúdo da transcrição"),
            ("{{COURSE_NAME}}", "Nome do curso"),
            ("{{FILE_NAME}}", "Nome do arquivo atual"),
            ("{{DURATION}}", "Duração do áudio"),
            ("{{COURSE_CATEGORY}}", "Categoria detectada automaticamente"),
            ("{{USER_PROFILE}}", "Perfil do usuário (TDAH, analítico, etc.)"),
            ("{{LANGUAGE}}", "Idioma do conteúdo"),
            ("{{COMPLEXITY_LEVEL}}", "Nível de complexidade detectado")
        ]
        
        for var, desc in variables:
            variables_table.add_row(var, desc)
        
        self.console.print(variables_table)
        
        # Edit content
        self.console.print(f"\n[{NORD_CYAN}]📝 Editor de Prompt (use Ctrl+D para finalizar):[/{NORD_CYAN}]")
        self.console.print(f"[{NORD_DIM}]O conteúdo atual já está preenchido no editor.[/{NORD_DIM}]")
        
        # Pre-fill with current content
        prompt_content = prompt_data["content"]
        print(prompt_content, end="")
        
        new_content = ""
        try:
            while True:
                line = input()
                new_content += line + "\n"
        except EOFError:
            pass
        
        # If no new content was entered, use the current content
        if not new_content.strip():
            new_content = prompt_content
        
        # Preview do prompt
        preview_panel = Panel(new_content, title="Preview do Prompt", border_style=NORD_GREEN)
        self.console.print(preview_panel)
        
        # Ask for changes summary
        changes_summary = Prompt.ask("Resumo das alterações")
        
        if Confirm.ask("Salvar este prompt?"):
            # Get next version
            current_version = prompt_data["version"]
            next_version = self.get_next_version(prompt_name)
            
            # Save the prompt
            prompt_path = Path(prompt_data["path"])
            with open(prompt_path, 'w') as f:
                f.write(new_content)
            
            # Save version
            self.save_prompt_version(prompt_name, new_content, changes_summary)
            
            # Update prompt templates
            self.prompt_templates[prompt_name]["content"] = new_content
            self.prompt_templates[prompt_name]["version"] = next_version
            
            # Update stats
            self._update_prompt_stats(prompt_name, {
                "current_version": next_version
            })
            
            self.console.print(f"[{NORD_GREEN}]✅ Prompt '{prompt_name}' atualizado com sucesso para versão {next_version}![/{NORD_GREEN}]")
        else:
            self.console.print(f"[{NORD_YELLOW}]Operação cancelada.[/{NORD_YELLOW}]")
    
    def get_next_version(self, prompt_name: str) -> str:
        """
        Get the next version number for a prompt
        
        Args:
            prompt_name (str): The name of the prompt
            
        Returns:
            str: The next version number (e.g., "v1.2")
        """
        if prompt_name not in self.prompt_templates:
            return "v1.0"
        
        current_version = self.prompt_templates[prompt_name]["version"]
        
        # Parse version
        match = re.match(r"v(\d+)\.(\d+)", current_version)
        if not match:
            return "v1.0"
        
        major, minor = map(int, match.groups())
        
        # Increment minor version
        minor += 1
        
        return f"v{major}.{minor}"
    
    def save_prompt_version(self, prompt_name: str, content: str, changes_summary: str):
        """
        Save a new version of a prompt
        
        Args:
            prompt_name (str): The name of the prompt
            content (str): The prompt content
            changes_summary (str): Summary of changes
        """
        version = self.get_next_version(prompt_name)
        
        version_info = {
            "version": version,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "changes": changes_summary,
            "performance_metrics": {
                "avg_tokens": 0,
                "success_rate": 0,
                "user_rating": 0
            }
        }
        
        # Save in /prompts/versions/prompt_name_v1.2.json
        version_file = self.versions_dir / f"{prompt_name}_{version}.json"
        with open(version_file, 'w') as f:
            json.dump(version_info, f, indent=2)
    
    def manage_prompt_versions(self, prompt_name: str = None):
        """
        Manage versions of prompts
        
        Args:
            prompt_name (str, optional): The name of the prompt to manage. If None, user will be asked to select.
        """
        if not prompt_name:
            # Show available prompts
            self.console.print(f"[bold {NORD_BLUE}]🔄 Gerenciamento de Versões[/]")
            
            prompts_table = Table(show_header=True, header_style=NORD_BLUE)
            prompts_table.add_column("ID")
            prompts_table.add_column("Nome")
            prompts_table.add_column("Versão Atual")
            prompts_table.add_column("Categoria")
            
            for i, (name, data) in enumerate(self.prompt_templates.items(), 1):
                prompts_table.add_row(
                    str(i),
                    name,
                    data["version"],
                    data["category"]
                )
            
            self.console.print(prompts_table)
            
            # Ask for prompt to manage
            prompt_id = Prompt.ask("Selecione o ID do prompt para gerenciar versões", default="1")
            
            try:
                prompt_id = int(prompt_id)
                if prompt_id < 1 or prompt_id > len(self.prompt_templates):
                    self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    return
                
                prompt_name = list(self.prompt_templates.keys())[prompt_id - 1]
            except ValueError:
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
        
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt '{prompt_name}' não encontrado.[/{NORD_RED}]")
            return
        
        # Get versions for this prompt
        versions = []
        for version_file in self.versions_dir.glob(f"{prompt_name}_v*.json"):
            with open(version_file, 'r') as f:
                version_data = json.load(f)
                versions.append(version_data)
        
        # Sort versions by creation date
        versions.sort(key=lambda v: v["created_at"], reverse=True)
        
        if not versions:
            self.console.print(f"[{NORD_YELLOW}]Nenhuma versão encontrada para o prompt '{prompt_name}'.[/{NORD_YELLOW}]")
            return
        
        # Show versions
        self.console.print(f"\n[bold {NORD_BLUE}]Versões do Prompt: {prompt_name}[/]")
        
        versions_table = Table(show_header=True, header_style=NORD_BLUE)
        versions_table.add_column("ID")
        versions_table.add_column("Versão")
        versions_table.add_column("Data de Criação")
        versions_table.add_column("Alterações")
        versions_table.add_column("Rating")
        
        for i, version in enumerate(versions, 1):
            # Format date
            created_at = datetime.fromisoformat(version["created_at"])
            date_str = created_at.strftime("%d/%m/%Y %H:%M")
            
            # Format rating
            rating = version["performance_metrics"]["user_rating"]
            rating_str = "⭐" * int(rating) if rating > 0 else "N/A"
            
            versions_table.add_row(
                str(i),
                version["version"],
                date_str,
                version["changes"],
                rating_str
            )
        
        self.console.print(versions_table)
        
        # Show options
        self.console.print(f"\n[{NORD_CYAN}]Opções:[/{NORD_CYAN}]")
        self.console.print(f"[{NORD_BLUE}][1][/{NORD_BLUE}] 👁️ Visualizar versão")
        self.console.print(f"[{NORD_BLUE}][2][/{NORD_BLUE}] 🔄 Reverter para versão")
        self.console.print(f"[{NORD_BLUE}][3][/{NORD_BLUE}] 🔍 Comparar versões")
        self.console.print(f"[{NORD_BLUE}][4][/{NORD_BLUE}] 📊 Ver métricas de desempenho")
        self.console.print(f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar")
        
        option = Prompt.ask("Escolha uma opção", choices=["0", "1", "2", "3", "4"], default="0")
        
        if option == "0":
            return
        elif option == "1":
            # View version
            version_id = Prompt.ask("ID da versão para visualizar")
            
            try:
                version_id = int(version_id)
                if version_id < 1 or version_id > len(versions):
                    self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    return
                
                version = versions[version_id - 1]
                
                # Show version content
                self.console.print(f"\n[bold {NORD_BLUE}]Conteúdo da Versão {version['version']}:[/]")
                content_panel = Panel(version["content"], title=f"Versão {version['version']} - {version['changes']}", border_style=NORD_GREEN)
                self.console.print(content_panel)
                
                # Wait for user to continue
                Prompt.ask("Pressione Enter para continuar", default="")
                
                # Recursive call to show versions again
                self.manage_prompt_versions(prompt_name)
            except ValueError:
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
        elif option == "2":
            # Revert to version
            version_id = Prompt.ask("ID da versão para reverter")
            
            try:
                version_id = int(version_id)
                if version_id < 1 or version_id > len(versions):
                    self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    return
                
                version = versions[version_id - 1]
                
                # Show version content
                self.console.print(f"\n[bold {NORD_BLUE}]Conteúdo da Versão {version['version']}:[/]")
                content_panel = Panel(version["content"], title=f"Versão {version['version']} - {version['changes']}", border_style=NORD_GREEN)
                self.console.print(content_panel)
                
                if Confirm.ask(f"Reverter para versão {version['version']}?"):
                    # Save the prompt
                    prompt_path = Path(self.prompt_templates[prompt_name]["path"])
                    with open(prompt_path, 'w') as f:
                        f.write(version["content"])
                    
                    # Save new version
                    next_version = self.get_next_version(prompt_name)
                    self.save_prompt_version(
                        prompt_name, 
                        version["content"], 
                        f"Revertido para versão {version['version']}"
                    )
                    
                    # Update prompt templates
                    self.prompt_templates[prompt_name]["content"] = version["content"]
                    self.prompt_templates[prompt_name]["version"] = next_version
                    
                    # Update stats
                    self._update_prompt_stats(prompt_name, {
                        "current_version": next_version
                    })
                    
                    self.console.print(f"[{NORD_GREEN}]✅ Prompt revertido com sucesso para versão {version['version']}![/{NORD_GREEN}]")
                else:
                    self.console.print(f"[{NORD_YELLOW}]Operação cancelada.[/{NORD_YELLOW}]")
                
                # Recursive call to show versions again
                self.manage_prompt_versions(prompt_name)
            except ValueError:
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
        elif option == "3":
            # Compare versions
            version_id1 = Prompt.ask("ID da primeira versão")
            version_id2 = Prompt.ask("ID da segunda versão")
            
            try:
                version_id1 = int(version_id1)
                version_id2 = int(version_id2)
                
                if (version_id1 < 1 or version_id1 > len(versions) or 
                    version_id2 < 1 or version_id2 > len(versions)):
                    self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    return
                
                version1 = versions[version_id1 - 1]
                version2 = versions[version_id2 - 1]
                
                # Show comparison
                self.console.print(f"\n[bold {NORD_BLUE}]Comparação de Versões:[/]")
                
                # Create side-by-side panels
                from rich.columns import Columns
                
                panel1 = Panel(
                    version1["content"], 
                    title=f"Versão {version1['version']} - {version1['changes']}", 
                    border_style=NORD_BLUE
                )
                
                panel2 = Panel(
                    version2["content"], 
                    title=f"Versão {version2['version']} - {version2['changes']}", 
                    border_style=NORD_GREEN
                )
                
                self.console.print(Columns([panel1, panel2]))
                
                # Wait for user to continue
                Prompt.ask("Pressione Enter para continuar", default="")
                
                # Recursive call to show versions again
                self.manage_prompt_versions(prompt_name)
            except ValueError:
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
        elif option == "4":
            # View performance metrics
            version_id = Prompt.ask("ID da versão para ver métricas")
            
            try:
                version_id = int(version_id)
                if version_id < 1 or version_id > len(versions):
                    self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    return
                
                version = versions[version_id - 1]
                
                # Show metrics
                self.console.print(f"\n[bold {NORD_BLUE}]Métricas de Desempenho - Versão {version['version']}:[/]")
                
                metrics_table = Table(show_header=True, header_style=NORD_BLUE)
                metrics_table.add_column("Métrica")
                metrics_table.add_column("Valor")
                
                metrics = version["performance_metrics"]
                
                metrics_table.add_row("Média de Tokens", str(metrics["avg_tokens"]))
                metrics_table.add_row("Taxa de Sucesso", f"{metrics['success_rate']}%")
                metrics_table.add_row("Avaliação do Usuário", "⭐" * int(metrics["user_rating"]) if metrics["user_rating"] > 0 else "N/A")
                
                self.console.print(metrics_table)
                
                # Wait for user to continue
                Prompt.ask("Pressione Enter para continuar", default="")
                
                # Recursive call to show versions again
                self.manage_prompt_versions(prompt_name)
            except ValueError:
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
    
    def test_prompt_effectiveness(self, prompt_name: str = None):
        """
        Test the effectiveness of a prompt
        
        Args:
            prompt_name (str, optional): The name of the prompt to test. If None, user will be asked to select.
        """
        if not prompt_name:
            # Show available prompts
            self.console.print(f"[bold {NORD_BLUE}]🧪 Teste de Efetividade de Prompts[/]")
            
            prompts_table = Table(show_header=True, header_style=NORD_BLUE)
            prompts_table.add_column("ID")
            prompts_table.add_column("Nome")
            prompts_table.add_column("Versão Atual")
            prompts_table.add_column("Categoria")
            
            for i, (name, data) in enumerate(self.prompt_templates.items(), 1):
                prompts_table.add_row(
                    str(i),
                    name,
                    data["version"],
                    data["category"]
                )
            
            self.console.print(prompts_table)
            
            # Ask for prompt to test
            prompt_id = Prompt.ask("Selecione o ID do prompt para testar", default="1")
            
            try:
                prompt_id = int(prompt_id)
                if prompt_id < 1 or prompt_id > len(self.prompt_templates):
                    self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    return
                
                prompt_name = list(self.prompt_templates.keys())[prompt_id - 1]
            except ValueError:
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
        
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt '{prompt_name}' não encontrado.[/{NORD_RED}]")
            return
        
        # Get sample transcription
        self.console.print(f"\n[{NORD_CYAN}]Selecione uma amostra de transcrição para testar:[/{NORD_CYAN}]")
        
        # Get transcription files
        if HAS_SETTINGS:
            transcription_dir = Path(settings.get_default_transcription_dir())
        else:
            transcription_dir = Path(FallbackSettings.get_default_transcription_dir())
        if not transcription_dir.exists():
            self.console.print(f"[{NORD_RED}]Diretório de transcrições não encontrado.[/{NORD_RED}]")
            return
        
        transcription_files = list(transcription_dir.glob("*.txt"))
        
        if not transcription_files:
            self.console.print(f"[{NORD_RED}]Nenhuma transcrição encontrada.[/{NORD_RED}]")
            return
        
        # Show transcription files
        transcriptions_table = Table(show_header=True, header_style=NORD_BLUE)
        transcriptions_table.add_column("ID")
        transcriptions_table.add_column("Arquivo")
        transcriptions_table.add_column("Tamanho")
        
        for i, file in enumerate(transcription_files, 1):
            # Get file size
            size_kb = file.stat().st_size / 1024
            size_str = f"{size_kb:.1f} KB"
            
            transcriptions_table.add_row(
                str(i),
                file.name,
                size_str
            )
        
        self.console.print(transcriptions_table)
        
        # Ask for transcription to test
        transcription_id = Prompt.ask("Selecione o ID da transcrição para testar", default="1")
        
        try:
            transcription_id = int(transcription_id)
            if transcription_id < 1 or transcription_id > len(transcription_files):
                self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                return
            
            transcription_file = transcription_files[transcription_id - 1]
        except ValueError:
            self.console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
            return
        
        # Read transcription
        with open(transcription_file, 'r') as f:
            transcription_content = f.read()
        
        # Get prompt content
        prompt_content = self.prompt_templates[prompt_name]["content"]
        
        # Replace variables
        variables = {
            "TRANSCRIPTION": transcription_content,
            "COURSE_NAME": "Curso de Teste",
            "FILE_NAME": transcription_file.name,
            "DURATION": "10:30",
            "COURSE_CATEGORY": "technical",
            "USER_PROFILE": "analítico",
            "LANGUAGE": "pt-BR",
            "COMPLEXITY_LEVEL": "intermediário"
        }
        
        for var_name, var_value in variables.items():
            prompt_content = prompt_content.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        # Show prompt with variables replaced
        self.console.print(f"\n[bold {NORD_BLUE}]Prompt com Variáveis Substituídas:[/]")
        prompt_panel = Panel(prompt_content, title=f"Prompt: {prompt_name}", border_style=NORD_GREEN)
        self.console.print(prompt_panel)
        
        # Simulate AI processing
        self.console.print(f"\n[{NORD_CYAN}]Simulando processamento com IA...[/{NORD_CYAN}]")
        
        with Progress(
            TextColumn(f"[{NORD_BLUE}]{{task.description}}[/{NORD_BLUE}]"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(f"[{NORD_CYAN}]Processando...[/{NORD_CYAN}]", total=100)
            
            # Simulate processing
            for i in range(10):
                progress.update(task, advance=10)
                time.sleep(0.2)
        
        # Calculate metrics
        token_count = len(prompt_content.split())
        success_rate = random.randint(70, 100)  # Simulated success rate
        
        # Show results
        self.console.print(f"\n[bold {NORD_GREEN}]Resultados do Teste:[/]")
        
        results_table = Table(show_header=True, header_style=NORD_BLUE)
        results_table.add_column("Métrica")
        results_table.add_column("Valor")
        
        results_table.add_row("Tokens Utilizados", str(token_count))
        results_table.add_row("Taxa de Sucesso", f"{success_rate}%")
        
        self.console.print(results_table)
        
        # Ask for user rating
        rating = Prompt.ask("Avalie a qualidade do resultado (1-5)", choices=["1", "2", "3", "4", "5"], default="5")
        rating = int(rating)
        
        # Update metrics for this version
        version = self.prompt_templates[prompt_name]["version"]
        version_file = self.versions_dir / f"{prompt_name}_{version}.json"
        
        if version_file.exists():
            with open(version_file, 'r') as f:
                version_data = json.load(f)
            
            # Update metrics
            metrics = version_data["performance_metrics"]
            metrics["avg_tokens"] = (metrics["avg_tokens"] + token_count) / 2
            metrics["success_rate"] = (metrics["success_rate"] + success_rate) / 2
            metrics["user_rating"] = (metrics["user_rating"] + rating) / 2
            
            with open(version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
        
        # Update prompt stats
        self._update_prompt_stats(prompt_name, {
            "avg_rating": rating
        })
        
        # Show suggestions for improvement
        self.console.print(f"\n[bold {NORD_BLUE}]Sugestões para Melhoria:[/]")
        
        suggestions = []
        
        # Token count suggestions
        if token_count > 500:
            suggestions.append("O prompt é muito longo, considere reduzir para melhorar a eficiência.")
        elif token_count < 100:
            suggestions.append("O prompt é muito curto, considere adicionar mais contexto ou instruções.")
        
        # Variable usage suggestions
        for var_name in ["TRANSCRIPTION", "COURSE_NAME", "FILE_NAME"]:
            if f"{{{{{var_name}}}}}" not in self.prompt_templates[prompt_name]["content"]:
                suggestions.append(f"Considere usar a variável {{{{{var_name}}}}} para tornar o prompt mais dinâmico.")
        
        # Structure suggestions
        if ":" not in self.prompt_templates[prompt_name]["content"]:
            suggestions.append("Considere usar uma estrutura mais clara com seções delimitadas por ':'.")
        
        if not suggestions:
            suggestions.append("O prompt parece bem estruturado e eficiente.")
        
        for suggestion in suggestions:
            self.console.print(f"[{NORD_YELLOW}]• {suggestion}[/{NORD_YELLOW}]")
        
        self.console.print(f"\n[{NORD_GREEN}]✅ Teste concluído com sucesso![/{NORD_GREEN}]")
    
    def display_usage_statistics(self):
        """
        Display usage statistics for prompts
        """
        self.console.print(f"[bold {NORD_BLUE}]📊 Estatísticas de Uso de Prompts[/]")
        
        # Load stats
        with open(self.stats_file, 'r') as f:
            stats = json.load(f)
        
        # Show global stats
        global_stats = stats["global_stats"]
        
        self.console.print(f"\n[{NORD_CYAN}]Estatísticas Globais:[/{NORD_CYAN}]")
        
        global_table = Table(show_header=True, header_style=NORD_BLUE)
        global_table.add_column("Métrica")
        global_table.add_column("Valor")
        
        global_table.add_row("Total de Usos", str(global_stats["total_uses"]))
        global_table.add_row("Média de Tokens", f"{global_stats['avg_tokens']:.1f}")
        global_table.add_row("Média de Avaliação", f"{global_stats['avg_rating']:.1f} ⭐")
        
        # Format last updated
        last_updated = datetime.fromisoformat(global_stats["last_updated"])
        last_updated_str = last_updated.strftime("%d/%m/%Y %H:%M")
        
        global_table.add_row("Última Atualização", last_updated_str)
        
        self.console.print(global_table)
        
        # Show prompt stats
        self.console.print(f"\n[{NORD_CYAN}]Estatísticas por Prompt:[/{NORD_CYAN}]")
        
        prompts_table = Table(show_header=True, header_style=NORD_BLUE)
        prompts_table.add_column("Nome")
        prompts_table.add_column("Versão")
        prompts_table.add_column("Usos")
        prompts_table.add_column("Última Uso")
        prompts_table.add_column("Avaliação")
        
        # Sort prompts by usage
        prompt_stats = [(name, data) for name, data in stats["prompts"].items()]
        prompt_stats.sort(key=lambda x: x[1].get("uses", 0), reverse=True)
        
        for name, data in prompt_stats:
            # Skip prompts with no uses
            if data.get("uses", 0) == 0:
                continue
            
            # Format last used
            if data.get("last_used", "Never") == "Never":
                last_used_str = "Nunca"
            else:
                last_used = datetime.fromisoformat(data["last_used"])
                
                # If today, show time
                if last_used.date() == datetime.now().date():
                    last_used_str = f"Hoje {last_used.strftime('%H:%M')}"
                # If yesterday, show "Ontem"
                elif last_used.date() == (datetime.now().date() - datetime.timedelta(days=1)):
                    last_used_str = "Ontem"
                # If within a week, show days ago
                elif (datetime.now().date() - last_used.date()).days <= 7:
                    days = (datetime.now().date() - last_used.date()).days
                    last_used_str = f"{days} dias atrás"
                # Otherwise, show date
                else:
                    last_used_str = last_used.strftime("%d/%m/%Y")
            
            # Format rating
            rating = data.get("avg_rating", 0)
            rating_str = "⭐" * int(rating) if rating > 0 else "N/A"
            
            prompts_table.add_row(
                name,
                data.get("current_version", "v1.0"),
                str(data.get("uses", 0)),
                last_used_str,
                rating_str
            )
        
        self.console.print(prompts_table)
    
    def export_import_prompts(self):
        """
        Export or import prompts
        """
        self.console.print(f"[bold {NORD_BLUE}]📤 Exportar/Importar Prompts[/]")
        
        self.console.print(f"\n[{NORD_CYAN}]Opções:[/{NORD_CYAN}]")
        self.console.print(f"[{NORD_BLUE}][1][/{NORD_BLUE}] 📤 Exportar Prompts")
        self.console.print(f"[{NORD_BLUE}][2][/{NORD_BLUE}] 📥 Importar Prompts")
        self.console.print(f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar")
        
        option = Prompt.ask("Escolha uma opção", choices=["0", "1", "2"], default="0")
        
        if option == "0":
            return
        elif option == "1":
            # Export prompts
            self.console.print(f"\n[{NORD_CYAN}]Exportando Prompts...[/{NORD_CYAN}]")
            
            # Ask for export directory
            export_dir = Prompt.ask("Diretório para exportar", default="./exports")
            
            # Create directory if it doesn't exist
            export_path = Path(export_dir)
            export_path.mkdir(exist_ok=True, parents=True)
            
            # Create export file
            export_file = export_path / f"prompts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Prepare export data
            export_data = {
                "prompts": {},
                "versions": {},
                "stats": {},
                "exported_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # Export prompts
            for name, data in self.prompt_templates.items():
                export_data["prompts"][name] = {
                    "content": data["content"],
                    "category": data["category"],
                    "custom": data["custom"],
                    "version": data["version"]
                }
            
            # Export versions
            for version_file in self.versions_dir.glob("*.json"):
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                
                prompt_name = version_file.stem.split("_v")[0]
                version = version_file.stem.split("_v")[1]
                
                if prompt_name not in export_data["versions"]:
                    export_data["versions"][prompt_name] = {}
                
                export_data["versions"][prompt_name][version] = version_data
            
            # Export stats
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
            
            export_data["stats"] = stats
            
            # Save export file
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.console.print(f"[{NORD_GREEN}]✅ Prompts exportados com sucesso para {export_file}![/{NORD_GREEN}]")
        elif option == "2":
            # Import prompts
            self.console.print(f"\n[{NORD_CYAN}]Importando Prompts...[/{NORD_CYAN}]")
            
            # Ask for import file
            import_file = Prompt.ask("Arquivo de importação")
            
            import_path = Path(import_file)
            
            if not import_path.exists():
                self.console.print(f"[{NORD_RED}]Arquivo não encontrado: {import_file}[/{NORD_RED}]")
                return
            
            try:
                with open(import_path, 'r') as f:
                    import_data = json.load(f)
                
                # Validate import data
                if "prompts" not in import_data or "versions" not in import_data or "stats" not in import_data:
                    self.console.print(f"[{NORD_RED}]Arquivo de importação inválido.[/{NORD_RED}]")
                    return
                
                # Ask for import options
                self.console.print(f"\n[{NORD_CYAN}]Opções de Importação:[/{NORD_CYAN}]")
                
                import_prompts = Confirm.ask("Importar prompts?", default=True)
                import_versions = Confirm.ask("Importar versões?", default=True)
                import_stats = Confirm.ask("Importar estatísticas?", default=False)
                
                # Import prompts
                if import_prompts:
                    for name, data in import_data["prompts"].items():
                        # Determine file path
                        if data["custom"]:
                            prompt_path = self.custom_dir / f"{name}.txt"
                        else:
                            prompt_path = self.prompts_dir / f"{name}.txt"
                        
                        # Save prompt
                        with open(prompt_path, 'w') as f:
                            f.write(data["content"])
                        
                        # Update prompt templates
                        self.prompt_templates[name] = {
                            "name": name,
                            "path": str(prompt_path),
                            "content": data["content"],
                            "category": data["category"],
                            "custom": data["custom"],
                            "version": data["version"],
                            "last_used": "Never",
                            "rating": 0,
                            "uses": 0
                        }
                
                # Import versions
                if import_versions:
                    for prompt_name, versions in import_data["versions"].items():
                        for version, version_data in versions.items():
                            version_file = self.versions_dir / f"{prompt_name}_v{version}.json"
                            
                            with open(version_file, 'w') as f:
                                json.dump(version_data, f, indent=2)
                
                # Import stats
                if import_stats:
                    with open(self.stats_file, 'w') as f:
                        json.dump(import_data["stats"], f, indent=2)
                
                self.console.print(f"[{NORD_GREEN}]✅ Importação concluída com sucesso![/{NORD_GREEN}]")
                
                # Reload prompt templates
                self.prompt_templates = self.load_prompt_templates()
            except Exception as e:
                self.console.print(f"[{NORD_RED}]Erro ao importar prompts: {str(e)}[/{NORD_RED}]")
                return

def main():
    """
    Main function for the prompt manager
    """
    try:
        # Create prompt manager
        prompt_manager = PromptManager(console=console)
        
        while True:
            # Display header
            console.print(f"[bold {NORD_BLUE}]📝 Gerenciador de Prompts[/]")
            console.print(f"[{NORD_CYAN}]━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{NORD_CYAN}]\n")
            
            # Display available prompts
            console.print(f"[bold {NORD_BLUE}]📋 Prompts Disponíveis:[/]")
            
            prompts_table = Table(show_header=True, header_style=NORD_BLUE)
            prompts_table.add_column("Nome")
            prompts_table.add_column("Versão")
            prompts_table.add_column("Última Uso")
            prompts_table.add_column("Rating")
            
            for name, data in prompt_manager.prompt_templates.items():
                # Format last used
                if data["last_used"] == "Never":
                    last_used_str = "Nunca"
                else:
                    last_used = datetime.fromisoformat(data["last_used"])
                    
                    # If today, show time
                    if last_used.date() == datetime.now().date():
                        last_used_str = f"Hoje {last_used.strftime('%H:%M')}"
                    # If yesterday, show "Ontem"
                    elif last_used.date() == (datetime.now().date() - datetime.timedelta(days=1)):
                        last_used_str = "Ontem"
                    # If within a week, show days ago
                    elif (datetime.now().date() - last_used.date()).days <= 7:
                        days = (datetime.now().date() - last_used.date()).days
                        last_used_str = f"{days} dias"
                    # Otherwise, show date
                    else:
                        last_used_str = last_used.strftime("%d/%m/%Y")
                
                # Format rating
                rating = data["rating"]
                rating_str = "⭐" * int(rating) if rating > 0 else "N/A"
                
                prompts_table.add_row(
                    name,
                    data["version"],
                    last_used_str,
                    rating_str
                )
            
            console.print(prompts_table)
            
            # Display menu
            console.print(f"\n[{NORD_BLUE}][1][/{NORD_BLUE}] ➕ Criar Novo Prompt")
            console.print(f"[{NORD_BLUE}][2][/{NORD_BLUE}] ✏️ Editar Prompt Existente")
            console.print(f"[{NORD_BLUE}][3][/{NORD_BLUE}] 🔄 Gerenciar Versões")
            console.print(f"[{NORD_BLUE}][4][/{NORD_BLUE}] 🧪 Testar Prompt")
            console.print(f"[{NORD_BLUE}][5][/{NORD_BLUE}] 📊 Estatísticas de Uso")
            console.print(f"[{NORD_BLUE}][6][/{NORD_BLUE}] 📤 Exportar/Importar")
            console.print(f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar")
            
            choice = Prompt.ask("\nEscolha uma opção", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")
            
            if choice == "0":
                console.print(f"[{NORD_GREEN}]Voltando ao menu principal...[/{NORD_GREEN}]")
                break
            elif choice == "1":
                prompt_manager.create_custom_prompt()
            elif choice == "2":
                # Show available prompts
                console.print(f"\n[bold {NORD_BLUE}]✏️ Editar Prompt Existente[/]")
                
                prompts_table = Table(show_header=True, header_style=NORD_BLUE)
                prompts_table.add_column("ID")
                prompts_table.add_column("Nome")
                prompts_table.add_column("Versão")
                prompts_table.add_column("Categoria")
                
                for i, (name, data) in enumerate(prompt_manager.prompt_templates.items(), 1):
                    prompts_table.add_row(
                        str(i),
                        name,
                        data["version"],
                        data["category"]
                    )
                
                console.print(prompts_table)
                
                # Ask for prompt to edit
                prompt_id = Prompt.ask("Selecione o ID do prompt para editar", default="1")
                
                try:
                    prompt_id = int(prompt_id)
                    if prompt_id < 1 or prompt_id > len(prompt_manager.prompt_templates):
                        console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                        continue
                    
                    prompt_name = list(prompt_manager.prompt_templates.keys())[prompt_id - 1]
                    prompt_manager.edit_prompt(prompt_name)
                except ValueError:
                    console.print(f"[{NORD_RED}]ID inválido.[/{NORD_RED}]")
                    continue
            elif choice == "3":
                prompt_manager.manage_prompt_versions()
            elif choice == "4":
                prompt_manager.test_prompt_effectiveness()
            elif choice == "5":
                prompt_manager.display_usage_statistics()
            elif choice == "6":
                prompt_manager.export_import_prompts()
            
            # Add a separator between operations
            console.print("\n" + "─" * console.width + "\n")
    
    except KeyboardInterrupt:
        console.print(f"\n[{NORD_YELLOW}]Operação interrompida pelo usuário[/{NORD_YELLOW}]")
    except Exception as e:
        handle_error("Erro no gerenciador de prompts", e)

if __name__ == "__main__":
    main()