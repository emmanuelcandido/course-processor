# Drive Uploader Module

The Drive Uploader module provides functionality for uploading files to Google Drive.

## Features

- Upload files to Google Drive
- Create and manage folders
- Share files and folders
- List files and folders
- Download files

## Usage

### Basic Usage

```python
from modules.drive_uploader import DriveUploader
from rich.console import Console

console = Console()

# Initialize Drive uploader
drive = DriveUploader(
    credentials_path="/path/to/credentials.json",
    console=console
)

# Upload a file
success, result = drive.upload_file(
    file_path="/path/to/file.mp3",
    folder_id="folder-id",  # Optional
    mime_type="audio/mpeg"  # Optional
)

if success:
    print(f"File uploaded successfully: {result}")
else:
    print(f"Failed to upload file: {result}")
```

### Managing Folders

```python
# Create a folder
success, result = drive.create_folder(
    folder_name="My Folder",
    parent_folder_id="parent-folder-id"  # Optional
)

if success:
    print(f"Folder created successfully: {result}")
else:
    print(f"Failed to create folder: {result}")

# List files in a folder
success, result = drive.list_files(
    folder_id="folder-id",  # Optional
    file_type="audio"  # Optional
)

if success:
    print(f"Files listed successfully:")
    for file in result:
        print(f"- {file['name']} ({file['id']})")
else:
    print(f"Failed to list files: {result}")
```

### Sharing Files

```python
# Share a file
success, result = drive.share_file(
    file_id="file-id",
    email="user@example.com",
    role="reader"  # reader, writer, commenter, owner
)

if success:
    print(f"File shared successfully: {result}")
else:
    print(f"Failed to share file: {result}")
```

### Batch Processing

```python
# Upload multiple files
files = [
    "/path/to/file1.mp3",
    "/path/to/file2.mp3",
    "/path/to/file3.mp3"
]

success, results = drive.batch_upload(
    file_paths=files,
    folder_id="folder-id",  # Optional
    mime_type="audio/mpeg"  # Optional
)

if success:
    print(f"Batch upload completed successfully")
    for file_path, file_id in results.items():
        print(f"{file_path} -> {file_id}")
else:
    print(f"Failed to upload batch: {results}")
```

## Class Reference

### DriveUploader

The main class for uploading files to Google Drive.

#### Methods

- `upload_file`: Upload a file
- `create_folder`: Create a folder
- `list_files`: List files in a folder
- `share_file`: Share a file
- `download_file`: Download a file
- `batch_upload`: Upload multiple files
- `delete_file`: Delete a file
- `get_file_info`: Get file information
- `get_folder_id`: Get folder ID by name

## Dependencies

- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- rich (for console output)