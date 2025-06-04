"""
GitHub Manager Module

This module provides functionality for managing GitHub repositories.
"""

import os
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from rich.progress import Progress

class GitHubManager:
    """
    Class for managing GitHub repositories
    """
    
    def __init__(self, repo_path: str, credentials: Optional[Dict[str, str]] = None):
        """
        Initialize GitHub manager
        
        Args:
            repo_path: Path to local repository
            credentials: GitHub credentials (username, token)
        """
        self.repo_path = repo_path
        self.credentials = credentials or {}
        
    def check_credentials(self) -> bool:
        """
        Check if GitHub credentials are configured
        
        Returns:
            bool: True if credentials are configured, False otherwise
        """
        return "username" in self.credentials and "token" in self.credentials
        
    def is_valid_repository(self) -> bool:
        """
        Check if the repository path is a valid Git repository
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.repo_path or not os.path.exists(self.repo_path):
            return False
            
        # Check if .git directory exists
        git_dir = os.path.join(self.repo_path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    def _format_remote_url_with_auth(self, remote_url: str) -> str:
        """
        Format remote URL with authentication credentials
        
        Args:
            remote_url: Original remote URL
            
        Returns:
            str: Remote URL with authentication
        """
        # Try to get token from environment variable first
        env_token = os.environ.get("GITHUB_TOKEN")
        
        # Get credentials
        username = self.credentials.get("username")
        token = env_token if env_token else self.credentials.get("token")
        
        if not remote_url.startswith("https://"):
            return remote_url
            
        # Extract the repository part (owner/repo.git)
        if "github.com/" in remote_url:
            repo_part = remote_url.split("github.com/")[1]
            
            if env_token:
                return f"https://{env_token}@github.com/{repo_part}"
            else:
                return f"https://{username}:{token}@github.com/{repo_part}"
        
        return remote_url
    
    def clone_repository(self, repo_url: str, local_dir: str,
                        progress: Optional[Progress] = None,
                        task_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Clone a GitHub repository
        
        Args:
            repo_url: Repository URL
            local_dir: Local directory to clone to
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            Tuple[bool, str]: Success status and output message
        """
        # Check if credentials are configured
        if not self.check_credentials():
            return False, "GitHub credentials not configured"
            
        # Create directory if it doesn't exist
        os.makedirs(local_dir, exist_ok=True)
        
        # Check if directory is empty
        if os.listdir(local_dir):
            return False, f"Directory {local_dir} is not empty"
            
        # Format URL with credentials
        repo_url_with_auth = self._format_remote_url_with_auth(repo_url)
            
        try:
            # Clone repository
            if progress:
                progress.update(task_id, description=f"Clonando repositório para {local_dir}")
                
            result = subprocess.run(
                ["git", "clone", repo_url_with_auth, local_dir],
                capture_output=True,
                text=True,
                check=True
            )
            
            if progress:
                progress.update(task_id, description="Repositório clonado com sucesso")
                
            return True, "Repository cloned successfully"
        except subprocess.CalledProcessError as e:
            token = self.credentials.get("token", "")
            error_message = e.stderr
            if token:
                error_message = error_message.replace(token, "***")  # Hide token in error message
            return False, f"Error cloning repository: {error_message}"
    
    def commit_and_push(self, local_dir: str, commit_message: str,
                      files_to_add: Optional[List[str]] = None,
                      branch_name: Optional[str] = None,
                      progress: Optional[Progress] = None,
                      task_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Commit and push changes to GitHub
        
        Args:
            local_dir: Local repository directory
            commit_message: Commit message
            files_to_add: List of files to add (if None, add all)
            branch_name: Branch name (if None, use current branch)
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            Tuple[bool, str]: Success status and output message
        """
        # Check if credentials are configured
        if not self.check_credentials():
            return False, "GitHub credentials not configured"
            
        # Check if directory exists and is a Git repository
        if not os.path.exists(local_dir) or not os.path.exists(os.path.join(local_dir, '.git')):
            return False, f"Directory {local_dir} is not a Git repository"
            
        try:
            # Configure Git credentials
            username = self.credentials.get("username")
            token = os.environ.get("GITHUB_TOKEN") or self.credentials.get("token")
            
            # Set Git user name and email
            subprocess.run(
                ["git", "-C", local_dir, "config", "user.name", username],
                capture_output=True,
                text=True,
                check=True
            )
            
            subprocess.run(
                ["git", "-C", local_dir, "config", "user.email", f"{username}@github.com"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Add files
            if progress:
                progress.update(task_id, description="Adicionando arquivos")
                
            if files_to_add:
                for file in files_to_add:
                    subprocess.run(
                        ["git", "-C", local_dir, "add", file],
                        capture_output=True,
                        text=True,
                        check=True
                    )
            else:
                subprocess.run(
                    ["git", "-C", local_dir, "add", "."],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "-C", local_dir, "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return False, "No changes to commit"
                
            # Commit changes
            if progress:
                progress.update(task_id, description="Commitando alterações")
                
            subprocess.run(
                ["git", "-C", local_dir, "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get current branch if not specified
            if not branch_name:
                result = subprocess.run(
                    ["git", "-C", local_dir, "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                branch_name = result.stdout.strip()
                
            # Push changes
            if progress:
                progress.update(task_id, description=f"Enviando alterações para branch {branch_name}")
                
            # Get remote URL
            result = subprocess.run(
                ["git", "-C", local_dir, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Format URL with credentials
            remote_url_with_auth = self._format_remote_url_with_auth(remote_url)
                
            # Set remote URL with credentials
            subprocess.run(
                ["git", "-C", local_dir, "remote", "set-url", "origin", remote_url_with_auth],
                capture_output=True,
                text=True,
                check=True
            )
                
            # Push changes
            subprocess.run(
                ["git", "-C", local_dir, "push", "origin", branch_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Reset remote URL to hide credentials
            if remote_url.startswith("https://"):
                subprocess.run(
                    ["git", "-C", local_dir, "remote", "set-url", "origin", remote_url],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
            if progress:
                progress.update(task_id, description="Alterações enviadas com sucesso")
                
            return True, f"Changes pushed to {branch_name} successfully"
        except subprocess.CalledProcessError as e:
            error_message = e.stderr
            token = self.credentials.get("token", "")
            if token:
                error_message = error_message.replace(token, "***")  # Hide token in error message
            return False, f"Error pushing changes: {error_message}"
    
    def add_all(self) -> bool:
        """
        Add all files to the Git index
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_valid_repository():
            return False
            
        try:
            subprocess.run(
                ["git", "-C", self.repo_path, "add", "."],
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
            
    def add_files(self, files: List[str]) -> bool:
        """
        Add specific files to the Git index
        
        Args:
            files: List of files to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_valid_repository():
            return False
            
        try:
            for file in files:
                subprocess.run(
                    ["git", "-C", self.repo_path, "add", file],
                    capture_output=True,
                    text=True,
                    check=True
                )
            return True
        except subprocess.CalledProcessError:
            return False
            
    def commit(self, message: str) -> bool:
        """
        Commit changes
        
        Args:
            message: Commit message
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_valid_repository():
            return False
            
        try:
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "-C", self.repo_path, "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return False
                
            # Configure Git credentials
            username = self.credentials.get("username")
            
            # Set Git user name and email
            subprocess.run(
                ["git", "-C", self.repo_path, "config", "user.name", username],
                capture_output=True,
                text=True,
                check=True
            )
            
            subprocess.run(
                ["git", "-C", self.repo_path, "config", "user.email", f"{username}@github.com"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Commit changes
            subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True
            )
            
            return True
        except subprocess.CalledProcessError:
            return False
            
    def push(self, branch: str = "main") -> bool:
        """
        Push changes to the remote repository
        
        Args:
            branch: Branch name to push
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_valid_repository() or not self.check_credentials():
            return False
            
        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "-C", self.repo_path, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Format URL with credentials
            remote_url_with_auth = self._format_remote_url_with_auth(remote_url)
                
            # Set remote URL with credentials
            subprocess.run(
                ["git", "-C", self.repo_path, "remote", "set-url", "origin", remote_url_with_auth],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Push changes
            try:
                result = subprocess.run(
                    ["git", "-C", self.repo_path, "push", "origin", branch],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"Push output: {result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"Error pushing changes: {e.stderr}")
                return False
            
            # Reset remote URL to hide credentials
            if remote_url.startswith("https://"):
                subprocess.run(
                    ["git", "-C", self.repo_path, "remote", "set-url", "origin", remote_url],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error in push method: {e.stderr}")
            return False
            
    def pull(self, branch: str = "main") -> bool:
        """
        Pull changes from the remote repository
        
        Args:
            branch: Branch name to pull
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_valid_repository() or not self.check_credentials():
            return False
            
        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "-C", self.repo_path, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Format URL with credentials
            remote_url_with_auth = self._format_remote_url_with_auth(remote_url)
                
            # Set remote URL with credentials
            subprocess.run(
                ["git", "-C", self.repo_path, "remote", "set-url", "origin", remote_url_with_auth],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Pull changes
            subprocess.run(
                ["git", "-C", self.repo_path, "pull", "origin", branch],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Reset remote URL to hide credentials
            if remote_url.startswith("https://"):
                subprocess.run(
                    ["git", "-C", self.repo_path, "remote", "set-url", "origin", remote_url],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
            return True
        except subprocess.CalledProcessError:
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get repository status
        
        Returns:
            Dict[str, Any]: Repository status
        """
        if not self.is_valid_repository():
            return {"error": "Not a valid Git repository"}
            
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "-C", self.repo_path, "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            
            current_branch = result.stdout.strip()
            
            # Get remotes
            result = subprocess.run(
                ["git", "-C", self.repo_path, "remote", "-v"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remotes = {}
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2 and "(fetch)" in line:
                        remotes[parts[0]] = parts[1]
            
            # Get modified files
            result = subprocess.run(
                ["git", "-C", self.repo_path, "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            
            modified_files = [file for file in result.stdout.strip().split("\n") if file]
            
            # Get untracked files
            result = subprocess.run(
                ["git", "-C", self.repo_path, "ls-files", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                check=True
            )
            
            untracked_files = [file for file in result.stdout.strip().split("\n") if file]
            
            return {
                "current_branch": current_branch,
                "remotes": remotes,
                "modified_files": modified_files,
                "untracked_files": untracked_files
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"Error getting repository status: {e.stderr}"}
            
    def copy_files_to_repo(self, source_dir: str, target_dir: str = None) -> bool:
        """
        Copy files to repository
        
        Args:
            source_dir: Source directory
            target_dir: Target directory (if None, use repository root)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_valid_repository():
            return False
            
        if not os.path.exists(source_dir):
            return False
            
        target_dir = target_dir or self.repo_path
        
        try:
            # Create target directory if it doesn't exist
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy files
            import shutil
            
            # Get list of files in source directory
            files = os.listdir(source_dir)
            
            for file in files:
                source_file = os.path.join(source_dir, file)
                target_file = os.path.join(target_dir, file)
                
                if os.path.isfile(source_file):
                    shutil.copy2(source_file, target_file)
                elif os.path.isdir(source_file):
                    shutil.copytree(source_file, target_file, dirs_exist_ok=True)
                    
            return True
        except Exception:
            return False
            
    def update_github_with_files(self, source_dir: str, commit_message: str,
                               branch_name: Optional[str] = None,
                               progress: Optional[Progress] = None,
                               task_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Update GitHub repository with files
        
        Args:
            source_dir: Source directory
            commit_message: Commit message
            branch_name: Branch name (if None, use current branch)
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            Tuple[bool, str]: Success status and output message
        """
        if not self.is_valid_repository() or not self.check_credentials():
            return False, "Repository not valid or credentials not configured"
            
        if not os.path.exists(source_dir):
            return False, f"Source directory {source_dir} does not exist"
            
        try:
            # Copy files to repository
            if progress:
                progress.update(task_id, description=f"Copiando arquivos de {source_dir} para {self.repo_path}")
                
            if not self.copy_files_to_repo(source_dir):
                return False, f"Failed to copy files from {source_dir} to {self.repo_path}"
                
            # Commit and push changes
            return self.commit_and_push(
                self.repo_path,
                commit_message,
                branch_name=branch_name,
                progress=progress,
                task_id=task_id
            )
        except Exception as e:
            return False, f"Error updating GitHub repository: {str(e)}"