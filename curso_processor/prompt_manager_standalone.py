#!/usr/bin/env python3
"""
Prompt Manager Standalone - Gerenciador de Prompts para Curso Processor
Versão independente que não requer o módulo de credenciais
"""

import os
import json
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown

# Define Nord Theme colors
NORD_BLUE = "bright_blue"
NORD_CYAN = "bright_cyan"
NORD_GREEN = "bright_green"
NORD_YELLOW = "bright_yellow"
NORD_RED = "bright_red"
NORD_DIM = "dim white"

# Create console
console = Console()

def handle_error(message: str, exception: Exception = None):
    """Display error message with Nord Theme styling"""
    error_panel = Panel(
        Text.from_markup(
            f"{message}\n\n" + (f"[{NORD_DIM}]{str(exception)}[/{NORD_DIM}]" if exception else "")
        ),
        title="[bold red]Erro[/bold red]",
        border_style=NORD_RED,
        padding=(1, 2)
    )
    console.print(error_panel)

def create_progress_bar(description: str = "Processando"):
    """Create a progress bar with Nord Theme styling"""
    return Progress(
        TextColumn(f"[{NORD_BLUE}]{description}[/{NORD_BLUE}]"),
        BarColumn(complete_style=NORD_CYAN, finished_style=NORD_GREEN),
        TaskProgressColumn(),
        console=console
    )

class PromptManager:
    """Gerenciador de prompts para o Curso Processor"""
    
    def __init__(self):
        self.console = console
        self.app_dir = Path(os.getcwd())
        self.prompts_dir = self.app_dir / "prompts"
        self.custom_dir = self.prompts_dir / "custom"
        self.versions_dir = self.prompts_dir / "versions"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Load prompt templates
        self.prompt_templates = self.load_prompt_templates()
        
        # Load usage statistics
        self.usage_stats = self._load_usage_stats()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for directory in [self.prompts_dir, self.custom_dir, self.versions_dir]:
            directory.mkdir(exist_ok=True, parents=True)
    
    def _load_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Load prompt usage statistics"""
        stats_file = self.prompts_dir / "usage_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                handle_error(f"Erro ao carregar estatísticas de uso: {str(e)}")
                return {}
        return {}
    
    def _save_usage_stats(self):
        """Save prompt usage statistics"""
        stats_file = self.prompts_dir / "usage_stats.json"
        try:
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump(self.usage_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            handle_error(f"Erro ao salvar estatísticas de uso: {str(e)}")
    
    def _update_usage_stats(self, prompt_name: str, action: str):
        """Update usage statistics for a prompt"""
        if prompt_name not in self.usage_stats:
            self.usage_stats[prompt_name] = {
                "created_at": datetime.datetime.now().isoformat(),
                "last_used": None,
                "use_count": 0,
                "edit_count": 0,
                "test_count": 0,
                "version_count": 0
            }
        
        stats = self.usage_stats[prompt_name]
        stats["last_used"] = datetime.datetime.now().isoformat()
        
        if action == "use":
            stats["use_count"] += 1
        elif action == "edit":
            stats["edit_count"] += 1
        elif action == "test":
            stats["test_count"] += 1
        elif action == "version":
            stats["version_count"] += 1
        
        self._save_usage_stats()
    
    def load_prompt_templates(self) -> Dict[str, str]:
        """Load all prompt templates from the prompts directory"""
        templates = {}
        
        # Load default prompts
        for prompt_file in self.prompts_dir.glob("*.txt"):
            if prompt_file.is_file():
                try:
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        templates[prompt_file.stem] = f.read()
                except Exception as e:
                    handle_error(f"Erro ao carregar prompt {prompt_file.name}", e)
        
        # Load custom prompts
        for prompt_file in self.custom_dir.glob("*.txt"):
            if prompt_file.is_file():
                try:
                    with open(prompt_file, "r", encoding="utf-8") as f:
                        templates[f"custom/{prompt_file.stem}"] = f.read()
                except Exception as e:
                    handle_error(f"Erro ao carregar prompt personalizado {prompt_file.name}", e)
        
        return templates
    
    def display_prompt_list(self):
        """Display a list of available prompts"""
        self.console.print(f"\n[bold {NORD_CYAN}]Prompts Disponíveis:[/bold {NORD_CYAN}]")
        
        # Create table
        table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
        table.add_column("ID", style=NORD_BLUE, width=4)
        table.add_column("Nome", style=NORD_CYAN)
        table.add_column("Tipo", style=NORD_GREEN)
        table.add_column("Última Utilização", style=NORD_YELLOW)
        table.add_column("Usos", style=NORD_DIM, justify="right")
        
        # Add default prompts
        i = 1
        for name in sorted([n for n in self.prompt_templates.keys() if not n.startswith("custom/")]):
            stats = self.usage_stats.get(name, {})
            last_used = stats.get("last_used", "Nunca")
            if last_used and last_used != "Nunca":
                try:
                    last_used = datetime.datetime.fromisoformat(last_used).strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            use_count = stats.get("use_count", 0)
            
            table.add_row(
                str(i),
                name,
                "Padrão",
                last_used,
                str(use_count)
            )
            i += 1
        
        # Add custom prompts
        for name in sorted([n for n in self.prompt_templates.keys() if n.startswith("custom/")]):
            display_name = name.replace("custom/", "")
            stats = self.usage_stats.get(name, {})
            last_used = stats.get("last_used", "Nunca")
            if last_used and last_used != "Nunca":
                try:
                    last_used = datetime.datetime.fromisoformat(last_used).strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            use_count = stats.get("use_count", 0)
            
            table.add_row(
                str(i),
                display_name,
                "Personalizado",
                last_used,
                str(use_count)
            )
            i += 1
        
        self.console.print(table)
    
    def view_prompt(self, prompt_name: str):
        """View a prompt template"""
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt não encontrado: {prompt_name}[/{NORD_RED}]")
            return
        
        content = self.prompt_templates[prompt_name]
        
        # Update usage statistics
        self._update_usage_stats(prompt_name, "use")
        
        # Display prompt
        self.console.print(f"\n[bold {NORD_CYAN}]Prompt: {prompt_name}[/bold {NORD_CYAN}]")
        
        # Create panel with prompt content
        panel = Panel(
            Text(content, style=NORD_DIM),
            title=f"[bold {NORD_BLUE}]{prompt_name}[/bold {NORD_BLUE}]",
            border_style=NORD_CYAN,
            padding=(1, 2),
            width=100
        )
        self.console.print(panel)
        
        # Display variables used in the prompt
        variables = self._extract_variables(content)
        if variables:
            var_table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
            var_table.add_column("Variável", style=NORD_CYAN)
            var_table.add_column("Descrição", style=NORD_DIM)
            
            var_descriptions = {
                "TRANSCRIPTION": "Conteúdo da transcrição",
                "COURSE_NAME": "Nome do curso",
                "FILE_NAME": "Nome do arquivo atual",
                "DURATION": "Duração do áudio",
                "COURSE_CATEGORY": "Categoria do curso (detectada automaticamente)",
                "USER_PROFILE": "Perfil do usuário (ADHD, analítico, etc.)",
                "LANGUAGE": "Idioma do conteúdo",
                "COMPLEXITY_LEVEL": "Nível de complexidade detectado"
            }
            
            for var in variables:
                var_table.add_row(
                    f"{{{{{var}}}}}",
                    var_descriptions.get(var, "Variável personalizada")
                )
            
            self.console.print(f"\n[bold {NORD_CYAN}]Variáveis Utilizadas:[/bold {NORD_CYAN}]")
            self.console.print(var_table)
    
    def _extract_variables(self, content: str) -> List[str]:
        """Extract variables from prompt content"""
        import re
        pattern = r"{{([A-Z_]+)}}"
        return list(set(re.findall(pattern, content)))
    
    def create_custom_prompt(self):
        """Create a new custom prompt"""
        self.console.print(f"\n[bold {NORD_CYAN}]Criar Novo Prompt Personalizado[/bold {NORD_CYAN}]")
        
        # Get prompt name
        prompt_name = Prompt.ask(f"[{NORD_BLUE}]Nome do prompt[/{NORD_BLUE}]")
        if not prompt_name:
            self.console.print(f"[{NORD_RED}]Nome inválido.[/{NORD_RED}]")
            return
        
        # Check if prompt already exists
        file_name = f"{prompt_name.lower().replace(' ', '_')}.txt"
        file_path = self.custom_dir / file_name
        if file_path.exists():
            self.console.print(f"[{NORD_RED}]Um prompt com este nome já existe.[/{NORD_RED}]")
            return
        
        # Get prompt content
        self.console.print(f"\n[{NORD_CYAN}]Digite o conteúdo do prompt (termine com uma linha vazia):[/{NORD_CYAN}]")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        content = "\n".join(lines)
        if not content:
            self.console.print(f"[{NORD_RED}]Conteúdo vazio.[/{NORD_RED}]")
            return
        
        # Save prompt
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Update templates
            self.prompt_templates[f"custom/{prompt_name.lower().replace(' ', '_')}"] = content
            
            # Update usage statistics
            self._update_usage_stats(f"custom/{prompt_name.lower().replace(' ', '_')}", "edit")
            
            self.console.print(f"[{NORD_GREEN}]Prompt personalizado criado com sucesso![/{NORD_GREEN}]")
        except Exception as e:
            handle_error(f"Erro ao salvar prompt personalizado", e)
    
    def edit_prompt(self, prompt_name: str):
        """Edit an existing prompt"""
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt não encontrado: {prompt_name}[/{NORD_RED}]")
            return
        
        # Check if it's a default prompt
        is_custom = prompt_name.startswith("custom/")
        if not is_custom:
            # Create a backup of the default prompt
            self._create_version(prompt_name)
            
            # Warn user about editing default prompt
            self.console.print(f"[{NORD_YELLOW}]Atenção: Você está editando um prompt padrão.[/{NORD_YELLOW}]")
            if not Confirm.ask(f"[{NORD_YELLOW}]Deseja continuar?[/{NORD_YELLOW}]"):
                return
        
        # Get current content
        current_content = self.prompt_templates[prompt_name]
        
        # Get new content
        self.console.print(f"\n[{NORD_CYAN}]Edite o conteúdo do prompt (termine com uma linha vazia):[/{NORD_CYAN}]")
        self.console.print(f"[{NORD_DIM}]Conteúdo atual:[/{NORD_DIM}]")
        print(current_content)
        
        self.console.print(f"\n[{NORD_CYAN}]Novo conteúdo:[/{NORD_CYAN}]")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        new_content = "\n".join(lines)
        if not new_content:
            self.console.print(f"[{NORD_RED}]Conteúdo vazio.[/{NORD_RED}]")
            return
        
        # Save prompt
        try:
            # Determine file path
            if is_custom:
                file_name = prompt_name.replace("custom/", "")
                file_path = self.custom_dir / f"{file_name}.txt"
            else:
                file_path = self.prompts_dir / f"{prompt_name}.txt"
            
            # Create version if content changed
            if current_content != new_content:
                self._create_version(prompt_name)
                
                # Save new content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                # Update templates
                self.prompt_templates[prompt_name] = new_content
                
                # Update usage statistics
                self._update_usage_stats(prompt_name, "edit")
                
                self.console.print(f"[{NORD_GREEN}]Prompt editado com sucesso![/{NORD_GREEN}]")
            else:
                self.console.print(f"[{NORD_YELLOW}]Nenhuma alteração detectada.[/{NORD_YELLOW}]")
        except Exception as e:
            handle_error(f"Erro ao salvar prompt", e)
    
    def _create_version(self, prompt_name: str):
        """Create a version of a prompt"""
        if prompt_name not in self.prompt_templates:
            return
        
        try:
            # Get current content
            content = self.prompt_templates[prompt_name]
            
            # Create version directory
            version_dir = self.versions_dir / prompt_name
            version_dir.mkdir(exist_ok=True, parents=True)
            
            # Generate version file name
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            version_file = version_dir / f"v{timestamp}.txt"
            
            # Save version
            with open(version_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Update usage statistics
            self._update_usage_stats(prompt_name, "version")
            
            return version_file
        except Exception as e:
            handle_error(f"Erro ao criar versão do prompt", e)
            return None
    
    def manage_prompt_versions(self, prompt_name: str):
        """Manage versions of a prompt"""
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt não encontrado: {prompt_name}[/{NORD_RED}]")
            return
        
        # Check if versions exist
        version_dir = self.versions_dir / prompt_name
        if not version_dir.exists() or not list(version_dir.glob("*.txt")):
            self.console.print(f"[{NORD_YELLOW}]Nenhuma versão encontrada para este prompt.[/{NORD_YELLOW}]")
            return
        
        # List versions
        versions = sorted(version_dir.glob("*.txt"), reverse=True)
        
        self.console.print(f"\n[bold {NORD_CYAN}]Versões do Prompt: {prompt_name}[/bold {NORD_CYAN}]")
        
        # Create table
        table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
        table.add_column("ID", style=NORD_BLUE, width=4)
        table.add_column("Versão", style=NORD_CYAN)
        table.add_column("Data", style=NORD_GREEN)
        table.add_column("Hora", style=NORD_YELLOW)
        
        for i, version in enumerate(versions):
            # Extract timestamp from filename
            version_name = version.stem
            if version_name.startswith("v"):
                timestamp = version_name[1:]  # Remove 'v' prefix
                try:
                    dt = datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    date = dt.strftime("%d/%m/%Y")
                    time = dt.strftime("%H:%M:%S")
                except:
                    date = "Desconhecida"
                    time = "Desconhecida"
            else:
                date = "Desconhecida"
                time = "Desconhecida"
            
            table.add_row(
                str(i + 1),
                version_name,
                date,
                time
            )
        
        self.console.print(table)
        
        # Ask which version to view
        version_id = Prompt.ask(
            f"[{NORD_BLUE}]Selecione uma versão para visualizar (ou 0 para voltar)[/{NORD_BLUE}]",
            default="0"
        )
        
        try:
            version_id = int(version_id)
            if version_id == 0:
                return
            
            if 1 <= version_id <= len(versions):
                version_file = versions[version_id - 1]
                
                # Read version content
                with open(version_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Display version
                self.console.print(f"\n[bold {NORD_CYAN}]Versão: {version_file.stem}[/bold {NORD_CYAN}]")
                
                # Create panel with version content
                panel = Panel(
                    Text(content, style=NORD_DIM),
                    title=f"[bold {NORD_BLUE}]{version_file.stem}[/bold {NORD_BLUE}]",
                    border_style=NORD_CYAN,
                    padding=(1, 2),
                    width=100
                )
                self.console.print(panel)
                
                # Ask if user wants to restore this version
                if Confirm.ask(f"[{NORD_YELLOW}]Deseja restaurar esta versão?[/{NORD_YELLOW}]"):
                    self._restore_version(prompt_name, version_file)
            else:
                self.console.print(f"[{NORD_RED}]ID de versão inválido.[/{NORD_RED}]")
        except ValueError:
            self.console.print(f"[{NORD_RED}]ID de versão inválido.[/{NORD_RED}]")
    
    def _restore_version(self, prompt_name: str, version_file: Path):
        """Restore a prompt to a previous version"""
        try:
            # Read version content
            with open(version_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Determine file path
            if prompt_name.startswith("custom/"):
                file_name = prompt_name.replace("custom/", "")
                file_path = self.custom_dir / f"{file_name}.txt"
            else:
                file_path = self.prompts_dir / f"{prompt_name}.txt"
            
            # Create version of current content
            self._create_version(prompt_name)
            
            # Save restored content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Update templates
            self.prompt_templates[prompt_name] = content
            
            # Update usage statistics
            self._update_usage_stats(prompt_name, "edit")
            
            self.console.print(f"[{NORD_GREEN}]Versão restaurada com sucesso![/{NORD_GREEN}]")
        except Exception as e:
            handle_error(f"Erro ao restaurar versão", e)
    
    def test_prompt_effectiveness(self, prompt_name: str):
        """Test the effectiveness of a prompt"""
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt não encontrado: {prompt_name}[/{NORD_RED}]")
            return
        
        self.console.print(f"\n[bold {NORD_CYAN}]Teste de Eficácia do Prompt: {prompt_name}[/bold {NORD_CYAN}]")
        
        # Get sample transcription
        self.console.print(f"\n[{NORD_CYAN}]Selecione uma amostra de transcrição para testar:[/{NORD_CYAN}]")
        
        # Get transcription files
        transcription_dir = Path(os.path.join(os.getcwd(), "data", "transcriptions"))
        if not transcription_dir.exists():
            self.console.print(f"[{NORD_RED}]Diretório de transcrições não encontrado.[/{NORD_RED}]")
            return
        
        # List transcription files
        transcription_files = list(transcription_dir.glob("*.txt"))
        if not transcription_files:
            self.console.print(f"[{NORD_RED}]Nenhuma transcrição encontrada.[/{NORD_RED}]")
            return
        
        # Create table
        table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
        table.add_column("ID", style=NORD_BLUE, width=4)
        table.add_column("Arquivo", style=NORD_CYAN)
        table.add_column("Tamanho", style=NORD_GREEN, justify="right")
        
        for i, file in enumerate(transcription_files):
            table.add_row(
                str(i + 1),
                file.name,
                f"{file.stat().st_size / 1024:.1f} KB"
            )
        
        self.console.print(table)
        
        # Ask which file to use
        file_id = Prompt.ask(
            f"[{NORD_BLUE}]Selecione um arquivo (ou 0 para voltar)[/{NORD_BLUE}]",
            default="0"
        )
        
        try:
            file_id = int(file_id)
            if file_id == 0:
                return
            
            if 1 <= file_id <= len(transcription_files):
                file_path = transcription_files[file_id - 1]
                
                # Read transcription
                with open(file_path, "r", encoding="utf-8") as f:
                    transcription = f.read()
                
                # Get prompt template
                template = self.prompt_templates[prompt_name]
                
                # Replace variables
                prompt = template.replace("{{TRANSCRIPTION}}", transcription)
                prompt = prompt.replace("{{COURSE_NAME}}", "Curso de Teste")
                prompt = prompt.replace("{{FILE_NAME}}", file_path.name)
                prompt = prompt.replace("{{DURATION}}", "10:00")
                prompt = prompt.replace("{{COURSE_CATEGORY}}", "Teste")
                prompt = prompt.replace("{{USER_PROFILE}}", "Teste")
                prompt = prompt.replace("{{LANGUAGE}}", "Português")
                prompt = prompt.replace("{{COMPLEXITY_LEVEL}}", "Intermediário")
                
                # Display prompt
                self.console.print(f"\n[bold {NORD_CYAN}]Prompt Processado:[/bold {NORD_CYAN}]")
                
                # Create panel with prompt content
                panel = Panel(
                    Text(prompt[:1000] + "..." if len(prompt) > 1000 else prompt, style=NORD_DIM),
                    title=f"[bold {NORD_BLUE}]Prompt para Teste[/bold {NORD_BLUE}]",
                    border_style=NORD_CYAN,
                    padding=(1, 2),
                    width=100
                )
                self.console.print(panel)
                
                # Update usage statistics
                self._update_usage_stats(prompt_name, "test")
                
                # Display test results
                self.console.print(f"\n[bold {NORD_GREEN}]Análise de Qualidade do Prompt:[/bold {NORD_GREEN}]")
                
                # Create quality metrics table
                metrics_table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
                metrics_table.add_column("Métrica", style=NORD_CYAN)
                metrics_table.add_column("Valor", style=NORD_GREEN)
                metrics_table.add_column("Avaliação", style=NORD_YELLOW)
                
                # Calculate metrics
                word_count = len(prompt.split())
                char_count = len(prompt)
                avg_word_length = char_count / word_count if word_count > 0 else 0
                
                # Evaluate prompt quality
                clarity_score = min(10, max(1, 10 - (avg_word_length - 5) * 2))
                specificity_score = min(10, max(1, word_count / 100))
                
                metrics_table.add_row(
                    "Contagem de Palavras",
                    str(word_count),
                    "Bom" if 300 <= word_count <= 1000 else "Muito Curto" if word_count < 300 else "Muito Longo"
                )
                metrics_table.add_row(
                    "Tamanho Médio das Palavras",
                    f"{avg_word_length:.1f} caracteres",
                    "Bom" if 4 <= avg_word_length <= 6 else "Muito Simples" if avg_word_length < 4 else "Muito Complexo"
                )
                metrics_table.add_row(
                    "Clareza",
                    f"{clarity_score:.1f}/10",
                    "Excelente" if clarity_score >= 8 else "Bom" if clarity_score >= 6 else "Precisa Melhorar"
                )
                metrics_table.add_row(
                    "Especificidade",
                    f"{specificity_score:.1f}/10",
                    "Excelente" if specificity_score >= 8 else "Bom" if specificity_score >= 6 else "Precisa Melhorar"
                )
                
                self.console.print(metrics_table)
                
                # Display recommendations
                self.console.print(f"\n[bold {NORD_CYAN}]Recomendações:[/bold {NORD_CYAN}]")
                
                recommendations = []
                if word_count < 300:
                    recommendations.append("Adicione mais detalhes e instruções específicas.")
                elif word_count > 1000:
                    recommendations.append("Considere reduzir o tamanho do prompt para melhorar a clareza.")
                
                if avg_word_length < 4:
                    recommendations.append("Use termos mais específicos e técnicos quando apropriado.")
                elif avg_word_length > 6:
                    recommendations.append("Simplifique a linguagem para melhorar a compreensão.")
                
                if "{{" in prompt and "}}" in prompt:
                    recommendations.append("Algumas variáveis não foram substituídas. Verifique o formato das variáveis.")
                
                if not recommendations:
                    recommendations.append("O prompt parece bem estruturado e eficaz.")
                
                for rec in recommendations:
                    self.console.print(f"• [{NORD_YELLOW}]{rec}[/{NORD_YELLOW}]")
            else:
                self.console.print(f"[{NORD_RED}]ID de arquivo inválido.[/{NORD_RED}]")
        except ValueError:
            self.console.print(f"[{NORD_RED}]ID de arquivo inválido.[/{NORD_RED}]")
        except Exception as e:
            handle_error(f"Erro ao testar prompt", e)
    
    def display_usage_statistics(self):
        """Display usage statistics for all prompts"""
        self.console.print(f"\n[bold {NORD_CYAN}]Estatísticas de Uso dos Prompts:[/bold {NORD_CYAN}]")
        
        if not self.usage_stats:
            self.console.print(f"[{NORD_YELLOW}]Nenhuma estatística disponível.[/{NORD_YELLOW}]")
            return
        
        # Create table
        table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
        table.add_column("Prompt", style=NORD_CYAN)
        table.add_column("Criado em", style=NORD_GREEN)
        table.add_column("Última Utilização", style=NORD_YELLOW)
        table.add_column("Usos", style=NORD_DIM, justify="right")
        table.add_column("Edições", style=NORD_DIM, justify="right")
        table.add_column("Testes", style=NORD_DIM, justify="right")
        table.add_column("Versões", style=NORD_DIM, justify="right")
        
        for name, stats in sorted(self.usage_stats.items()):
            # Format dates
            created_at = stats.get("created_at", "Desconhecido")
            if created_at and created_at != "Desconhecido":
                try:
                    created_at = datetime.datetime.fromisoformat(created_at).strftime("%d/%m/%Y")
                except:
                    pass
            
            last_used = stats.get("last_used", "Nunca")
            if last_used and last_used != "Nunca":
                try:
                    last_used = datetime.datetime.fromisoformat(last_used).strftime("%d/%m/%Y %H:%M")
                except:
                    pass
            
            # Get counts
            use_count = stats.get("use_count", 0)
            edit_count = stats.get("edit_count", 0)
            test_count = stats.get("test_count", 0)
            version_count = stats.get("version_count", 0)
            
            # Format display name
            display_name = name
            if name.startswith("custom/"):
                display_name = f"📝 {name.replace('custom/', '')}"
            
            table.add_row(
                display_name,
                created_at,
                last_used,
                str(use_count),
                str(edit_count),
                str(test_count),
                str(version_count)
            )
        
        self.console.print(table)
    
    def export_import_prompts(self):
        """Export or import prompts"""
        self.console.print(f"\n[bold {NORD_CYAN}]Exportar/Importar Prompts[/bold {NORD_CYAN}]")
        
        # Create menu
        menu_panel = Panel(
            Text.from_markup(
                "\n".join([
                    f"[{NORD_BLUE}][1][/{NORD_BLUE}] Exportar Todos os Prompts",
                    f"[{NORD_BLUE}][2][/{NORD_BLUE}] Exportar Prompts Personalizados",
                    f"[{NORD_BLUE}][3][/{NORD_BLUE}] Importar Prompts",
                    f"[{NORD_BLUE}][0][/{NORD_BLUE}] Voltar"
                ])
            ),
            title="[bold]Menu de Exportação/Importação[/bold]",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        self.console.print(menu_panel)
        
        # Get user choice
        choice = Prompt.ask(
            f"[{NORD_BLUE}]Escolha uma opção[/{NORD_BLUE}]",
            choices=["0", "1", "2", "3"],
            default="0"
        )
        
        if choice == "0":
            return
        elif choice == "1":
            self._export_prompts(custom_only=False)
        elif choice == "2":
            self._export_prompts(custom_only=True)
        elif choice == "3":
            self._import_prompts()
    
    def _export_prompts(self, custom_only: bool = False):
        """Export prompts to a zip file"""
        try:
            # Create export directory
            export_dir = self.app_dir / "exports"
            export_dir.mkdir(exist_ok=True)
            
            # Generate export file name
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = export_dir / f"prompts_export_{timestamp}.zip"
            
            # Create progress bar
            with create_progress_bar("Exportando prompts") as progress:
                task = progress.add_task("Exportando...", total=100)
                
                # Create temporary directory
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Copy prompts
                    progress.update(task, advance=20, description="Copiando prompts...")
                    
                    if custom_only:
                        # Copy only custom prompts
                        custom_export_dir = temp_path / "custom"
                        custom_export_dir.mkdir(exist_ok=True)
                        
                        for prompt_file in self.custom_dir.glob("*.txt"):
                            shutil.copy(prompt_file, custom_export_dir)
                    else:
                        # Copy all prompts
                        prompts_export_dir = temp_path / "prompts"
                        prompts_export_dir.mkdir(exist_ok=True)
                        
                        for prompt_file in self.prompts_dir.glob("*.txt"):
                            shutil.copy(prompt_file, prompts_export_dir)
                        
                        # Copy custom prompts
                        custom_export_dir = temp_path / "custom"
                        custom_export_dir.mkdir(exist_ok=True)
                        
                        for prompt_file in self.custom_dir.glob("*.txt"):
                            shutil.copy(prompt_file, custom_export_dir)
                    
                    # Export usage statistics
                    progress.update(task, advance=20, description="Exportando estatísticas...")
                    
                    stats_file = temp_path / "usage_stats.json"
                    with open(stats_file, "w", encoding="utf-8") as f:
                        json.dump(self.usage_stats, f, indent=2, ensure_ascii=False)
                    
                    # Create zip file
                    progress.update(task, advance=40, description="Criando arquivo zip...")
                    
                    import zipfile
                    with zipfile.ZipFile(export_file, "w") as zipf:
                        for file in temp_path.glob("**/*"):
                            if file.is_file():
                                zipf.write(file, file.relative_to(temp_path))
                    
                    progress.update(task, advance=20, description="Concluído!")
            
            self.console.print(f"[{NORD_GREEN}]Prompts exportados com sucesso para: {export_file}[/{NORD_GREEN}]")
        except Exception as e:
            handle_error(f"Erro ao exportar prompts", e)
    
    def _import_prompts(self):
        """Import prompts from a zip file"""
        self.console.print(f"\n[{NORD_CYAN}]Importar Prompts[/{NORD_CYAN}]")
        
        # Get export directory
        export_dir = self.app_dir / "exports"
        if not export_dir.exists():
            self.console.print(f"[{NORD_RED}]Diretório de exportações não encontrado.[/{NORD_RED}]")
            return
        
        # List export files
        export_files = list(export_dir.glob("*.zip"))
        if not export_files:
            self.console.print(f"[{NORD_RED}]Nenhum arquivo de exportação encontrado.[/{NORD_RED}]")
            return
        
        # Create table
        table = Table(show_header=True, header_style=f"bold {NORD_BLUE}")
        table.add_column("ID", style=NORD_BLUE, width=4)
        table.add_column("Arquivo", style=NORD_CYAN)
        table.add_column("Tamanho", style=NORD_GREEN, justify="right")
        table.add_column("Data", style=NORD_YELLOW)
        
        for i, file in enumerate(sorted(export_files, key=lambda f: f.stat().st_mtime, reverse=True)):
            # Get file date
            file_date = datetime.datetime.fromtimestamp(file.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            
            table.add_row(
                str(i + 1),
                file.name,
                f"{file.stat().st_size / 1024:.1f} KB",
                file_date
            )
        
        self.console.print(table)
        
        # Ask which file to import
        file_id = Prompt.ask(
            f"[{NORD_BLUE}]Selecione um arquivo para importar (ou 0 para voltar)[/{NORD_BLUE}]",
            default="0"
        )
        
        try:
            file_id = int(file_id)
            if file_id == 0:
                return
            
            if 1 <= file_id <= len(export_files):
                import_file = export_files[file_id - 1]
                
                # Ask for import mode
                self.console.print(f"\n[{NORD_CYAN}]Modo de Importação:[/{NORD_CYAN}]")
                mode = Prompt.ask(
                    f"[{NORD_BLUE}]Escolha o modo de importação[/{NORD_BLUE}]",
                    choices=["1", "2", "3"],
                    default="1"
                )
                
                # Create progress bar
                with create_progress_bar("Importando prompts") as progress:
                    task = progress.add_task("Importando...", total=100)
                    
                    # Create temporary directory
                    import tempfile
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        
                        # Extract zip file
                        progress.update(task, advance=20, description="Extraindo arquivo zip...")
                        
                        import zipfile
                        with zipfile.ZipFile(import_file, "r") as zipf:
                            zipf.extractall(temp_path)
                        
                        # Import prompts
                        progress.update(task, advance=20, description="Importando prompts...")
                        
                        # Import custom prompts
                        custom_import_dir = temp_path / "custom"
                        if custom_import_dir.exists():
                            for prompt_file in custom_import_dir.glob("*.txt"):
                                if mode == "1":  # Import all
                                    shutil.copy(prompt_file, self.custom_dir)
                                elif mode == "2":  # Import only new
                                    if not (self.custom_dir / prompt_file.name).exists():
                                        shutil.copy(prompt_file, self.custom_dir)
                                elif mode == "3":  # Import and overwrite
                                    shutil.copy(prompt_file, self.custom_dir)
                        
                        # Import default prompts
                        prompts_import_dir = temp_path / "prompts"
                        if prompts_import_dir.exists() and mode == "3":  # Only overwrite in mode 3
                            for prompt_file in prompts_import_dir.glob("*.txt"):
                                shutil.copy(prompt_file, self.prompts_dir)
                        
                        # Import usage statistics
                        progress.update(task, advance=40, description="Importando estatísticas...")
                        
                        stats_file = temp_path / "usage_stats.json"
                        if stats_file.exists():
                            with open(stats_file, "r", encoding="utf-8") as f:
                                imported_stats = json.load(f)
                            
                            # Merge statistics
                            if mode == "1":  # Import all
                                self.usage_stats.update(imported_stats)
                            elif mode == "2":  # Import only new
                                for name, stats in imported_stats.items():
                                    if name not in self.usage_stats:
                                        self.usage_stats[name] = stats
                            elif mode == "3":  # Import and overwrite
                                self.usage_stats.update(imported_stats)
                            
                            # Save merged statistics
                            self._save_usage_stats()
                        
                        progress.update(task, advance=20, description="Concluído!")
                
                # Reload prompt templates
                self.prompt_templates = self.load_prompt_templates()
                
                self.console.print(f"[{NORD_GREEN}]Prompts importados com sucesso![/{NORD_GREEN}]")
            else:
                self.console.print(f"[{NORD_RED}]ID de arquivo inválido.[/{NORD_RED}]")
        except ValueError:
            self.console.print(f"[{NORD_RED}]ID de arquivo inválido.[/{NORD_RED}]")
        except Exception as e:
            handle_error(f"Erro ao importar prompts", e)
    
    def delete_prompt(self, prompt_name: str):
        """Delete a prompt"""
        if prompt_name not in self.prompt_templates:
            self.console.print(f"[{NORD_RED}]Prompt não encontrado: {prompt_name}[/{NORD_RED}]")
            return
        
        # Check if it's a default prompt
        is_custom = prompt_name.startswith("custom/")
        if not is_custom:
            self.console.print(f"[{NORD_RED}]Não é possível excluir prompts padrão.[/{NORD_RED}]")
            return
        
        # Confirm deletion
        if not Confirm.ask(f"[{NORD_RED}]Tem certeza que deseja excluir o prompt '{prompt_name}'?[/{NORD_RED}]"):
            return
        
        try:
            # Create backup
            self._create_version(prompt_name)
            
            # Delete prompt file
            file_name = prompt_name.replace("custom/", "")
            file_path = self.custom_dir / f"{file_name}.txt"
            file_path.unlink()
            
            # Remove from templates
            del self.prompt_templates[prompt_name]
            
            self.console.print(f"[{NORD_GREEN}]Prompt excluído com sucesso![/{NORD_GREEN}]")
        except Exception as e:
            handle_error(f"Erro ao excluir prompt", e)

def display_ascii_art():
    """Display ASCII art for Prompt Manager"""
    ascii_art = """
    ██████╗ ██████╗  ██████╗ ███╗   ███╗██████╗ ████████╗
    ██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝
    ██████╔╝██████╔╝██║   ██║██╔████╔██║██████╔╝   ██║   
    ██╔═══╝ ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝    ██║   
    ██║     ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║        ██║   
    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝        ╚═╝   
    ███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
    ████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
    ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
    ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
    ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
    """
    console.print(f"[{NORD_CYAN}]{ascii_art}[/{NORD_CYAN}]")

def display_menu(prompt_manager):
    """Display the main menu"""
    menu_panel = Panel(
        Text.from_markup(
            "\n".join([
                f"[{NORD_BLUE}][1][/{NORD_BLUE}] 📋 Listar Prompts",
                f"[{NORD_BLUE}][2][/{NORD_BLUE}] 👁️ Visualizar Prompt",
                f"[{NORD_BLUE}][3][/{NORD_BLUE}] ✏️ Editar Prompt",
                f"[{NORD_BLUE}][4][/{NORD_BLUE}] ➕ Criar Prompt Personalizado",
                f"[{NORD_BLUE}][5][/{NORD_BLUE}] 🗑️ Excluir Prompt",
                f"[{NORD_BLUE}][6][/{NORD_BLUE}] 🔄 Gerenciar Versões",
                f"[{NORD_BLUE}][7][/{NORD_BLUE}] 🧪 Testar Eficácia do Prompt",
                f"[{NORD_BLUE}][8][/{NORD_BLUE}] 📊 Estatísticas de Uso",
                f"[{NORD_BLUE}][9][/{NORD_BLUE}] 📤 Exportar/Importar Prompts",
                f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
            ])
        ),
        title="[bold]Menu do Gerenciador de Prompts[/bold]",
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    console.print(menu_panel)

def select_prompt(prompt_manager):
    """Select a prompt from the list"""
    prompt_manager.display_prompt_list()
    
    prompt_names = list(prompt_manager.prompt_templates.keys())
    if not prompt_names:
        console.print(f"[{NORD_RED}]Nenhum prompt disponível.[/{NORD_RED}]")
        return None
    
    prompt_id = Prompt.ask(
        f"[{NORD_BLUE}]Selecione um prompt (ou 0 para voltar)[/{NORD_BLUE}]",
        default="0"
    )
    
    try:
        prompt_id = int(prompt_id)
        if prompt_id == 0:
            return None
        
        if 1 <= prompt_id <= len(prompt_names):
            return prompt_names[prompt_id - 1]
        else:
            console.print(f"[{NORD_RED}]ID de prompt inválido.[/{NORD_RED}]")
            return None
    except ValueError:
        console.print(f"[{NORD_RED}]ID de prompt inválido.[/{NORD_RED}]")
        return None

def main():
    """Main function"""
    try:
        # Display ASCII art
        display_ascii_art()
        
        # Create prompt manager
        prompt_manager = PromptManager()
        
        while True:
            # Display menu
            display_menu(prompt_manager)
            
            # Get user choice
            choice = Prompt.ask(
                f"[{NORD_BLUE}]Escolha uma opção[/{NORD_BLUE}]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
                default="0"
            )
            
            if choice == "0":
                break
            elif choice == "1":
                prompt_manager.display_prompt_list()
            elif choice == "2":
                prompt_name = select_prompt(prompt_manager)
                if prompt_name:
                    prompt_manager.view_prompt(prompt_name)
            elif choice == "3":
                prompt_name = select_prompt(prompt_manager)
                if prompt_name:
                    prompt_manager.edit_prompt(prompt_name)
            elif choice == "4":
                prompt_manager.create_custom_prompt()
            elif choice == "5":
                prompt_name = select_prompt(prompt_manager)
                if prompt_name:
                    prompt_manager.delete_prompt(prompt_name)
            elif choice == "6":
                prompt_name = select_prompt(prompt_manager)
                if prompt_name:
                    prompt_manager.manage_prompt_versions(prompt_name)
            elif choice == "7":
                prompt_name = select_prompt(prompt_manager)
                if prompt_name:
                    prompt_manager.test_prompt_effectiveness(prompt_name)
            elif choice == "8":
                prompt_manager.display_usage_statistics()
            elif choice == "9":
                prompt_manager.export_import_prompts()
            
            # Add a separator between operations
            console.print("\n" + "─" * console.width + "\n")
    
    except KeyboardInterrupt:
        console.print(f"\n[{NORD_YELLOW}]Operação interrompida pelo usuário[/{NORD_YELLOW}]")
    except Exception as e:
        handle_error("Erro inesperado", e)

if __name__ == "__main__":
    main()