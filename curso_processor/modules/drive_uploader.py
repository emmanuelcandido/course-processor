"""
Google Drive uploader module for Curso Processor
Handles uploading files to Google Drive and managing permissions
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from pydantic import BaseModel

from utils import ui_components
from config import credentials

# Import Google API libraries
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False


class GoogleDriveManager:
    """
    Class for managing Google Drive operations
    """
    
    # Define scopes for Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self, 
                 credentials_path: str = None, 
                 token_path: str = None,
                 console: Optional[Console] = None):
        """
        Initialize the Google Drive manager
        
        Args:
            credentials_path: Path to credentials file (service account or OAuth client)
            token_path: Path to token file (for OAuth)
            console: Rich console for output
        """
        self.console = console or Console()
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.authenticated = False
        self.folder_cache = {}
        self.retry_count = 3
        self.retry_delay = 2  # seconds
    
    def authenticate(self, auth_type: str = "oauth") -> bool:
        """
        Authenticate with Google Drive API
        
        Args:
            auth_type: Authentication type ('service_account' or 'oauth')
            
        Returns:
            Success status
        """
        if not GOOGLE_APIS_AVAILABLE:
            self.console.print("[bold red]Google API libraries not available. Install with 'pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib'[/bold red]")
            return False
        
        try:
            creds = None
            
            if auth_type == "service_account":
                if not self.credentials_path or not os.path.exists(self.credentials_path):
                    self.console.print("[bold red]Service account credentials file not found[/bold red]")
                    return False
                
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.SCOPES
                )
            
            elif auth_type == "oauth":
                # Get Google credentials from config
                google_creds = credentials.get_google_credentials()
                
                if not google_creds.get("client_id") or not google_creds.get("client_secret"):
                    self.console.print("[bold red]Credenciais do Google não configuradas[/bold red]")
                    return False
                
                # Check if we have a refresh token
                if google_creds.get("refresh_token"):
                    creds = Credentials.from_authorized_user_info({
                        "client_id": google_creds["client_id"],
                        "client_secret": google_creds["client_secret"],
                        "refresh_token": google_creds["refresh_token"]
                    })
                
                # If no valid credentials, we need to authenticate
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_config(
                            {
                                "installed": {
                                    "client_id": google_creds["client_id"],
                                    "client_secret": google_creds["client_secret"],
                                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                    "token_uri": "https://oauth2.googleapis.com/token",
                                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                                }
                            },
                            self.SCOPES
                        )
                        creds = flow.run_local_server(port=0)
                    
                    # Save the credentials for the next run
                    credentials.set_google_credentials(
                        refresh_token=creds.refresh_token
                    )
            
            else:
                self.console.print(f"[bold red]Invalid authentication type: {auth_type}[/bold red]")
                return False
            
            # Build the Drive API service
            self.service = build('drive', 'v3', credentials=creds)
            self.authenticated = True
            
            self.console.print("[bold green]Successfully authenticated with Google Drive[/bold green]")
            return True
        
        except Exception as e:
            self.console.print(f"[bold red]Authentication failed: {str(e)}[/bold red]")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure the service is authenticated"""
        if not self.authenticated or not self.service:
            return self.authenticate()
        return True
    
    def validate_folder_id(self, folder_id: str) -> bool:
        """
        Validate if a folder ID exists
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            True if folder exists, False otherwise
        """
        if not self._ensure_authenticated():
            return False
        
        try:
            file = self.service.files().get(fileId=folder_id, fields="id, name, mimeType").execute()
            return file.get('mimeType') == 'application/vnd.google-apps.folder'
        except Exception:
            return False
    
    def get_folder_id(self, folder_name: str, parent_id: str = None) -> Tuple[bool, str]:
        """
        Get folder ID by name
        
        Args:
            folder_name: Folder name
            parent_id: Parent folder ID (optional)
            
        Returns:
            Tuple of (success, folder_id or error message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Check cache first
            cache_key = f"{parent_id}:{folder_name}" if parent_id else f"root:{folder_name}"
            if cache_key in self.folder_cache:
                return True, self.folder_cache[cache_key]
            
            # Build query
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            # Execute query
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                # Cache the result
                self.folder_cache[cache_key] = folder_id
                return True, folder_id
            else:
                return False, f"Folder '{folder_name}' not found"
        
        except Exception as e:
            return False, f"Error getting folder ID: {str(e)}"
    
    def create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Folder name
            parent_id: Parent folder ID (optional)
            
        Returns:
            Folder ID if successful, None otherwise
        """
        if not self._ensure_authenticated():
            return None
        
        try:
            # Check if folder already exists
            exists, result = self.get_folder_id(folder_name, parent_id)
            if exists:
                return result
            
            # Create folder metadata
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            # Create folder
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            
            # Cache the result
            cache_key = f"{parent_id}:{folder_name}" if parent_id else f"root:{folder_name}"
            self.folder_cache[cache_key] = folder_id
            
            return folder_id
        
        except Exception as e:
            self.console.print(f"[bold red]Error creating folder: {str(e)}[/bold red]")
            return None
    
    def create_course_folder(self, course_name: str, base_folder_id: str) -> Tuple[bool, str]:
        """
        Create a course folder structure
        
        Args:
            course_name: Course name
            base_folder_id: Base folder ID (Cursos)
            
        Returns:
            Tuple of (success, folder_id or error message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Validate base folder
            if not self.validate_folder_id(base_folder_id):
                return False, f"Base folder ID '{base_folder_id}' is invalid"
            
            # Create course folder
            success, result = self.create_folder(course_name, base_folder_id)
            if not success:
                return False, result
            
            return True, result
        
        except Exception as e:
            return False, f"Error creating course folder: {str(e)}"
    
    def handle_duplicate_files(self, file_name: str, parent_id: str = None) -> Tuple[bool, str]:
        """
        Handle duplicate files in Google Drive
        
        Args:
            file_name: File name
            parent_id: Parent folder ID (optional)
            
        Returns:
            Tuple of (success, file_id or None)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Build query
            query = f"name = '{file_name}' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            # Execute query
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                # Return the first file ID
                return True, items[0]['id']
            
            return True, None
        
        except Exception as e:
            return False, f"Error handling duplicate files: {str(e)}"
    
    def upload_file(self, file_path: str, folder_id: str = None, mime_type: str = None,
                   progress: Optional[Progress] = None, task_id: Optional[int] = None) -> str:
        """
        Upload a file to Google Drive
        
        Args:
            file_path: Path to the file
            folder_id: Folder ID (optional)
            mime_type: MIME type (optional)
            progress: Rich progress object
            task_id: Task ID for progress tracking
            
        Returns:
            File ID if successful, None otherwise
        """
        if not self._ensure_authenticated():
            return None
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                self.console.print(f"[bold red]File '{file_path}' not found[/bold red]")
                return None
            
            # Get file name
            file_name = os.path.basename(file_path)
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, description=f"Fazendo upload de {file_name}")
            
            # Check for duplicates
            if folder_id:
                success, duplicate_id = self.handle_duplicate_files(file_name, folder_id)
                if success and duplicate_id:
                    # Delete the duplicate file
                    self.service.files().delete(fileId=duplicate_id).execute()
            
            # Create file metadata
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Determine MIME type if not provided
            if not mime_type:
                if file_path.endswith('.mp3'):
                    mime_type = 'audio/mpeg'
                elif file_path.endswith('.wav'):
                    mime_type = 'audio/wav'
                elif file_path.endswith('.m4a'):
                    mime_type = 'audio/mp4'
                elif file_path.endswith('.pdf'):
                    mime_type = 'application/pdf'
                elif file_path.endswith('.txt'):
                    mime_type = 'text/plain'
                elif file_path.endswith('.md'):
                    mime_type = 'text/markdown'
                else:
                    mime_type = 'application/octet-stream'
            
            # Get file size for progress tracking
            file_size = os.path.getsize(file_path)
            
            # Create media
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            # Create the file
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            )
            
            # Upload with progress tracking
            if progress and task_id is not None:
                # Use the existing progress bar
                response = None
                last_progress = 0
                
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        current = status.resumable_progress
                        progress.update(
                            task_id, 
                            description=f"Uploading {file_name} - {current / (1024 * 1024):.2f} MB"
                        )
                        last_progress = current
            else:
                # Create a new progress bar
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TextColumn("[bold green]{task.completed:.2f}/{task.total:.2f} MB"),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    console=self.console
                ) as progress:
                    upload_task = progress.add_task(
                        f"[cyan]Uploading {file_name}[/cyan]", 
                        total=file_size / (1024 * 1024)  # Convert to MB
                    )
                    
                    response = None
                    last_progress = 0
                    
                    while response is None:
                        status, response = request.next_chunk()
                        if status:
                            current = status.resumable_progress
                            progress.update(
                                upload_task, 
                                completed=current / (1024 * 1024),  # Convert to MB
                                description=f"[cyan]Uploading {file_name} - {current / (1024 * 1024):.2f} MB[/cyan]"
                            )
                            last_progress = current
            
            # Update progress if provided
            if progress and task_id is not None:
                progress.update(task_id, advance=1)
            
            file_id = response.get('id')
            
            return file_id
        
        except Exception as e:
            self.console.print(f"[bold red]Error uploading file: {str(e)}[/bold red]")
            return None
    
    def upload_audio_file(self, audio_path: str, course_name: str, base_folder_id: str) -> Tuple[bool, str]:
        """
        Upload an audio file to a course folder
        
        Args:
            audio_path: Path to the audio file
            course_name: Course name
            base_folder_id: Base folder ID (Cursos)
            
        Returns:
            Tuple of (success, file_id or error message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Create course folder
            success, course_folder_id = self.create_course_folder(course_name, base_folder_id)
            if not success:
                return False, course_folder_id
            
            # Upload audio file
            success, file_id = self.upload_file(audio_path, course_folder_id)
            if not success:
                return False, file_id
            
            return True, file_id
        
        except Exception as e:
            return False, f"Error uploading audio file: {str(e)}"
    
    def set_public_permissions(self, file_id: str) -> Tuple[bool, str]:
        """
        Make a file publicly accessible
        
        Args:
            file_id: File ID
            
        Returns:
            Tuple of (success, message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Create permission
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            # Apply permission
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            return True, "File is now publicly accessible"
        
        except Exception as e:
            return False, f"Error setting permissions: {str(e)}"
    
    def get_direct_download_url(self, file_id: str) -> str:
        """
        Get direct download URL for a file
        
        Args:
            file_id: File ID
            
        Returns:
            Direct download URL
        """
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    def get_podcast_url(self, file_id: str) -> str:
        """
        Get podcast-compatible URL for a file
        
        Args:
            file_id: File ID
            
        Returns:
            Podcast-compatible URL
        """
        return f"https://drive.google.com/uc?export=download&id={file_id}"
        
    def share_folder(self, folder_id: str) -> str:
        """
        Share a folder publicly
        
        Args:
            folder_id: Folder ID
            
        Returns:
            Sharing link if successful, None otherwise
        """
        if not self._ensure_authenticated():
            return None
        
        try:
            # Create permission
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            # Apply permission
            self.service.permissions().create(
                fileId=folder_id,
                body=permission
            ).execute()
            
            # Get sharing link
            file = self.service.files().get(
                fileId=folder_id,
                fields='webViewLink'
            ).execute()
            
            return file.get('webViewLink')
        
        except Exception as e:
            self.console.print(f"[bold red]Error sharing folder: {str(e)}[/bold red]")
            return None
    
    def batch_upload(self, file_paths: List[str], folder_id: str = None) -> Tuple[bool, Dict[str, str]]:
        """
        Upload multiple files to Google Drive
        
        Args:
            file_paths: List of file paths
            folder_id: Folder ID (optional)
            
        Returns:
            Tuple of (success, dict of file_path -> file_id)
        """
        if not self._ensure_authenticated():
            return False, {"error": "Not authenticated"}
        
        results = {}
        all_success = True
        
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold green]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            main_task = progress.add_task(
                f"[cyan]Uploading {len(file_paths)} files[/cyan]", 
                total=len(file_paths)
            )
            
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    results[file_path] = f"File not found"
                    all_success = False
                    progress.update(main_task, advance=1)
                    continue
                
                file_name = os.path.basename(file_path)
                progress.update(main_task, description=f"[cyan]Uploading {file_name}[/cyan]")
                
                success, result = self.upload_file(
                    file_path, 
                    folder_id,
                    progress=progress,
                    task_id=main_task
                )
                
                if success:
                    results[file_path] = result
                else:
                    results[file_path] = result
                    all_success = False
                
                progress.update(main_task, advance=1)
        
        return all_success, results
    
    def monitor_upload_progress(self, request, file_name: str, file_size: int) -> Tuple[bool, str]:
        """
        Monitor upload progress for a file
        
        Args:
            request: Upload request
            file_name: File name
            file_size: File size in bytes
            
        Returns:
            Tuple of (success, file_id or error message)
        """
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[bold green]{task.completed:.2f}/{task.total:.2f} MB"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Uploading {file_name}[/cyan]", 
                total=file_size / (1024 * 1024)  # Convert to MB
            )
            
            response = None
            last_progress = 0
            
            while response is None:
                status, response = request.next_chunk()
                if status:
                    current = status.resumable_progress
                    progress.update(
                        task, 
                        completed=current / (1024 * 1024),  # Convert to MB
                        description=f"[cyan]Uploading {file_name} - {current / (1024 * 1024):.2f} MB[/cyan]"
                    )
                    last_progress = current
        
        if response:
            return True, response.get('id')
        else:
            return False, "Upload failed"
    
    def list_files(self, folder_id: str = None, file_type: str = None) -> Tuple[bool, List[Dict]]:
        """
        List files in a folder
        
        Args:
            folder_id: Folder ID (optional)
            file_type: File type filter (optional)
            
        Returns:
            Tuple of (success, list of files)
        """
        if not self._ensure_authenticated():
            return False, ["Not authenticated"]
        
        try:
            # Build query
            query = "trashed = false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
            if file_type:
                if file_type.lower() == 'audio':
                    query += " and (mimeType contains 'audio/')"
                elif file_type.lower() == 'video':
                    query += " and (mimeType contains 'video/')"
                elif file_type.lower() == 'image':
                    query += " and (mimeType contains 'image/')"
                elif file_type.lower() == 'document':
                    query += " and (mimeType contains 'text/' or mimeType contains 'application/pdf')"
            
            # Execute query
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, createdTime, webViewLink)'
            ).execute()
            
            files = results.get('files', [])
            
            return True, files
        
        except Exception as e:
            return False, [f"Error listing files: {str(e)}"]
    
    def share_file(self, file_id: str, email: str, role: str = 'reader') -> Tuple[bool, str]:
        """
        Share a file with a user
        
        Args:
            file_id: File ID
            email: User email
            role: Permission role (reader, writer, commenter, owner)
            
        Returns:
            Tuple of (success, message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Create permission
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            # Apply permission
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            return True, f"File shared with {email}"
        
        except Exception as e:
            return False, f"Error sharing file: {str(e)}"
    
    def download_file(self, file_id: str, output_path: str) -> Tuple[bool, str]:
        """
        Download a file from Google Drive
        
        Args:
            file_id: File ID
            output_path: Output file path
            
        Returns:
            Tuple of (success, message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            # Get file metadata
            file = self.service.files().get(fileId=file_id, fields="name, size").execute()
            file_name = file.get('name')
            file_size = int(file.get('size', 0))
            
            # Create request
            request = self.service.files().get_media(fileId=file_id)
            
            # Download with progress tracking
            with open(output_path, 'wb') as f:
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TextColumn("[bold green]{task.completed:.2f}/{task.total:.2f} MB"),
                    TimeElapsedColumn(),
                    TimeRemainingColumn(),
                    console=self.console
                ) as progress:
                    task = progress.add_task(
                        f"[cyan]Downloading {file_name}[/cyan]", 
                        total=file_size / (1024 * 1024)  # Convert to MB
                    )
                    
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            progress.update(
                                task, 
                                completed=status.resumable_progress / (1024 * 1024),  # Convert to MB
                                description=f"[cyan]Downloading {file_name} - {status.resumable_progress / (1024 * 1024):.2f} MB[/cyan]"
                            )
            
            return True, f"File downloaded to {output_path}"
        
        except Exception as e:
            return False, f"Error downloading file: {str(e)}"
    
    def delete_file(self, file_id: str) -> Tuple[bool, str]:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: File ID
            
        Returns:
            Tuple of (success, message)
        """
        if not self._ensure_authenticated():
            return False, "Not authenticated"
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True, "File deleted"
        
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def get_file_info(self, file_id: str) -> Tuple[bool, Dict]:
        """
        Get file information
        
        Args:
            file_id: File ID
            
        Returns:
            Tuple of (success, file info)
        """
        if not self._ensure_authenticated():
            return False, {"error": "Not authenticated"}
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink"
            ).execute()
            
            return True, file
        
        except Exception as e:
            return False, {"error": f"Error getting file info: {str(e)}"}


# Legacy functions for backward compatibility
def upload_file_to_drive(file_path: str, folder_id: Optional[str] = None,
                       progress: Optional[Progress] = None,
                       task_id: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Upload a file to Google Drive
    
    Args:
        file_path: Path to the file
        folder_id: Google Drive folder ID (if None, upload to root)
        progress: Rich progress object
        task_id: Task ID for progress tracking
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and file info or error message
    """
    console = Console()
    drive_manager = GoogleDriveManager(console=console)
    
    # Authenticate
    if not drive_manager.authenticate(auth_type="oauth"):
        return False, {"error": "Authentication failed"}
    
    # Upload file
    success, result = drive_manager.upload_file(
        file_path=file_path,
        folder_id=folder_id,
        progress=progress,
        task_id=task_id
    )
    
    if success:
        return True, {
            "id": result,
            "name": os.path.basename(file_path),
            "link": drive_manager.get_direct_download_url(result)
        }
    else:
        return False, {"error": result}

def create_drive_folder(folder_name: str, parent_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Create a folder in Google Drive
    
    Args:
        folder_name: Name of the folder
        parent_id: Parent folder ID (if None, create in root)
        
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and folder info or error message
    """
    console = Console()
    drive_manager = GoogleDriveManager(console=console)
    
    # Authenticate
    if not drive_manager.authenticate(auth_type="oauth"):
        return False, {"error": "Authentication failed"}
    
    # Create folder
    success, result = drive_manager.create_folder(
        folder_name=folder_name,
        parent_id=parent_id
    )
    
    if success:
        return True, {
            "id": result,
            "name": folder_name,
            "link": f"https://drive.google.com/drive/folders/{result}"
        }
    else:
        return False, {"error": result}

def batch_upload_files(file_paths: List[str], folder_name: Optional[str] = None) -> List[Tuple[bool, Dict[str, Any]]]:
    """
    Upload multiple files to Google Drive
    
    Args:
        file_paths: List of file paths
        folder_name: Name of the folder to create (if None, upload to root)
        
    Returns:
        List[Tuple[bool, Dict[str, Any]]]: List of results (success status and file info or error message)
    """
    console = Console()
    drive_manager = GoogleDriveManager(console=console)
    
    # Authenticate
    if not drive_manager.authenticate(auth_type="oauth"):
        return [(False, {"error": "Authentication failed"}) for _ in file_paths]
    
    # Create folder if needed
    folder_id = None
    if folder_name:
        success, result = drive_manager.create_folder(folder_name)
        if success:
            folder_id = result
            ui_components.print_success(f"Pasta criada: {folder_name} (ID: {folder_id})")
        else:
            ui_components.print_error(f"Erro ao criar pasta: {result}")
            return [(False, {"error": f"Failed to create folder: {result}"}) for _ in file_paths]
    
    # Create progress bar
    progress = ui_components.create_progress_bar("Fazendo upload para o Google Drive")
    
    results = []
    
    with progress:
        # Add task
        task = progress.add_task("Iniciando upload...", total=len(file_paths))
        
        # Upload each file
        for file_path in file_paths:
            success, result = drive_manager.upload_file(
                file_path=file_path,
                folder_id=folder_id,
                progress=progress,
                task_id=task
            )
            
            if success:
                results.append((True, {
                    "id": result,
                    "name": os.path.basename(file_path),
                    "link": drive_manager.get_direct_download_url(result)
                }))
            else:
                results.append((False, {"error": result}))
    
    # Count successful uploads
    successful = sum(1 for result in results if result[0])
    
    # Print summary
    ui_components.print_success(f"Upload concluído: {successful}/{len(file_paths)} arquivos enviados com sucesso")
    
    return results