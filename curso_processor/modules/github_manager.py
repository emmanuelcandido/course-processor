"""
GitHub manager module for Curso Processor

This module provides functionality to manage GitHub repositories for course content,
including repository setup, XML file updates, and automated commits and pushes.
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import logging

from rich.progress import Progress
from rich.console import Console

from utils import ui_components
from config import credentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GitHubManager:
    """
    GitHub manager class for handling GitHub operations
    """
    
    def __init__(self, repo_path: str = None, console: Console = None):
        """
        Initialize GitHub manager
        
        Args:
            repo_path: Path to local repository
            console: Rich console instance
        """
        self.console = console or Console()
        self.credentials = credentials.get_github_credentials()
        self.repo_path = os.path.expanduser(repo_path) if repo_path else None
    
    def check_credentials(self) -> bool:
        """
        Check if GitHub credentials are configured
        
        Returns:
            bool: True if credentials are configured, False otherwise
        """
        return bool(self.credentials.get("username") and self.credentials.get("token"))
        
    def is_valid_repository(self) -> bool:
        """
        Check if the repository path is a valid Git repository
        
        Returns:
            bool: True if the repository is valid, False otherwise
        """
        if not self.repo_path or not os.path.exists(self.repo_path):
            return False
            
        # Check if .git directory exists
        git_dir = os.path.join(self.repo_path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    def validate_git_config(self) -> bool:
        """
        Check if git user.name and user.email are configured
        
        Returns:
            bool: True if both user.name and user.email are configured, False otherwise
        """
        if not self.is_valid_repository():
            return False
            
        try:
            # Check user.name
            result = subprocess.run(
                ["git", "-C", self.repo_path, "config", "user.name"],
                capture_output=True,
                text=True,
                check=False
            )
            has_name = result.returncode == 0 and result.stdout.strip()
            
            # Check user.email
            result = subprocess.run(
                ["git", "-C", self.repo_path, "config", "user.email"],
                capture_output=True,
                text=True,
                check=False
            )
            has_email = result.returncode == 0 and result.stdout.strip()
            
            return has_name and has_email
        except Exception as e:
            logger.error(f"Error validating git config: {e}")
            return False
    
    def setup_repository(self, remote_url: Optional[str] = None) -> Tuple[bool, str]:
        """
        Set up a git repository in the specified directory
        
        Args:
            remote_url: URL of the remote repository (optional)
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.repo_path:
            return False, "Repository path not specified"
            
        # Create directory if it doesn't exist
        os.makedirs(self.repo_path, exist_ok=True)
        
        # Initialize repository if it doesn't exist
        if not self.is_valid_repository():
            try:
                result = subprocess.run(
                    ["git", "init"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info(f"Initialized git repository at {self.repo_path}")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to initialize repository: {e.stderr}"
        
        # Configure user if not already configured
        if not self.validate_git_config():
            username = self.credentials.get("username", "curso_processor")
            email = f"{username}@github.com"
            
            try:
                # Set user.name
                subprocess.run(
                    ["git", "-C", self.repo_path, "config", "user.name", username],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Set user.email
                subprocess.run(
                    ["git", "-C", self.repo_path, "config", "user.email", email],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info(f"Configured git user: {username} <{email}>")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to configure git user: {e.stderr}"
        
        # Set up remote if provided
        if remote_url:
            try:
                # Check if remote already exists
                result = subprocess.run(
                    ["git", "-C", self.repo_path, "remote"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if "origin" in result.stdout.split():
                    # Update existing remote
                    subprocess.run(
                        ["git", "-C", self.repo_path, "remote", "set-url", "origin", remote_url],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                else:
                    # Add new remote
                    subprocess.run(
                        ["git", "-C", self.repo_path, "remote", "add", "origin", remote_url],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                
                logger.info(f"Set remote 'origin' to {remote_url}")
            except subprocess.CalledProcessError as e:
                return False, f"Failed to set remote: {e.stderr}"
        
        return True, "Repository setup completed successfully"
    
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
            
        # Try to get token from environment variable first
        import os
        env_token = os.environ.get("GITHUB_TOKEN")
        
        # Format URL with credentials
        username = self.credentials.get("username")
        token = env_token if env_token else self.credentials.get("token")
        
        # Extract the repository URL without protocol
        if repo_url.startswith("https://"):
            if env_token:
                repo_url_with_auth = f"https://{env_token}@{repo_url[8:]}"
            else:
                repo_url_with_auth = f"https://{username}:{token}@{repo_url[8:]}"
        else:
            return False, "Only HTTPS URLs are supported"
            
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
            error_message = e.stderr.replace(token, "***")  # Hide token in error message
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
            # Try to get token from environment variable first
            import os
            env_token = os.environ.get("GITHUB_TOKEN")
            
            # Configure Git credentials
            username = self.credentials.get("username")
            token = env_token if env_token else self.credentials.get("token")
            
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
            if remote_url.startswith("https://"):
                if env_token:
                    remote_url_with_auth = f"https://{env_token}@{remote_url[8:]}"
                else:
                    remote_url_with_auth = f"https://{username}:{token}@{remote_url[8:]}"
                
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
            files: List of file paths to add
            
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
        Commit changes to the repository
        
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
                return False  # No changes to commit
                
            # Configure Git user name and email if not already set
            username = self.credentials.get("username")
            if username:
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
            
    def commit_xml_changes(self, xml_path: str, commit_message: Optional[str] = None) -> Tuple[bool, str]:
        """
        Commit changes to an XML file
        
        Args:
            xml_path: Path to the XML file
            commit_message: Custom commit message (optional)
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        if not self.is_valid_repository():
            return False, "Not a git repository"
        
        # Ensure the XML file exists
        xml_path = os.path.abspath(os.path.expanduser(xml_path))
        if not os.path.isfile(xml_path):
            return False, f"XML file not found: {xml_path}"
        
        # Get the relative path to the XML file from the repository root
        try:
            rel_path = os.path.relpath(xml_path, self.repo_path)
        except ValueError:
            return False, f"XML file is not within the repository: {xml_path}"
        
        try:
            # Stage the XML file
            subprocess.run(
                ["git", "-C", self.repo_path, "add", rel_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "-C", self.repo_path, "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return True, "No changes to commit"
            
            # Create commit message
            if not commit_message:
                commit_message = f"Update XML file - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Configure Git user name and email if not already set
            if not self.validate_git_config():
                username = self.credentials.get("username", "curso_processor")
                email = f"{username}@github.com"
                
                subprocess.run(
                    ["git", "-C", self.repo_path, "config", "user.name", username],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                subprocess.run(
                    ["git", "-C", self.repo_path, "config", "user.email", email],
                    capture_output=True,
                    text=True,
                    check=True
                )
            
            # Commit changes
            subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                check=True
            )
            
            return True, f"Changes committed successfully: {commit_message}"
        except subprocess.CalledProcessError as e:
            return False, f"Failed to commit changes: {e.stderr}"
            
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
            
            # Try to get token from environment variable first
            import os
            env_token = os.environ.get("GITHUB_TOKEN")
            
            # Format URL with credentials
            username = self.credentials.get("username")
            token = env_token if env_token else self.credentials.get("token")
            
            if remote_url.startswith("https://"):
                if env_token:
                    remote_url_with_auth = f"https://{env_token}@{remote_url[8:]}"
                else:
                    remote_url_with_auth = f"https://{username}:{token}@{remote_url[8:]}"
                
                # Set remote URL with credentials
                subprocess.run(
                    ["git", "-C", self.repo_path, "remote", "set-url", "origin", remote_url_with_auth],
                    capture_output=True,
                    text=True,
                    check=True
                )
            
            # Push changes
            subprocess.run(
                ["git", "-C", self.repo_path, "push", "origin", branch],
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
            
    def update_repository(self, xml_path: str, commit_message: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Update the repository with changes to an XML file
        
        Args:
            xml_path: Path to the XML file
            commit_message: Custom commit message (optional)
            
        Returns:
            Tuple[bool, str, str]: Success status, message, and public URL
        """
        # Commit changes
        success, message = self.commit_xml_changes(xml_path, commit_message)
        if not success and "No changes to commit" not in message:
            return False, message, ""
        
        # Push to remote
        branch = "main"  # Default branch
        
        # Get current branch
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                branch = result.stdout.strip()
        except subprocess.CalledProcessError:
            pass  # Use default branch
        
        # Push changes
        push_success = self.push(branch)
        if not push_success:
            return False, f"Commit successful but push failed", ""
        
        # Get public URL
        public_url = self.get_public_xml_url(os.path.basename(xml_path))
        
        return True, "Repository updated successfully", public_url
    
    def get_public_xml_url(self, xml_filename: str) -> str:
        """
        Get the public URL for the XML file
        
        Args:
            xml_filename: XML filename
            
        Returns:
            str: Public URL for the XML file
        """
        if not self.is_valid_repository():
            return ""
        
        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "-C", self.repo_path, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Get current branch
            result = subprocess.run(
                ["git", "-C", self.repo_path, "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            
            branch = result.stdout.strip() or "main"
            
            # Convert SSH URL to HTTPS URL if necessary
            if remote_url.startswith("git@github.com:"):
                # Format: git@github.com:username/repo.git
                parts = remote_url.split(":")
                if len(parts) >= 2:
                    repo_path = parts[1]
                    if repo_path.endswith(".git"):
                        repo_path = repo_path[:-4]
                    remote_url = f"https://github.com/{repo_path}"
            elif remote_url.startswith("https://"):
                # Format: https://github.com/username/repo.git
                if remote_url.endswith(".git"):
                    remote_url = remote_url[:-4]
                
                # Remove authentication if present
                if "@" in remote_url:
                    parts = remote_url.split("@")
                    remote_url = f"https://{parts[1]}"
            
            # Construct the raw content URL
            if "github.com" in remote_url:
                # GitHub raw content URL format
                raw_url = remote_url.replace("https://github.com", "https://raw.githubusercontent.com")
                return f"{raw_url}/{branch}/{xml_filename}"
            
            return ""
        except subprocess.CalledProcessError:
            return ""
            
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
            
            # Try to get token from environment variable first
            import os
            env_token = os.environ.get("GITHUB_TOKEN")
            
            # Format URL with credentials
            username = self.credentials.get("username")
            token = env_token if env_token else self.credentials.get("token")
            
            if remote_url.startswith("https://"):
                if env_token:
                    remote_url_with_auth = f"https://{env_token}@{remote_url[8:]}"
                else:
                    remote_url_with_auth = f"https://{username}:{token}@{remote_url[8:]}"
                
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
    
    def copy_files_to_repo(self, files: List[str], repo_dir: str, target_dir: Optional[str] = None,
                         progress: Optional[Progress] = None,
                         task_id: Optional[int] = None) -> Tuple[bool, List[str]]:
        """
        Copy files to a repository directory
        
        Args:
            files: List of file paths
            repo_dir: Repository directory
            target_dir: Target directory within the repository (if None, use repository root)
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            Tuple[bool, List[str]]: Success status and list of copied files
        """
        if not os.path.exists(repo_dir):
            return False, []
            
        # Create target directory if it doesn't exist
        if target_dir:
            target_path = os.path.join(repo_dir, target_dir)
            os.makedirs(target_path, exist_ok=True)
        else:
            target_path = repo_dir
            
        copied_files = []
        
        try:
            for file in files:
                if not os.path.exists(file):
                    continue
                    
                # Get file name
                file_name = os.path.basename(file)
                
                # Create target file path
                target_file = os.path.join(target_path, file_name)
                
                # Copy file
                if progress:
                    progress.update(task_id, description=f"Copiando {file_name}")
                    
                shutil.copy2(file, target_file)
                copied_files.append(target_file)
                
            return True, copied_files
        except Exception as e:
            return False, copied_files
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get repository status
        
        Returns:
            Dict[str, Any]: Repository status information
        """
        if not self.is_valid_repository():
            return {"error": "Not a valid repository"}
            
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "-C", self.repo_path, "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = result.stdout.strip()
            
            # Get modified files
            result = subprocess.run(
                ["git", "-C", self.repo_path, "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True
            )
            
            modified_files = []
            untracked_files = []
            
            for line in result.stdout.splitlines():
                if line.startswith("??"):
                    untracked_files.append(line[3:])
                elif line.startswith(" M") or line.startswith("M "):
                    modified_files.append(line[3:])
                    
            # Get remote information
            result = subprocess.run(
                ["git", "-C", self.repo_path, "remote", "-v"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remotes = {}
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    url = parts[1]
                    remotes[name] = url
            
            return {
                "current_branch": current_branch,
                "modified_files": modified_files,
                "untracked_files": untracked_files,
                "remotes": remotes
            }
        except subprocess.CalledProcessError as e:
            return {"error": f"Error getting repository status: {e}"}
    
    def update_github_with_files(self, files: List[str], repo_url: str, local_dir: str,
                              target_dir: Optional[str] = None,
                              commit_message: str = "Update files",
                              branch_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Update GitHub repository with files
        
        Args:
            files: List of file paths
            repo_url: Repository URL
            local_dir: Local directory for the repository
            target_dir: Target directory within the repository
            commit_message: Commit message
            branch_name: Branch name
            
        Returns:
            Tuple[bool, str]: Success status and output message
        """
        # Check if credentials are configured
        if not self.check_credentials():
            return False, "GitHub credentials not configured"
            
        # Create progress bar
        progress = ui_components.create_progress_bar("Atualizando GitHub")
        
        with progress:
            # Add tasks
            clone_task = progress.add_task("Clonando repositório...", total=1)
            copy_task = progress.add_task("Copiando arquivos...", total=1, visible=False)
            commit_task = progress.add_task("Commitando alterações...", total=1, visible=False)
            push_task = progress.add_task("Enviando alterações...", total=1, visible=False)
            
            # Clone repository if it doesn't exist
            if not os.path.exists(local_dir) or not os.path.exists(os.path.join(local_dir, '.git')):
                success, message = self.clone_repository(repo_url, local_dir, progress, clone_task)
                if not success:
                    return False, message
            else:
                # Repository already exists, update status
                progress.update(clone_task, description="Repositório já existe", completed=1)
                
            # Copy files to repository
            progress.update(copy_task, visible=True)
            success, copied_files = self.copy_files_to_repo(files, local_dir, target_dir, progress, copy_task)
            
            if not success or not copied_files:
                return False, "Failed to copy files to repository"
                
            progress.update(copy_task, completed=1)
            
            # Commit changes
            progress.update(commit_task, visible=True)
            
            # Add files
            for file in copied_files:
                # Get relative path to repository
                rel_path = os.path.relpath(file, local_dir)
                subprocess.run(
                    ["git", "-C", local_dir, "add", rel_path],
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
                
            # Configure Git user name and email
            username = self.credentials.get("username")
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
            
            # Commit changes
            subprocess.run(
                ["git", "-C", local_dir, "commit", "-m", commit_message],
                capture_output=True,
                text=True,
                check=True
            )
            
            progress.update(commit_task, completed=1)
            
            # Push changes
            progress.update(push_task, visible=True)
            
            # Get remote URL
            result = subprocess.run(
                ["git", "-C", local_dir, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Format URL with credentials
            token = self.credentials.get("token")
            
            if remote_url.startswith("https://"):
                remote_url_with_auth = f"https://{username}:{token}@{remote_url[8:]}"
                
                # Set remote URL with credentials
                subprocess.run(
                    ["git", "-C", local_dir, "remote", "set-url", "origin", remote_url_with_auth],
                    capture_output=True,
                    text=True,
                    check=True
                )
            
            # Push changes
            subprocess.run(
                ["git", "-C", local_dir, "push", "origin", branch_name or "main"],
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
                
            progress.update(push_task, completed=1)
            
            return True, f"Files updated in GitHub repository: {len(copied_files)} files"

def clone_repository(repo_url: str, local_dir: str,
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
    try:
        # Import git (only when needed to avoid unnecessary dependencies)
        import git
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Clonando repositório {repo_url}")
        
        # Clone repository
        repo = git.Repo.clone_from(repo_url, local_dir)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        return True, f"Repositório clonado com sucesso em {local_dir}"
    
    except ImportError:
        error_message = "GitPython não está instalado. Execute 'pip install gitpython' para instalar."
        return False, error_message
    
    except Exception as e:
        error_message = f"Erro ao clonar repositório: {str(e)}"
        return False, error_message

def commit_and_push(local_dir: str, commit_message: str,
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
    try:
        # Import git
        import git
        
        # Get GitHub credentials
        github_creds = credentials.get_github_credentials()
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Preparando commit")
        
        # Open repository
        repo = git.Repo(local_dir)
        
        # Check if there are changes
        if not repo.is_dirty() and not repo.untracked_files:
            return True, "Nenhuma alteração para commit"
        
        # Add files
        if files_to_add:
            for file_path in files_to_add:
                repo.git.add(file_path)
        else:
            repo.git.add(A=True)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Criando commit")
        
        # Commit changes
        repo.git.commit(m=commit_message)
        
        # Switch branch if needed
        if branch_name:
            # Check if branch exists
            if branch_name in repo.heads:
                repo.git.checkout(branch_name)
            else:
                repo.git.checkout(b=branch_name)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Enviando para GitHub")
        
        # Set remote URL with credentials if available
        if github_creds.get("username") and github_creds.get("token"):
            remote_url = repo.remotes.origin.url
            if remote_url.startswith("https://"):
                auth_remote_url = f"https://{github_creds['username']}:{github_creds['token']}@" + remote_url[8:]
                repo.git.remote("set-url", "origin", auth_remote_url)
        
        # Push changes
        repo.git.push("--set-upstream", "origin", repo.active_branch.name)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        return True, f"Alterações enviadas com sucesso para o branch {repo.active_branch.name}"
    
    except ImportError:
        error_message = "GitPython não está instalado. Execute 'pip install gitpython' para instalar."
        return False, error_message
    
    except Exception as e:
        error_message = f"Erro ao enviar alterações para GitHub: {str(e)}"
        return False, error_message

def copy_files_to_repo(files: List[str], repo_dir: str, target_dir: Optional[str] = None,
                     progress: Optional[Progress] = None,
                     task_id: Optional[int] = None) -> Tuple[bool, List[str]]:
    """
    Copy files to a repository directory
    
    Args:
        files: List of file paths
        repo_dir: Repository directory
        target_dir: Target directory within the repository (if None, use repository root)
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, List[str]]: Success status and list of copied files
    """
    try:
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, description=f"Copiando arquivos para o repositório")
        
        # Determine target directory
        if target_dir:
            full_target_dir = os.path.join(repo_dir, target_dir)
            os.makedirs(full_target_dir, exist_ok=True)
        else:
            full_target_dir = repo_dir
        
        # Copy files
        copied_files = []
        for file_path in files:
            if os.path.exists(file_path):
                target_path = os.path.join(full_target_dir, os.path.basename(file_path))
                shutil.copy2(file_path, target_path)
                copied_files.append(target_path)
        
        # Update progress if provided
        if progress and task_id is not None:
            progress.update(task_id, advance=1)
        
        return True, copied_files
    
    except Exception as e:
        error_message = f"Erro ao copiar arquivos para o repositório: {str(e)}"
        return False, []

def update_github_with_files(files: List[str], repo_url: str, local_dir: str,
                          target_dir: Optional[str] = None,
                          commit_message: str = "Update files",
                          branch_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Update GitHub repository with files
    
    Args:
        files: List of file paths
        repo_url: Repository URL
        local_dir: Local directory for the repository
        target_dir: Target directory within the repository
        commit_message: Commit message
        branch_name: Branch name
        
    Returns:
        Tuple[bool, str]: Success status and output message
    """
    # Create progress bar
    progress = ui_components.create_progress_bar("Atualizando GitHub")
    
    with progress:
        # Add tasks
        clone_task = progress.add_task("Preparando repositório...", total=1)
        copy_task = progress.add_task("Copiando arquivos...", total=1, visible=False)
        commit_task = progress.add_task("Enviando alterações...", total=1, visible=False)
        
        # Clone or pull repository
        if os.path.exists(os.path.join(local_dir, ".git")):
            # Repository already exists, pull latest changes
            try:
                import git
                repo = git.Repo(local_dir)
                repo.git.pull()
                progress.update(clone_task, advance=1)
            except Exception as e:
                return False, f"Erro ao atualizar repositório local: {str(e)}"
        else:
            # Clone repository
            success, message = clone_repository(
                repo_url=repo_url,
                local_dir=local_dir,
                progress=progress,
                task_id=clone_task
            )
            
            if not success:
                return False, message
        
        # Make copy task visible
        progress.update(copy_task, visible=True)
        
        # Copy files to repository
        success, copied_files = copy_files_to_repo(
            files=files,
            repo_dir=local_dir,
            target_dir=target_dir,
            progress=progress,
            task_id=copy_task
        )
        
        if not success:
            return False, "Erro ao copiar arquivos para o repositório"
        
        # Make commit task visible
        progress.update(commit_task, visible=True)
        
        # Commit and push changes
        success, message = commit_and_push(
            local_dir=local_dir,
            commit_message=commit_message,
            files_to_add=copied_files,
            branch_name=branch_name,
            progress=progress,
            task_id=commit_task
        )
        
        return success, message