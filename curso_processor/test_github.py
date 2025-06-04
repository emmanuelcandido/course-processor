#!/usr/bin/env python3
"""
Test script for GitHub functionality
"""

import os
import sys
from rich.console import Console

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from curso_processor.modules.github_manager import GitHubManager
from curso_processor.utils import ui_components

def main():
    """
    Main function
    """
    console = Console()
    
    # Create GitHub manager
    github_manager = GitHubManager(console=console)
    
    # Check credentials
    if not github_manager.check_credentials():
        console.print("[bold red]GitHub credentials not configured[/bold red]")
        return
    
    console.print("[bold green]GitHub credentials configured[/bold green]")
    
    # Set repository path
    repo_path = "/workspace/curso_processor/test_repo"
    github_manager.repo_path = repo_path
    
    # Check if repository is valid
    if not github_manager.is_valid_repository():
        console.print(f"[bold red]Repository {repo_path} is not valid[/bold red]")
        return
    
    console.print(f"[bold green]Repository {repo_path} is valid[/bold green]")
    
    # Get repository status
    status = github_manager.get_status()
    console.print("[bold cyan]Repository status:[/bold cyan]")
    console.print(status)
    
    # Test copy files to repository
    files = ["/workspace/curso_processor/test_files/test.md"]
    
    progress = ui_components.create_progress_bar("Testing GitHub")
    
    with progress:
        task = progress.add_task("Copying files...", total=1)
        success, copied_files = github_manager.copy_files_to_repo(
            files=files,
            repo_dir=repo_path,
            progress=progress,
            task_id=task
        )
    
    if success:
        console.print(f"[bold green]Files copied successfully: {copied_files}[/bold green]")
    else:
        console.print("[bold red]Failed to copy files[/bold red]")
        return
    
    # Add files
    if github_manager.add_all():
        console.print("[bold green]Files added successfully[/bold green]")
    else:
        console.print("[bold red]Failed to add files[/bold red]")
        return
    
    # Commit changes
    commit_result = github_manager.commit("Test commit")
    if commit_result:
        console.print("[bold green]Changes committed successfully[/bold green]")
    else:
        console.print("[bold yellow]No changes to commit or commit failed[/bold yellow]")
        # Continue execution, don't return
    
    # Get updated status
    status = github_manager.get_status()
    console.print("[bold cyan]Updated repository status:[/bold cyan]")
    console.print(status)
    
    # Test update_github_with_files
    console.print("\n[bold cyan]Testing update_github_with_files method:[/bold cyan]")
    
    # Create a new test file
    new_test_file = "/workspace/curso_processor/test_files/test2.md"
    with open(new_test_file, "w") as f:
        f.write("# Test File 2\nThis is another test file for GitHub upload.")
    
    # Update GitHub with files
    success, message = github_manager.update_github_with_files(
        files=[new_test_file],
        repo_url="https://github.com/test_user/test_repo.git",
        local_dir=repo_path,
        commit_message="Add test file 2"
    )
    
    if success:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")
    
    # Get final status
    status = github_manager.get_status()
    console.print("[bold cyan]Final repository status:[/bold cyan]")
    console.print(status)

if __name__ == "__main__":
    main()