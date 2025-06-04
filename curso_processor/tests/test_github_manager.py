"""
Test script for the GitHubManager class
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.github_manager import GitHubManager
from config import credentials

def test_github_manager():
    """Test the GitHubManager class"""
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp()
    
    try:
        # Initialize GitHub manager
        manager = GitHubManager(repo_path=test_dir)
        
        # Test repository setup
        success, message = manager.setup_repository()
        assert success, f"Repository setup failed: {message}"
        assert manager.is_valid_repository(), "Repository should be valid after setup"
        
        # Test git config validation
        assert manager.validate_git_config(), "Git config should be valid after setup"
        
        # Create test XML file
        xml_dir = os.path.join(test_dir, "xml")
        os.makedirs(xml_dir, exist_ok=True)
        xml_path = os.path.join(xml_dir, "feed.xml")
        
        with open(xml_path, "w") as f:
            f.write("<xml>Test Feed</xml>")
        
        # Test commit XML changes
        success, message = manager.commit_xml_changes(xml_path)
        assert success, f"Commit XML changes failed: {message}"
        
        # Update XML file
        with open(xml_path, "w") as f:
            f.write("<xml>Updated Test Feed</xml>")
        
        # Test commit XML changes with custom message
        success, message = manager.commit_xml_changes(xml_path, "Update test feed")
        assert success, f"Commit XML changes with custom message failed: {message}"
        
        print("All GitHubManager tests passed!")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)

def test_remote_operations():
    """Test remote operations (requires valid credentials)"""
    # Skip if no credentials
    github_creds = credentials.get_github_credentials()
    if not github_creds.get("username") or not github_creds.get("token"):
        print("Skipping remote operations test (no credentials)")
        return
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp()
    
    try:
        # Initialize GitHub manager
        manager = GitHubManager(repo_path=test_dir)
        
        # Set up repository with remote URL
        # Note: This is a test repository that should exist
        remote_url = "https://github.com/test-user/test-repo.git"
        success, message = manager.setup_repository(remote_url)
        assert success, f"Repository setup with remote failed: {message}"
        
        # Create test XML file
        xml_dir = os.path.join(test_dir, "xml")
        os.makedirs(xml_dir, exist_ok=True)
        xml_path = os.path.join(xml_dir, "feed.xml")
        
        with open(xml_path, "w") as f:
            f.write("<xml>Test Feed</xml>")
        
        # Test commit XML changes
        success, message = manager.commit_xml_changes(xml_path)
        assert success, f"Commit XML changes failed: {message}"
        
        # Note: We don't actually push to remote in tests
        # Just verify the URL generation
        xml_url = manager.get_public_xml_url("feed.xml")
        assert "raw.githubusercontent.com" in xml_url, f"Invalid XML URL: {xml_url}"
        
        print("All remote operations tests passed!")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_github_manager()
    # Uncomment to test remote operations (requires valid credentials)
    # test_remote_operations()
    print("All tests passed!")