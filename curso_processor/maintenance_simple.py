#!/usr/bin/env python3
"""
Simplified version of the maintenance.py file for testing
"""

import os
import sys
import json
import time
import shutil
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID

# Initialize console
console = Console()

# Define Nord Theme colors
NORD_BLUE = "bright_blue"
NORD_CYAN = "bright_cyan"
NORD_GREEN = "bright_green"
NORD_YELLOW = "bright_yellow"
NORD_RED = "bright_red"
NORD_DIM = "dim white"

class SystemMaintenance:
    """System maintenance class"""
    
    def __init__(self):
        """Initialize system maintenance"""
        # Define directories
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, "data")
        self.temp_dir = os.path.join(self.base_dir, "temp")
        self.logs_dir = os.path.join(self.base_dir, "logs")
        self.cache_dir = os.path.join(self.base_dir, "cache")
        self.backups_dir = os.path.join(self.base_dir, "backups")
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.temp_dir, self.logs_dir, self.cache_dir, self.backups_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def cleanup_temp_files(self) -> float:
        """
        Clean up temporary files
        
        Returns:
            float: Space freed in MB
        """
        console.print(f"[{NORD_CYAN}]Limpando arquivos temporários...[/{NORD_CYAN}]")
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add task
            task = progress.add_task("[cyan]Limpando...", total=100)
            
            # Get initial size
            initial_size = self.get_directory_size(self.temp_dir)
            
            # Clean up temporary files
            for root, dirs, files in os.walk(self.temp_dir):
                # Update progress
                progress.update(task, advance=10)
                
                # Delete files
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        console.print(f"[{NORD_RED}]Erro ao excluir {file_path}: {str(e)}[/{NORD_RED}]")
                
                # Update progress
                progress.update(task, advance=40)
                
                # Delete empty directories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except Exception as e:
                        console.print(f"[{NORD_RED}]Erro ao excluir diretório {dir_path}: {str(e)}[/{NORD_RED}]")
                
                # Update progress
                progress.update(task, advance=50)
            
            # Get final size
            final_size = self.get_directory_size(self.temp_dir)
            
            # Calculate space freed
            space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
            
            # Complete progress
            progress.update(task, completed=100)
        
        console.print(f"[{NORD_GREEN}]✅ Limpeza concluída! Espaço liberado: {space_freed:.2f} MB[/{NORD_GREEN}]")
        
        return space_freed
    
    def get_directory_size(self, directory: str) -> float:
        """
        Get directory size
        
        Args:
            directory: Directory path
            
        Returns:
            float: Directory size in bytes
        """
        total_size = 0
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass
        
        return total_size
    
    def format_size(self, size_bytes: float) -> str:
        """
        Format size
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size
        """
        # Convert to appropriate unit
        if size_bytes < 1024:
            return f"{size_bytes:.2f} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def validate_system_integrity(self) -> Dict[str, Any]:
        """
        Validate system integrity
        
        Returns:
            Dict: Health report
        """
        console.print(f"[{NORD_CYAN}]Validando integridade do sistema...[/{NORD_CYAN}]")
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add task
            task = progress.add_task("[cyan]Validando...", total=100)
            
            # Validate directories
            progress.update(task, advance=20, description="[cyan]Validando diretórios...")
            directories_valid = self.validate_directories()
            
            # Validate files
            progress.update(task, advance=20, description="[cyan]Validando arquivos...")
            files_valid = self.validate_files()
            
            # Validate config files
            progress.update(task, advance=20, description="[cyan]Validando arquivos de configuração...")
            config_valid = self.validate_config_files()
            
            # Validate database
            progress.update(task, advance=20, description="[cyan]Validando banco de dados...")
            database_valid = self.validate_database()
            
            # Validate API credentials
            progress.update(task, advance=20, description="[cyan]Validando credenciais de API...")
            api_valid = self.validate_api_credentials()
            
            # Complete progress
            progress.update(task, completed=100)
        
        # Create health report
        validations = {
            "Diretórios": directories_valid,
            "Arquivos": files_valid,
            "Configurações": config_valid,
            "Banco de Dados": database_valid,
            "APIs": api_valid
        }
        
        # Count issues
        issues = []
        for validation_name, validation in validations.items():
            if not validation["is_valid"]:
                for issue in validation["issues"]:
                    issues.append({
                        "validation": validation_name,
                        "description": issue
                    })
        
        # Determine system health
        if len(issues) == 0:
            system_health = "SAUDÁVEL"
        elif len(issues) <= 3:
            system_health = "ATENÇÃO"
        else:
            system_health = "CRÍTICO"
        
        # Create recommendations
        recommendations = []
        if not directories_valid["is_valid"]:
            recommendations.append("Executar reparo de diretórios")
        if not files_valid["is_valid"]:
            recommendations.append("Executar reparo de arquivos")
        if not config_valid["is_valid"]:
            recommendations.append("Restaurar configurações padrão")
        if not database_valid["is_valid"]:
            recommendations.append("Reparar banco de dados")
        if not api_valid["is_valid"]:
            recommendations.append("Configurar credenciais de API")
        
        # Create health report
        health_report = {
            "system_health": system_health,
            "validations": {
                "Diretórios": directories_valid,
                "Arquivos": files_valid,
                "Configurações": config_valid,
                "Banco de Dados": database_valid,
                "APIs": api_valid
            },
            "issues": issues,
            "recommendations": recommendations
        }
        
        # Display health report
        self.display_health_report(health_report)
        
        return health_report
    
    def validate_directories(self) -> Dict[str, Any]:
        """
        Validate directories
        
        Returns:
            Dict: Validation result
        """
        issues = []
        
        # Check if directories exist
        directories = [
            self.data_dir,
            self.temp_dir,
            self.logs_dir,
            self.cache_dir,
            self.backups_dir
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                issues.append(f"Diretório não encontrado: {directory}")
            elif not os.path.isdir(directory):
                issues.append(f"Caminho não é um diretório: {directory}")
            elif not os.access(directory, os.R_OK | os.W_OK):
                issues.append(f"Diretório sem permissão de leitura/escrita: {directory}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_files(self) -> Dict[str, Any]:
        """
        Validate files
        
        Returns:
            Dict: Validation result
        """
        issues = []
        
        # Check if required files exist
        required_files = [
            os.path.join(self.data_dir, "settings.json"),
            os.path.join(self.data_dir, "processed_courses.json")
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                issues.append(f"Arquivo não encontrado: {file_path}")
            elif not os.path.isfile(file_path):
                issues.append(f"Caminho não é um arquivo: {file_path}")
            elif not os.access(file_path, os.R_OK | os.W_OK):
                issues.append(f"Arquivo sem permissão de leitura/escrita: {file_path}")
            elif os.path.getsize(file_path) == 0:
                issues.append(f"Arquivo vazio: {file_path}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_config_files(self) -> Dict[str, Any]:
        """
        Validate configuration files
        
        Returns:
            Dict: Validation result
        """
        issues = []
        
        # Check if settings.json is valid
        settings_file = os.path.join(self.data_dir, "settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                
                # Check if settings has required keys
                required_keys = ["paths", "language", "tts_settings", "ai_settings"]
                for key in required_keys:
                    if key not in settings:
                        issues.append(f"Configuração ausente: {key}")
            except json.JSONDecodeError:
                issues.append(f"Arquivo de configuração inválido: {settings_file}")
            except Exception as e:
                issues.append(f"Erro ao ler arquivo de configuração: {str(e)}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_database(self) -> Dict[str, Any]:
        """
        Validate database
        
        Returns:
            Dict: Validation result
        """
        issues = []
        
        # Check if processed_courses.json is valid
        courses_file = os.path.join(self.data_dir, "processed_courses.json")
        if os.path.exists(courses_file):
            try:
                with open(courses_file, "r") as f:
                    courses = json.load(f)
                
                # Check if courses is a list
                if not isinstance(courses, list):
                    issues.append(f"Formato de banco de dados inválido: {courses_file}")
            except json.JSONDecodeError:
                issues.append(f"Arquivo de banco de dados inválido: {courses_file}")
            except Exception as e:
                issues.append(f"Erro ao ler arquivo de banco de dados: {str(e)}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
    def validate_api_credentials(self) -> Dict[str, Any]:
        """
        Validate API credentials
        
        Returns:
            Dict: Validation result
        """
        issues = []
        
        # Simulate API validation
        apis = [
            {"name": "OpenAI", "configured": True, "status": "valid"},
            {"name": "Anthropic", "configured": False, "status": "not_configured"},
            {"name": "Google Drive", "configured": True, "status": "valid"},
            {"name": "GitHub", "configured": True, "status": "invalid"}
        ]
        
        # Check if APIs are configured
        for api in apis:
            if not api["configured"]:
                issues.append(f"API não configurada: {api['name']}")
            elif api["status"] != "valid":
                issues.append(f"API inválida: {api['name']} ({api['status']})")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues
        }
    
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
    
    def optimize_storage(self):
        """
        Optimize storage usage
        """
        console.print(f"[{NORD_CYAN}]Otimizando armazenamento...[/{NORD_CYAN}]")
        
        # Get initial sizes
        temp_initial_size = self.get_directory_size(self.temp_dir)
        logs_initial_size = self.get_directory_size(self.logs_dir)
        data_initial_size = self.get_directory_size(self.data_dir)
        cache_initial_size = self.get_directory_size(self.cache_dir)
        backups_initial_size = self.get_directory_size(self.backups_dir)
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add task
            task = progress.add_task("[cyan]Otimizando...", total=100)
            
            # Clean up temporary files
            progress.update(task, advance=20, description="[cyan]Limpando arquivos temporários...")
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
            
            # Clean up log files
            progress.update(task, advance=20, description="[cyan]Limpando arquivos de log...")
            for root, dirs, files in os.walk(self.logs_dir):
                for file in files:
                    if file.endswith(".log"):
                        file_path = os.path.join(root, file)
                        try:
                            # Check if file is older than 30 days
                            if os.path.getmtime(file_path) < time.time() - 30 * 24 * 60 * 60:
                                os.remove(file_path)
                        except Exception:
                            pass
            
            # Optimize database files
            progress.update(task, advance=20, description="[cyan]Otimizando banco de dados...")
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith(".json"):
                        file_path = os.path.join(root, file)
                        try:
                            # Read file
                            with open(file_path, "r") as f:
                                data = json.load(f)
                            
                            # Write file with minimal formatting
                            with open(file_path, "w") as f:
                                json.dump(data, f, separators=(",", ":"))
                        except Exception:
                            pass
            
            # Clean up cache files
            progress.update(task, advance=20, description="[cyan]Limpando arquivos de cache...")
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file is older than 7 days
                        if os.path.getmtime(file_path) < time.time() - 7 * 24 * 60 * 60:
                            os.remove(file_path)
                    except Exception:
                        pass
            
            # Remove old backups
            progress.update(task, advance=20, description="[cyan]Removendo backups antigos...")
            for root, dirs, files in os.walk(self.backups_dir):
                for file in files:
                    if file.endswith(".bak") or file.endswith(".backup"):
                        file_path = os.path.join(root, file)
                        try:
                            # Check if file is older than 90 days
                            if os.path.getmtime(file_path) < time.time() - 90 * 24 * 60 * 60:
                                os.remove(file_path)
                        except Exception:
                            pass
            
            # Complete progress
            progress.update(task, completed=100)
        
        # Get final sizes
        temp_final_size = self.get_directory_size(self.temp_dir)
        logs_final_size = self.get_directory_size(self.logs_dir)
        data_final_size = self.get_directory_size(self.data_dir)
        cache_final_size = self.get_directory_size(self.cache_dir)
        backups_final_size = self.get_directory_size(self.backups_dir)
        
        # Calculate space freed
        temp_space_freed = (temp_initial_size - temp_final_size) / (1024 * 1024)  # Convert to MB
        log_space_freed = (logs_initial_size - logs_final_size) / (1024 * 1024)  # Convert to MB
        db_space_freed = (data_initial_size - data_final_size) / (1024 * 1024)  # Convert to MB
        cache_space_freed = (cache_initial_size - cache_final_size) / (1024 * 1024)  # Convert to MB
        backup_space_freed = (backups_initial_size - backups_final_size) / (1024 * 1024)  # Convert to MB
        
        # Calculate total space freed
        total_space_freed = temp_space_freed + log_space_freed + db_space_freed + cache_space_freed + backup_space_freed
        
        # Create report
        report = [
            f"[{NORD_GREEN}]✅ Otimização concluída![/{NORD_GREEN}]",
            f"",
            f"[{NORD_CYAN}]📊 Relatório de Otimização:[/{NORD_CYAN}]",
            f"",
            f"• Arquivos temporários: {temp_space_freed:.2f} MB",
            f"• Arquivos de log: {log_space_freed:.2f} MB",
            f"• Banco de dados: {db_space_freed:.2f} MB",
            f"• Arquivos de cache: {cache_space_freed:.2f} MB",
            f"• Backups antigos: {backup_space_freed:.2f} MB",
            f"",
            f"[{NORD_GREEN}]Total de espaço liberado: {total_space_freed:.2f} MB[/{NORD_GREEN}]"
        ]
        
        # Create panel
        panel = Panel(
            Text.from_markup("\n".join(report)),
            title="Relatório de Otimização",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        
        console.print(panel)
    
    def _cleanup_log_files(self) -> float:
        """
        Clean up log files
        
        Returns:
            float: Space freed in MB
        """
        # Get initial size
        initial_size = self.get_directory_size(self.logs_dir)
        
        # Clean up log files
        for root, dirs, files in os.walk(self.logs_dir):
            for file in files:
                if file.endswith(".log"):
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file is older than 30 days
                        if os.path.getmtime(file_path) < time.time() - 30 * 24 * 60 * 60:
                            os.remove(file_path)
                    except Exception:
                        pass
        
        # Get final size
        final_size = self.get_directory_size(self.logs_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        return space_freed
    
    def _optimize_database_files(self) -> float:
        """
        Optimize database files
        
        Returns:
            float: Space freed in MB
        """
        # Get initial size
        initial_size = self.get_directory_size(self.data_dir)
        
        # Optimize database files
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        # Read file
                        with open(file_path, "r") as f:
                            data = json.load(f)
                        
                        # Write file with minimal formatting
                        with open(file_path, "w") as f:
                            json.dump(data, f, separators=(",", ":"))
                    except Exception:
                        pass
        
        # Get final size
        final_size = self.get_directory_size(self.data_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        return space_freed
    
    def _cleanup_cache_files(self) -> float:
        """
        Clean up cache files
        
        Returns:
            float: Space freed in MB
        """
        # Get initial size
        initial_size = self.get_directory_size(self.cache_dir)
        
        # Clean up cache files
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Check if file is older than 7 days
                    if os.path.getmtime(file_path) < time.time() - 7 * 24 * 60 * 60:
                        os.remove(file_path)
                except Exception:
                    pass
        
        # Get final size
        final_size = self.get_directory_size(self.cache_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        return space_freed
    
    def _remove_old_backups(self) -> float:
        """
        Remove old backups
        
        Returns:
            float: Space freed in MB
        """
        # Get initial size
        initial_size = self.get_directory_size(self.backups_dir)
        
        # Clean up backup files
        for root, dirs, files in os.walk(self.backups_dir):
            for file in files:
                if file.endswith(".bak") or file.endswith(".backup"):
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file is older than 90 days
                        if os.path.getmtime(file_path) < time.time() - 90 * 24 * 60 * 60:
                            os.remove(file_path)
                    except Exception:
                        pass
        
        # Get final size
        final_size = self.get_directory_size(self.backups_dir)
        
        # Calculate space freed
        space_freed = (initial_size - final_size) / (1024 * 1024)  # Convert to MB
        
        return space_freed
    
    def comprehensive_cleanup(self):
        """
        Perform comprehensive cleanup
        """
        console.print(f"[{NORD_CYAN}]Realizando limpeza completa...[/{NORD_CYAN}]")
        
        # Get initial sizes
        temp_initial_size = self.get_directory_size(self.temp_dir)
        logs_initial_size = self.get_directory_size(self.logs_dir)
        data_initial_size = self.get_directory_size(self.data_dir)
        cache_initial_size = self.get_directory_size(self.cache_dir)
        backups_initial_size = self.get_directory_size(self.backups_dir)
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add task
            task = progress.add_task("[cyan]Limpando...", total=100)
            
            # Clean up temporary files
            progress.update(task, advance=20, description="[cyan]Limpando arquivos temporários...")
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
            
            # Clean up log files
            progress.update(task, advance=20, description="[cyan]Limpando arquivos de log...")
            for root, dirs, files in os.walk(self.logs_dir):
                for file in files:
                    if file.endswith(".log"):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
            
            # Clean up cache files
            progress.update(task, advance=20, description="[cyan]Limpando arquivos de cache...")
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
            
            # Remove old backups
            progress.update(task, advance=20, description="[cyan]Removendo backups antigos...")
            for root, dirs, files in os.walk(self.backups_dir):
                for file in files:
                    if file.endswith(".bak") or file.endswith(".backup"):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
            
            # Optimize database files
            progress.update(task, advance=20, description="[cyan]Otimizando banco de dados...")
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith(".json"):
                        file_path = os.path.join(root, file)
                        try:
                            # Read file
                            with open(file_path, "r") as f:
                                data = json.load(f)
                            
                            # Write file with minimal formatting
                            with open(file_path, "w") as f:
                                json.dump(data, f, separators=(",", ":"))
                        except Exception:
                            pass
            
            # Complete progress
            progress.update(task, completed=100)
        
        # Get final sizes
        temp_final_size = self.get_directory_size(self.temp_dir)
        logs_final_size = self.get_directory_size(self.logs_dir)
        data_final_size = self.get_directory_size(self.data_dir)
        cache_final_size = self.get_directory_size(self.cache_dir)
        backups_final_size = self.get_directory_size(self.backups_dir)
        
        # Calculate space freed
        temp_space_freed = (temp_initial_size - temp_final_size) / (1024 * 1024)  # Convert to MB
        log_space_freed = (logs_initial_size - logs_final_size) / (1024 * 1024)  # Convert to MB
        db_space_freed = (data_initial_size - data_final_size) / (1024 * 1024)  # Convert to MB
        cache_space_freed = (cache_initial_size - cache_final_size) / (1024 * 1024)  # Convert to MB
        backup_space_freed = (backups_initial_size - backups_final_size) / (1024 * 1024)  # Convert to MB
        
        # Calculate total space freed
        total_space_freed = temp_space_freed + log_space_freed + db_space_freed + cache_space_freed + backup_space_freed
        
        console.print(f"[{NORD_GREEN}]✅ Limpeza completa concluída![/{NORD_GREEN}]")
    
    def auto_repair_system(self):
        """
        Auto-repair system
        """
        console.print(f"[{NORD_CYAN}]Reparando sistema automaticamente...[/{NORD_CYAN}]")
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            # Add task
            task = progress.add_task("[cyan]Reparando...", total=100)
            
            # Repair directories
            progress.update(task, advance=20, description="[cyan]Reparando diretórios...")
            self._repair_directories()
            
            # Repair files
            progress.update(task, advance=20, description="[cyan]Reparando arquivos...")
            self._repair_files()
            
            # Repair config files
            progress.update(task, advance=20, description="[cyan]Reparando arquivos de configuração...")
            self._repair_config_files()
            
            # Repair database
            progress.update(task, advance=20, description="[cyan]Reparando banco de dados...")
            self._repair_database()
            
            # Complete progress
            progress.update(task, completed=100)
        
        # Validate system integrity
        health_report = self.validate_system_integrity()
        
        # Check if system is healthy
        if health_report["system_health"] == "SAUDÁVEL":
            console.print(f"[{NORD_GREEN}]✅ Sistema reparado com sucesso![/{NORD_GREEN}]")
        else:
            console.print(f"[{NORD_YELLOW}]⚠️ Sistema parcialmente reparado. Alguns problemas persistem.[/{NORD_YELLOW}]")
    
    def _repair_directories(self):
        """
        Repair directories
        """
        # Create directories if they don't exist
        for directory in [self.data_dir, self.temp_dir, self.logs_dir, self.cache_dir, self.backups_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def _repair_files(self):
        """
        Repair files
        """
        # Create required files if they don't exist
        required_files = [
            os.path.join(self.data_dir, "settings.json"),
            os.path.join(self.data_dir, "processed_courses.json")
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                # Create file with default content
                if file_path.endswith("settings.json"):
                    with open(file_path, "w") as f:
                        json.dump({
                            "paths": {
                                "work_dir": os.path.join(self.base_dir, "work"),
                                "github_dir": os.path.join(self.base_dir, "github"),
                                "xml_dir": os.path.join(self.base_dir, "xml")
                            },
                            "language": "pt-BR",
                            "tts_settings": {
                                "voice": "pt-BR-Standard-A",
                                "rate": 1.0,
                                "pitch": 0.0
                            },
                            "ai_settings": {
                                "model": "gpt-4",
                                "temperature": 0.7,
                                "max_tokens": 4000
                            }
                        }, f, indent=4)
                elif file_path.endswith("processed_courses.json"):
                    with open(file_path, "w") as f:
                        json.dump([], f, indent=4)
    
    def _repair_config_files(self):
        """
        Repair configuration files
        """
        # Repair settings.json
        settings_file = os.path.join(self.data_dir, "settings.json")
        if os.path.exists(settings_file):
            try:
                # Try to read settings
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                
                # Check if settings has required keys
                required_keys = ["paths", "language", "tts_settings", "ai_settings"]
                for key in required_keys:
                    if key not in settings:
                        # Add missing key
                        if key == "paths":
                            settings["paths"] = {
                                "work_dir": os.path.join(self.base_dir, "work"),
                                "github_dir": os.path.join(self.base_dir, "github"),
                                "xml_dir": os.path.join(self.base_dir, "xml")
                            }
                        elif key == "language":
                            settings["language"] = "pt-BR"
                        elif key == "tts_settings":
                            settings["tts_settings"] = {
                                "voice": "pt-BR-Standard-A",
                                "rate": 1.0,
                                "pitch": 0.0
                            }
                        elif key == "ai_settings":
                            settings["ai_settings"] = {
                                "model": "gpt-4",
                                "temperature": 0.7,
                                "max_tokens": 4000
                            }
                
                # Write settings
                with open(settings_file, "w") as f:
                    json.dump(settings, f, indent=4)
            except Exception:
                # Create new settings file
                with open(settings_file, "w") as f:
                    json.dump({
                        "paths": {
                            "work_dir": os.path.join(self.base_dir, "work"),
                            "github_dir": os.path.join(self.base_dir, "github"),
                            "xml_dir": os.path.join(self.base_dir, "xml")
                        },
                        "language": "pt-BR",
                        "tts_settings": {
                            "voice": "pt-BR-Standard-A",
                            "rate": 1.0,
                            "pitch": 0.0
                        },
                        "ai_settings": {
                            "model": "gpt-4",
                            "temperature": 0.7,
                            "max_tokens": 4000
                        }
                    }, f, indent=4)
    
    def _repair_database(self):
        """
        Repair database
        """
        # Repair processed_courses.json
        courses_file = os.path.join(self.data_dir, "processed_courses.json")
        if os.path.exists(courses_file):
            try:
                # Try to read courses
                with open(courses_file, "r") as f:
                    courses = json.load(f)
                
                # Check if courses is a list
                if not isinstance(courses, list):
                    # Create new courses file
                    with open(courses_file, "w") as f:
                        json.dump([], f, indent=4)
            except Exception:
                # Create new courses file
                with open(courses_file, "w") as f:
                    json.dump([], f, indent=4)

def display_menu():
    """Display maintenance menu"""
    menu_items = [
        f"[{NORD_BLUE}][1][/{NORD_BLUE}] 🧹 Limpar Arquivos Temporários",
        f"[{NORD_BLUE}][2][/{NORD_BLUE}] 🔍 Validar Integridade do Sistema",
        f"[{NORD_BLUE}][3][/{NORD_BLUE}] 📊 Otimizar Armazenamento",
        f"[{NORD_BLUE}][4][/{NORD_BLUE}] 🧼 Limpeza Completa",
        f"[{NORD_BLUE}][5][/{NORD_BLUE}] 🔧 Reparar Sistema Automaticamente",
        f"[{NORD_BLUE}][0][/{NORD_BLUE}] ← Voltar"
    ]
    
    # Create menu panel
    panel = Panel(
        Text.from_markup("\n".join(menu_items)),
        title="Menu de Manutenção",
        border_style=NORD_CYAN,
        padding=(1, 2)
    )
    
    console.print(panel)

def main():
    """Main function"""
    try:
        # Create system maintenance
        system = SystemMaintenance()
        
        # Create panel
        panel = Panel(
            Text.from_markup(f"[{NORD_CYAN}]Sistema de Manutenção[/{NORD_CYAN}]\n\n[{NORD_DIM}]Utilize este sistema para manter o Curso Processor funcionando corretamente.[/{NORD_DIM}]"),
            title="Manutenção do Sistema",
            border_style=NORD_CYAN,
            padding=(1, 2)
        )
        
        console.print(panel)
        
        while True:
            # Display menu
            display_menu()
            
            # Get user choice
            choice = Prompt.ask("[bold]Escolha uma opção", choices=["0", "1", "2", "3", "4", "5"], default="0")
            
            if choice == "0":
                console.print(f"[{NORD_GREEN}]Voltando ao menu principal...[/{NORD_GREEN}]")
                break
            elif choice == "1":
                system.cleanup_temp_files()
            elif choice == "2":
                system.validate_system_integrity()
            elif choice == "3":
                system.optimize_storage()
            elif choice == "4":
                system.comprehensive_cleanup()
            elif choice == "5":
                system.auto_repair_system()
            
            # Add a separator between operations
            console.print("\n" + "─" * console.width + "\n")
    
    except KeyboardInterrupt:
        console.print(f"\n[{NORD_YELLOW}]Operação interrompida pelo usuário[/{NORD_YELLOW}]")
    except Exception as e:
        console.print(f"[{NORD_RED}]Erro: {str(e)}[/{NORD_RED}]")

if __name__ == "__main__":
    main()