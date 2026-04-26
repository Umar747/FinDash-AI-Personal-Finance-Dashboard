import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import jwt
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server import app

TEST_SECRET = "a_very_long_and_secure_secret_key_for_testing_32_chars"

# Initialise the Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = TEST_SECRET
    with app.test_client() as client:
        yield client

# Generate a valid JWT token header for testing protected routes
@pytest.fixture
def auth_header():
    token = jwt.encode({
        'user_id': 1,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, TEST_SECRET, algorithm="HS256")
    return {'Authorization': f'Bearer {token}'}

# Password Validation Tests - Does the password security logic work?
def test_password_check():
    from server import password_check
    
    # Failures
    assert password_check("short")[0] is False # Too short
    assert password_check("NoNumber!")[0] is False # Missing number
    assert password_check("nonuppercase1!")[0] is False # Missing uppercase
    assert password_check("NoSpecial1")[0] is False # Missing special char
    
    # Success
    assert password_check("StrongPass1!")[0] is True

# File Validation Tests - Are only CSV files accepted?
def test_allowed_file():
    from server import allowed_file
    assert allowed_file("data.csv") is True
    assert allowed_file("image.png") is False
    assert allowed_file("script.py") is False

# Auth Routes - Does the Signup and Login work?
@patch('server.get_db_connection')
def test_signup_success(mock_db, client):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = [1] # Return user_id
    mock_db.return_value = mock_conn

    response = client.post('/auth/signup', json={
        'username': 'new_unique_user',
        'password': 'Password123!'
    })
    
    assert response.status_code == 201
    assert response.get_json()['message'] == 'User created successfully'

# Protected Routes - Does transaction retrieval work?
@patch('server.get_db_connection')
def test_get_all_transactions(mock_db, client, auth_header):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value

    # Mock database rows (id, date, name, amount, category, account)
    mock_cur.fetchall.return_value = [
        (1, '2024-01-01', 'Salary', 3000.0, 'Income', 'HSBC')
    ]
    mock_db.return_value = mock_conn

    response = client.get('/transactions', headers=auth_header)
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['transactions']) == 1
    assert data['transactions'][0]['description'] == 'Salary'

# Error Handling - Is unauthorised access stopped?
def test_unauthorized_access(client):
    response = client.get('/transactions')
    assert response.status_code == 401
    assert response.get_json()['message'] == 'Token is missing!'

# Transaction Creation - Are positive transactions categorised properly?
@patch('server.get_db_connection')
@patch('server.model.predict_single')
@patch('server.nlp.transform_embeddings')
def test_create_transaction_logic(mock_nlp, mock_model, mock_db, client, auth_header):
    mock_conn = MagicMock()
    mock_cur = mock_conn.cursor.return_value
    mock_cur.fetchone.return_value = [101] # New ID
    mock_db.return_value = mock_conn

    # Test Income (positive amount)
    response = client.post('/transactions', json={
        'date': '2024-01-01',
        'description': 'Bonus',
        'amount': 500,
        'account_id': 1
    }, headers=auth_header)
    
    assert response.status_code == 201
    # Check that it didn't call the ML model for positive amounts
    assert not mock_model.called

# AI Agent Chat Route - Is the AI agent working properly?
@patch('server.ask_finance_agent')
def test_chat_with_agent(mock_agent, client, auth_header):
    mock_agent.return_value = "I have added your transaction."
    
    response = client.post('/api/chat', json={'message': 'Add a £5 transaction for coffee'}, headers=auth_header)
    
    assert response.status_code == 200
    assert response.get_json()['response'] == "I have added your transaction."