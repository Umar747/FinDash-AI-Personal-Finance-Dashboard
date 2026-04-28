import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.database import get_db_connection

# Environment Variables Test - Does it read from .env correctly?
def test_db_connection_env_loading():
    with patch('psycopg2.connect') as mock_connect:
        # Mock the environment to ensure consistency
        with patch.dict(os.environ, {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password'
        }):
            get_db_connection()
            
            # Check that psycopg2.connect was called with the expected arguments
            mock_connect.assert_called_once_with(
                host='localhost',
                port='5432',
                database='test_db',
                user='test_user',
                password='test_password'
            )

# Success Case - Does it return a connection object?
def test_get_db_connection_success():
    with patch('psycopg2.connect') as mock_connect:
        # Create a mock connection object
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        conn = get_db_connection()
        
        assert conn == mock_conn
        assert mock_connect.called

# Error Handling - How does it handle connection failures?
def test_get_db_connection_failure():
    with patch('psycopg2.connect') as mock_connect:
        # Simulate a connection timeout or authentication failure
        mock_connect.side_effect = Exception("Connection refused")
        
        with pytest.raises(Exception) as excinfo:
            get_db_connection()
        
        assert "Connection refused" in str(excinfo.value)

# Integration Check - Are all required env variables present?
def test_required_env_variables_presence():
    required_keys = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    
    # Mock both os.getenv and psycopg2.connect
    with patch('os.getenv') as mock_getenv, patch('psycopg2.connect') as mock_connect:
        get_db_connection()
        
        # Get all keys that os.getenv was called with
        called_keys = [call[0][0] for call in mock_getenv.call_args_list]
        
        for key in required_keys:
            assert key in called_keys, f"Database logic failed to request environment variable: {key}"
            
        # Check that connect was actually called with the results of getenv
        assert mock_connect.called