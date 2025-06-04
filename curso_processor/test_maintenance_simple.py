#!/usr/bin/env python3
"""
Simplified test script for the maintenance system
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Initialize console
console = Console()

def test_directory_structure():
    """Test directory structure creation"""
    console.print("[bold cyan]Testing directory structure creation...[/bold cyan]")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create base directories
        base_dirs = [
            os.path.join(temp_dir, "data"),
            os.path.join(temp_dir, "temp"),
            os.path.join(temp_dir, "logs"),
            os.path.join(temp_dir, "cache"),
            os.path.join(temp_dir, "backups")
        ]
        
        for directory in base_dirs:
            os.makedirs(directory, exist_ok=True)
        
        # Check if directories were created
        all_created = True
        for directory in base_dirs:
            if not os.path.exists(directory):
                all_created = False
                console.print(f"[bold red]❌ Directory not created: {directory}[/bold red]")
        
        if all_created:
            console.print("[bold green]✅ All directories created successfully[/bold green]")
        else:
            console.print("[bold red]❌ Some directories were not created[/bold red]")

def test_file_operations():
    """Test file operations"""
    console.print("[bold cyan]Testing file operations...[/bold cyan]")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = [
            os.path.join(temp_dir, "test1.txt"),
            os.path.join(temp_dir, "test2.txt"),
            os.path.join(temp_dir, "test3.txt")
        ]
        
        for i, file_path in enumerate(test_files):
            with open(file_path, "w") as f:
                f.write(f"Test file {i+1}")
        
        # Check if files were created
        all_created = True
        for file_path in test_files:
            if not os.path.exists(file_path):
                all_created = False
                console.print(f"[bold red]❌ File not created: {file_path}[/bold red]")
        
        if all_created:
            console.print("[bold green]✅ All files created successfully[/bold green]")
        else:
            console.print("[bold red]❌ Some files were not created[/bold red]")
        
        # Delete files
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Check if files were deleted
        all_deleted = True
        for file_path in test_files:
            if os.path.exists(file_path):
                all_deleted = False
                console.print(f"[bold red]❌ File not deleted: {file_path}[/bold red]")
        
        if all_deleted:
            console.print("[bold green]✅ All files deleted successfully[/bold green]")
        else:
            console.print("[bold red]❌ Some files were not deleted[/bold red]")

def test_json_operations():
    """Test JSON operations"""
    console.print("[bold cyan]Testing JSON operations...[/bold cyan]")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test JSON file
        json_file = os.path.join(temp_dir, "test.json")
        
        # Create test data
        test_data = {
            "name": "Test",
            "version": "1.0.0",
            "settings": {
                "language": "pt-BR",
                "theme": "nord",
                "debug": False
            },
            "paths": {
                "data": "/data",
                "temp": "/temp",
                "logs": "/logs"
            }
        }
        
        # Write test data to JSON file
        with open(json_file, "w") as f:
            json.dump(test_data, f, indent=4)
        
        # Check if JSON file was created
        if os.path.exists(json_file):
            console.print("[bold green]✅ JSON file created successfully[/bold green]")
        else:
            console.print("[bold red]❌ JSON file not created[/bold red]")
        
        # Read JSON file
        try:
            with open(json_file, "r") as f:
                read_data = json.load(f)
            
            # Check if data is correct
            if read_data == test_data:
                console.print("[bold green]✅ JSON data read successfully[/bold green]")
            else:
                console.print("[bold red]❌ JSON data does not match[/bold red]")
        except Exception as e:
            console.print(f"[bold red]❌ Error reading JSON file: {str(e)}[/bold red]")

def main():
    """Main function"""
    console.print(Panel(
        Text("Maintenance System Simple Test", style="bold cyan"),
        border_style="cyan"
    ))
    
    # Run tests
    test_directory_structure()
    print()
    
    test_file_operations()
    print()
    
    test_json_operations()

if __name__ == "__main__":
    main()