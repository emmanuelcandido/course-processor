"""
Test script for the configuration and credentials management
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import ConfigManager
from config.credentials import CredentialManager

def test_config_manager():
    """Test the ConfigManager class"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test settings file
        settings_file = os.path.join(temp_dir, "settings.json")
        
        # Initialize config manager
        config_manager = ConfigManager(settings_file)
        
        # Test default settings
        assert "directories" in config_manager.settings
        assert "language" in config_manager.settings
        assert "processing" in config_manager.settings
        assert "xml" in config_manager.settings
        
        # Test updating settings
        config_manager.update_setting("directories.work_directory", "/test/dir")
        assert config_manager.get_setting("directories.work_directory") == "/test/dir"
        
        # Test nested settings
        config_manager.update_setting("processing.audio_quality", 256)
        assert config_manager.get_setting("processing.audio_quality") == 256
        
        # Test saving and loading settings
        config_manager.save_settings()
        
        # Create new instance to test loading
        config_manager2 = ConfigManager(settings_file)
        assert config_manager2.get_setting("directories.work_directory") == "/test/dir"
        assert config_manager2.get_setting("processing.audio_quality") == 256
        
        # Test resetting to defaults
        config_manager2.reset_to_defaults()
        # Just check that we can reset and get a value
        assert isinstance(config_manager2.get_setting("directories.work_directory"), str)
        
        # Test exporting settings
        export_file = os.path.join(temp_dir, "export.json")
        config_manager.export_settings(export_file)
        assert os.path.exists(export_file)
        
        # Test importing settings
        config_manager2.import_settings(export_file)
        assert config_manager2.get_setting("directories.work_directory") == "/test/dir"
        
        # Test path validation
        config_manager.update_setting("directories.test_dir", os.path.join(temp_dir, "test_dir"))
        path_status = config_manager.validate_paths()
        assert "test_dir" in path_status
        
        # Test creating missing directories
        dir_status = config_manager.create_missing_directories()
        assert dir_status["test_dir"]
        assert os.path.exists(os.path.join(temp_dir, "test_dir"))
        
        print("All ConfigManager tests passed!")

def test_credential_manager():
    """Test the CredentialManager class"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test credentials file
        credentials_file = os.path.join(temp_dir, "credentials.json")
        
        # Initialize credential manager
        credential_manager = CredentialManager(credentials_file)
        
        # Test storing and retrieving credentials
        credential_manager.store_credential("openai", "api_key", "test-api-key")
        assert credential_manager.retrieve_credential("openai", "api_key") == "test-api-key"
        
        # Test encryption (if available)
        if credential_manager.encryption_key:
            # Check that the stored value is encrypted
            with open(credentials_file, 'r') as f:
                creds = json.load(f)
            
            # The stored value should not be the plain text
            assert creds["openai"]["api_key"] != "test-api-key"
            
            # But retrieving it should give the original value
            assert credential_manager.retrieve_credential("openai", "api_key") == "test-api-key"
        
        # Test deleting credentials
        credential_manager.delete_credential("openai", "api_key")
        assert credential_manager.retrieve_credential("openai", "api_key") == ""
        
        # Test storing multiple credentials
        credential_manager.store_credential("github", "username", "test-user")
        credential_manager.store_credential("github", "token", "test-token")
        
        assert credential_manager.retrieve_credential("github", "username") == "test-user"
        assert credential_manager.retrieve_credential("github", "token") == "test-token"
        
        # Test service status
        services = credential_manager.get_all_services()
        github_service = next((s for s in services if s["name"] == "github"), None)
        assert github_service is not None
        assert github_service["configured"] is True
        
        # Test usage statistics
        credential_manager.update_usage_stats("openai", 1000)
        usage = credential_manager.get_usage_stats("openai")
        assert usage["total_tokens"] == 1000
        
        credential_manager.reset_usage_stats("openai")
        usage = credential_manager.get_usage_stats("openai")
        assert usage["total_tokens"] == 0
        
        print("All CredentialManager tests passed!")

if __name__ == "__main__":
    test_config_manager()
    test_credential_manager()
    print("All tests passed!")