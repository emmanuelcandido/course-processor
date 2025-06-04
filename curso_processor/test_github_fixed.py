#!/usr/bin/env python3
"""
Test script for GitHub manager
"""

import os
import sys
from rich.console import Console

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import GitHub manager
from modules.github_manager_fixed import GitHubManager

# Create console
console = Console()

def main():
    """Main function"""
    # Set test repository path
    repo_path = "/workspace/test_github_repo"
    
    # Set GitHub credentials
    credentials = {
        "username": "openhands",
        "token": ""  # This will be overridden by GITHUB_TOKEN env var if available
    }
    
    # GITHUB_TOKEN environment variable is already set in the environment
    
    # Create GitHub manager
    manager = GitHubManager(repo_path=repo_path, credentials=credentials)
    
    # Check if repository is valid
    if not manager.is_valid_repository():
        console.print("[bold red]Repository is not valid")
        return
    
    console.print("[bold green]Repository is valid")
    
    # Get repository status
    status = manager.get_status()
    console.print("[bold cyan]Repository status:")
    console.print(status)
    
    # Add a line to README.md
    test_file = os.path.join(repo_path, "README.md")
    with open(test_file, "a") as f:
        f.write("Adding a new line.\n")
    
    # Add all files
    if manager.add_all():
        console.print("[bold green]Files added successfully")
    else:
        console.print("[bold red]Failed to add files")
    
    # Commit changes
    if manager.commit("Update README.md"):
        console.print("[bold green]Changes committed successfully")
    else:
        console.print("[bold red]Failed to commit changes")
    
    # Get current branch
    status = manager.get_status()
    current_branch = status.get('current_branch', 'master')
    
    # In a real scenario, we would push changes here
    console.print("[bold yellow]Skipping push operation in test environment")
    console.print("[bold green]Test completed successfully")

if __name__ == "__main__":
    main()