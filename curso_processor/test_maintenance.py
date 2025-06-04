#!/usr/bin/env python3
"""
Test script for the maintenance system
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

# Import maintenance system
import maintenance

# Initialize console
console = Console()

def test_cleanup_temp_files():
    """Test cleanup of temporary files"""
    console.print("[bold cyan]Testing cleanup of temporary files...[/bold cyan]")
    
    # Create maintenance system
    system = maintenance.SystemMaintenance()
    
    # Create temporary files
    temp_dir = system.temp_dir
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create 5 temporary files
    for i in range(5):
        with open(os.path.join(temp_dir, f"temp_file_{i}.txt"), "w") as f:
            f.write(f"Temporary file {i}")
    
    # Count files before cleanup
    files_before = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
    
    # Cleanup temporary files
    freed_space = system.cleanup_temp_files()
    
    # Count files after cleanup
    files_after = len([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])
    
    # Print results
    console.print(f"Files before cleanup: {files_before}")
    console.print(f"Files after cleanup: {files_after}")
    console.print(f"Space freed: {freed_space:.2f} MB")
    
    # Check if cleanup was successful
    if files_after == 0:
        console.print("[bold green]✅ Cleanup of temporary files successful[/bold green]")
    else:
        console.print("[bold red]❌ Cleanup of temporary files failed[/bold red]")

def test_migration():
    """Test migration functionality"""
    console.print("[bold cyan]Testing migration functionality...[/bold cyan]")
    
    # Create maintenance system
    system = maintenance.SystemMaintenance()
    
    # Create source and target directories
    with tempfile.TemporaryDirectory() as source_dir:
        with tempfile.TemporaryDirectory() as target_dir:
            # Create test files in source directory
            for i in range(3):
                # Create subdirectory
                subdir = os.path.join(source_dir, f"subdir_{i}")
                os.makedirs(subdir, exist_ok=True)
                
                # Create files of different types
                with open(os.path.join(subdir, f"audio_{i}.mp3"), "w") as f:
                    f.write(f"Audio file {i}")
                
                with open(os.path.join(subdir, f"text_{i}.txt"), "w") as f:
                    f.write(f"Text file {i}")
                
                with open(os.path.join(subdir, f"config_{i}.json"), "w") as f:
                    f.write(f'{{"name": "Config file {i}"}}')
            
            # Analyze migration
            migration_plan = system.analyze_migration(source_dir, target_dir)
            
            # Print migration plan
            console.print("Migration plan:")
            for file_type, info in migration_plan.items():
                if info["count"] > 0:
                    console.print(f"  {file_type}: {info['count']} files, {info['size']}")
            
            # Execute migration
            system.execute_migration(migration_plan, source_dir, target_dir, "copy")
            
            # Count files in target directory
            target_files = []
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    target_files.append(os.path.join(root, file))
            
            # Print results
            console.print(f"Files in target directory: {len(target_files)}")
            
            # Check if migration was successful
            source_files = []
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    source_files.append(os.path.relpath(os.path.join(root, file), source_dir))
            
            target_files = []
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    target_files.append(os.path.relpath(os.path.join(root, file), target_dir))
            
            if sorted(source_files) == sorted(target_files):
                console.print("[bold green]✅ Migration successful[/bold green]")
            else:
                console.print("[bold red]❌ Migration failed[/bold red]")
                console.print("Source files:", sorted(source_files))
                console.print("Target files:", sorted(target_files))

def test_system_validation():
    """Test system validation functionality"""
    console.print("[bold cyan]Testing system validation functionality...[/bold cyan]")
    
    # Create maintenance system
    system = maintenance.SystemMaintenance()
    
    # Validate system integrity
    health_report = system.validate_system_integrity()
    
    # Print health report
    console.print(f"System health: {health_report['system_health']}")
    console.print("Validations:")
    for validation_name, result in health_report["validations"].items():
        status = "✅" if result["is_valid"] else "❌"
        console.print(f"  {status} {validation_name}")
    
    if health_report["issues"]:
        console.print("Issues found:")
        for issue in health_report["issues"]:
            console.print(f"  • {issue['description']}")
    
    if health_report["recommendations"]:
        console.print("Recommendations:")
        for recommendation in health_report["recommendations"]:
            console.print(f"  • {recommendation}")

def test_storage_optimization():
    """Test storage optimization functionality"""
    console.print("[bold cyan]Testing storage optimization functionality...[/bold cyan]")
    
    # Create maintenance system
    system = maintenance.SystemMaintenance()
    
    # Create test files
    cache_dir = system.cache_dir
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create 5 cache files
    for i in range(5):
        with open(os.path.join(cache_dir, f"cache_file_{i}.txt"), "w") as f:
            f.write(f"Cache file {i}" * 1000)  # Make files larger
    
    # Get initial size
    initial_size = system.get_directory_size(cache_dir)
    
    # Optimize storage
    freed_space = system._optimize_database_files()
    
    # Get final size
    final_size = system.get_directory_size(cache_dir)
    
    # Print results
    console.print(f"Initial size: {system.format_size(initial_size)}")
    console.print(f"Final size: {system.format_size(final_size)}")
    console.print(f"Space freed: {freed_space:.2f} MB")
    
    # Check if optimization was successful
    if final_size <= initial_size:
        console.print("[bold green]✅ Storage optimization successful[/bold green]")
    else:
        console.print("[bold red]❌ Storage optimization failed[/bold red]")

def test_auto_repair():
    """Test auto-repair functionality"""
    console.print("[bold cyan]Testing auto-repair functionality...[/bold cyan]")
    
    # Create maintenance system
    system = maintenance.SystemMaintenance()
    
    # Get data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    
    # Create backup of settings.json
    settings_file = os.path.join(data_dir, "settings.json")
    if os.path.exists(settings_file):
        shutil.copy2(settings_file, f"{settings_file}.bak")
    
    try:
        # Corrupt settings.json
        if os.path.exists(settings_file):
            with open(settings_file, "w") as f:
                f.write("{")
        
        # Run auto-repair
        system._repair_config_files()
        
        # Check if settings.json was repaired
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    json.load(f)
                console.print("[bold green]✅ Auto-repair successful[/bold green]")
            except json.JSONDecodeError:
                console.print("[bold red]❌ Auto-repair failed[/bold red]")
    finally:
        # Restore settings.json
        if os.path.exists(f"{settings_file}.bak"):
            shutil.copy2(f"{settings_file}.bak", settings_file)
            os.remove(f"{settings_file}.bak")

def main():
    """Main function"""
    console.print(Panel(
        Text("Maintenance System Test", style="bold cyan"),
        border_style="cyan"
    ))
    
    # Run tests
    test_cleanup_temp_files()
    print()
    
    test_migration()
    print()
    
    test_system_validation()
    print()
    
    test_storage_optimization()
    print()
    
    test_auto_repair()

if __name__ == "__main__":
    main()