# GitHub Manager Module

The GitHub Manager module provides functionality for managing GitHub repositories.

## Features

- Clone repositories
- Create and manage branches
- Commit and push changes
- Create and manage pull requests
- Sync local and remote repositories

## Usage

### Basic Usage

```python
from modules.github_manager import GitHubManager
from rich.console import Console

console = Console()

# Initialize GitHub manager
github = GitHubManager(
    token="your-github-token",
    username="your-username",
    console=console
)

# Clone a repository
success, result = github.clone_repository(
    repo_url="https://github.com/username/repo.git",
    local_path="/path/to/local/repo"
)

if success:
    print(f"Repository cloned successfully: {result}")
else:
    print(f"Failed to clone repository: {result}")
```

### Managing Branches

```python
# Create a new branch
success, result = github.create_branch(
    repo_path="/path/to/local/repo",
    branch_name="feature/new-feature"
)

if success:
    print(f"Branch created successfully: {result}")
else:
    print(f"Failed to create branch: {result}")

# Switch to a branch
success, result = github.switch_branch(
    repo_path="/path/to/local/repo",
    branch_name="feature/new-feature"
)

if success:
    print(f"Switched to branch: {result}")
else:
    print(f"Failed to switch branch: {result}")
```

### Committing and Pushing Changes

```python
# Commit changes
success, result = github.commit_changes(
    repo_path="/path/to/local/repo",
    commit_message="Add new feature",
    files=["file1.py", "file2.py"]
)

if success:
    print(f"Changes committed successfully: {result}")
else:
    print(f"Failed to commit changes: {result}")

# Push changes
success, result = github.push_changes(
    repo_path="/path/to/local/repo",
    branch_name="feature/new-feature"
)

if success:
    print(f"Changes pushed successfully: {result}")
else:
    print(f"Failed to push changes: {result}")
```

### Creating Pull Requests

```python
# Create a pull request
success, result = github.create_pull_request(
    repo_owner="username",
    repo_name="repo",
    title="Add new feature",
    body="This PR adds a new feature",
    head_branch="feature/new-feature",
    base_branch="main"
)

if success:
    print(f"Pull request created successfully: {result}")
else:
    print(f"Failed to create pull request: {result}")
```

## Class Reference

### GitHubManager

The main class for managing GitHub repositories.

#### Methods

- `clone_repository`: Clone a repository
- `create_branch`: Create a new branch
- `switch_branch`: Switch to a branch
- `commit_changes`: Commit changes
- `push_changes`: Push changes
- `create_pull_request`: Create a pull request
- `get_pull_requests`: Get pull requests
- `merge_pull_request`: Merge a pull request
- `sync_repository`: Sync local and remote repositories

## Dependencies

- pygithub
- gitpython
- rich (for console output)