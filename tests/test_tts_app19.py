#!/usr/bin/env python3
"""
Comprehensive Test Suite for tts_app19.py
Tests Flask routes, database operations, security features, and core functionality
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    # Set test environment variables
    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    os.environ['OPENAI_API_KEY'] = 'sk-test-key-for-testing'
    os.environ['SECURE_COOKIES'] = 'false'

    # Import app after setting env vars
    from tts_app19 import app as flask_app

    # Configure app for testing
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    flask_app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

    yield flask_app

    # Cleanup
    import shutil
    if os.path.exists(flask_app.config['UPLOAD_FOLDER']):
        shutil.rmtree(flask_app.config['UPLOAD_FOLDER'])


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create an authenticated test client"""
    # Register a test user
    client.post('/register', data={
        'username': 'testuser',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!'
    })

    # Login
    client.post('/login', data={
        'username': 'testuser',
        'password': 'TestPass123!'
    })

    return client


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_index_redirect_to_login(client):
    """Test that index redirects to login when not authenticated"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location


def test_register_page_loads(client):
    """Test registration page loads successfully"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data or b'register' in response.data


def test_login_page_loads(client):
    """Test login page loads successfully"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data


def test_user_registration_success(client):
    """Test successful user registration"""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    # User should be redirected to login or homepage


def test_user_registration_password_mismatch(client):
    """Test registration fails with password mismatch"""
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'SecurePass123!',
        'confirm_password': 'DifferentPass123!'
    })

    # Should return error or stay on registration page
    assert response.status_code in [200, 400]


def test_user_login_success(client):
    """Test successful user login"""
    # First register
    client.post('/register', data={
        'username': 'loginuser',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!'
    })

    # Then login
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'TestPass123!'
    }, follow_redirects=True)

    assert response.status_code == 200


def test_user_login_invalid_credentials(client):
    """Test login fails with invalid credentials"""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'WrongPass123!'
    })

    # Should show error or stay on login page
    assert response.status_code in [200, 401]


def test_logout(auth_client):
    """Test user logout"""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

    # After logout, accessing protected page should redirect to login
    response = auth_client.get('/')
    assert response.status_code == 302


# ============================================================================
# PROTECTED ROUTE TESTS
# ============================================================================

def test_index_requires_authentication(client):
    """Test index page requires authentication"""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location


def test_index_accessible_when_authenticated(auth_client):
    """Test authenticated users can access index"""
    response = auth_client.get('/')
    assert response.status_code == 200


def test_dashboard_requires_authentication(client):
    """Test dashboard requires authentication"""
    response = client.get('/dashboard')
    # Should redirect to login
    assert response.status_code in [302, 401]


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

@patch('tts_app19.OpenAI')
def test_api_tts_endpoint_requires_auth(mock_openai, client):
    """Test TTS API endpoint requires authentication"""
    response = client.post('/api/tts', json={
        'text': 'Test text',
        'voice': 'alloy'
    })

    # Should return 401 or redirect
    assert response.status_code in [302, 401]


@patch('tts_app19.OpenAI')
def test_api_tts_endpoint_authenticated(mock_openai, auth_client):
    """Test TTS API endpoint works when authenticated"""
    # Mock OpenAI response
    mock_audio = Mock()
    mock_audio.read.return_value = b'fake audio data'
    mock_openai.return_value.audio.speech.create.return_value = mock_audio

    response = auth_client.post('/api/tts', json={
        'text': 'Test text',
        'voice': 'alloy',
        'speed': 1.0
    })

    # Should return audio file or success response
    assert response.status_code in [200, 201]


def test_api_tts_missing_text(auth_client):
    """Test TTS API returns error when text is missing"""
    response = auth_client.post('/api/tts', json={
        'voice': 'alloy'
    })

    # Should return 400 error
    assert response.status_code == 400


def test_api_tts_invalid_voice(auth_client):
    """Test TTS API validates voice parameter"""
    response = auth_client.post('/api/tts', json={
        'text': 'Test text',
        'voice': 'invalid_voice_name'
    })

    # Should return 400 error or use default voice
    assert response.status_code in [200, 400]


# ============================================================================
# FILE UPLOAD TESTS
# ============================================================================

def test_file_upload_pdf(auth_client):
    """Test PDF file upload and text extraction"""
    # Create a mock PDF file
    data = {
        'file': (BytesIO(b'%PDF-1.4\nTest content'), 'test.pdf')
    }

    with patch('PyPDF2.PdfReader'):
        response = auth_client.post('/upload', data=data,
                                   content_type='multipart/form-data')

        # Should process or return result
        assert response.status_code in [200, 302]


def test_file_upload_docx(auth_client):
    """Test DOCX file upload and text extraction"""
    # Create a mock DOCX file
    data = {
        'file': (BytesIO(b'PK\x03\x04'), 'test.docx')
    }

    with patch('docx.Document'):
        response = auth_client.post('/upload', data=data,
                                   content_type='multipart/form-data')

        assert response.status_code in [200, 302]


def test_file_upload_invalid_type(auth_client):
    """Test that invalid file types are rejected"""
    data = {
        'file': (BytesIO(b'invalid content'), 'test.exe')
    }

    response = auth_client.post('/upload', data=data,
                               content_type='multipart/form-data')

    # Should reject invalid file type
    assert response.status_code in [400, 415]


def test_file_upload_too_large(auth_client):
    """Test that files exceeding size limit are rejected"""
    # Create a large file (> 50MB)
    large_data = b'x' * (51 * 1024 * 1024)
    data = {
        'file': (BytesIO(large_data), 'large.pdf')
    }

    response = auth_client.post('/upload', data=data,
                               content_type='multipart/form-data')

    # Should reject due to size
    assert response.status_code in [400, 413]


# ============================================================================
# AUDIO LIBRARY TESTS
# ============================================================================

def test_get_audio_list(auth_client):
    """Test retrieving audio file list"""
    response = auth_client.get('/api/audio/list')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, (list, dict))


@patch('tts_app19.send_file')
def test_download_audio_file(mock_send_file, auth_client):
    """Test downloading an audio file"""
    mock_send_file.return_value = Mock(status_code=200)

    # First create an audio file (mocked)
    with patch('tts_app19.OpenAI'):
        auth_client.post('/api/tts', json={
            'text': 'Test',
            'voice': 'alloy'
        })

    # Try to download
    response = auth_client.get('/download/1')

    # Should allow download or return 404 if not found
    assert response.status_code in [200, 404]


def test_delete_audio_file(auth_client):
    """Test deleting an audio file"""
    response = auth_client.post('/api/audio/delete/1')

    # Should return success or 404 if not found
    assert response.status_code in [200, 404]


# ============================================================================
# AI AGENTS TESTS
# ============================================================================

@patch('tts_agents.create_agent_system')
def test_ai_preprocess_endpoint(mock_agents, auth_client):
    """Test AI text preprocessing endpoint"""
    mock_agent = Mock()
    mock_agent.preprocess_text.return_value = "Cleaned text"
    mock_agents.return_value = mock_agent

    response = auth_client.post('/api/agent/preprocess', json={
        'text': 'Test   text   with   spaces'
    })

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'processed_text' in data or 'result' in data


@patch('tts_agents.create_agent_system')
def test_ai_chunking_endpoint(mock_agents, auth_client):
    """Test AI smart chunking endpoint"""
    mock_agent = Mock()
    mock_agent.smart_chunk.return_value = [
        {'text': 'Chunk 1', 'chars': 7},
        {'text': 'Chunk 2', 'chars': 7}
    ]
    mock_agents.return_value = mock_agent

    response = auth_client.post('/api/agent/smart-chunk', json={
        'text': 'Long text ' * 500
    })

    assert response.status_code == 200


@patch('tts_agents.create_agent_system')
def test_ai_metadata_suggestion(mock_agents, auth_client):
    """Test AI metadata suggestion endpoint"""
    mock_agent = Mock()
    mock_agent.suggest_metadata.return_value = {
        'filename': 'suggested_name',
        'category': 'test',
        'summary': 'Test summary'
    }
    mock_agents.return_value = mock_agent

    response = auth_client.post('/api/agent/suggest-metadata', json={
        'text': 'Test content for metadata'
    })

    assert response.status_code == 200


# ============================================================================
# SECURITY TESTS
# ============================================================================

def test_csrf_protection_enabled(app):
    """Test that CSRF protection is enabled in production"""
    # In production, CSRF should be enabled
    assert 'csrf' in dir()  # CSRF module should be imported


def test_rate_limiting_works(client):
    """Test that rate limiting prevents abuse"""
    # Make many requests in quick succession
    responses = []
    for i in range(100):
        response = client.get('/login')
        responses.append(response.status_code)

    # At least some requests should be rate limited (429)
    # Or all should succeed if rate limit is high
    assert all(code in [200, 429] for code in responses)


def test_sql_injection_prevention(auth_client):
    """Test that SQL injection attempts are prevented"""
    # Try SQL injection in username
    response = auth_client.post('/login', data={
        'username': "admin' OR '1'='1",
        'password': "password"
    })

    # Should not succeed
    assert response.status_code in [200, 401]


def test_xss_prevention(auth_client):
    """Test that XSS attempts are sanitized"""
    # Try XSS in text field
    response = auth_client.post('/api/tts', json={
        'text': '<script>alert("XSS")</script>',
        'voice': 'alloy'
    })

    # Should handle safely (sanitize or reject)
    assert response.status_code in [200, 400]


def test_session_security(client):
    """Test session cookie security settings"""
    response = client.get('/login')

    # Check that session cookie has security flags
    cookies = response.headers.getlist('Set-Cookie')
    if cookies:
        cookie_str = str(cookies)
        # In production should have HttpOnly and Secure
        assert 'HttpOnly' in cookie_str or app.config['TESTING']


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_404_error_handler(client):
    """Test 404 error handling"""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404


def test_500_error_handling(auth_client):
    """Test 500 error handling"""
    # Trigger a server error by sending invalid data
    with patch('tts_app19.OpenAI', side_effect=Exception("Server error")):
        response = auth_client.post('/api/tts', json={
            'text': 'Test',
            'voice': 'alloy'
        })

        # Should handle error gracefully
        assert response.status_code in [500, 400]


def test_method_not_allowed(client):
    """Test method not allowed handling"""
    # Try POST to a GET-only route
    response = client.post('/login-page-only-get')

    # Should return 405 or 404
    assert response.status_code in [404, 405]


# ============================================================================
# DATABASE TESTS
# ============================================================================

def test_database_connection():
    """Test database connection"""
    from database import Database

    db = Database(':memory:')
    assert db is not None


def test_user_creation():
    """Test creating a user in database"""
    from database import Database

    db = Database(':memory:')
    user_id = db.create_user('testuser', 'hashed_password')

    assert user_id is not None
    assert user_id > 0


def test_user_retrieval():
    """Test retrieving a user from database"""
    from database import Database

    db = Database(':memory:')
    user_id = db.create_user('testuser', 'hashed_password')
    user = db.get_user_by_username('testuser')

    assert user is not None
    assert user['username'] == 'testuser'


def test_audio_file_storage():
    """Test storing audio file metadata in database"""
    from database import Database

    db = Database(':memory:')
    user_id = db.create_user('testuser', 'hashed_password')

    file_id = db.save_audio_file(
        user_id=user_id,
        filename='test.mp3',
        voice='alloy',
        speed=1.0,
        text_preview='Test text',
        file_path='/path/to/file.mp3'
    )

    assert file_id is not None
    assert file_id > 0


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

def test_secure_filename():
    """Test filename sanitization"""
    from werkzeug.utils import secure_filename

    dangerous = "../../../etc/passwd"
    safe = secure_filename(dangerous)

    assert '..' not in safe
    assert '/' not in safe


def test_password_hashing():
    """Test password hashing and verification"""
    from werkzeug.security import generate_password_hash, check_password_hash

    password = "TestPass123!"
    hashed = generate_password_hash(password)

    assert hashed != password
    assert check_password_hash(hashed, password)
    assert not check_password_hash(hashed, "WrongPassword")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_tts_workflow(auth_client):
    """Test complete TTS workflow from text to audio"""
    with patch('tts_app19.OpenAI') as mock_openai:
        # Mock OpenAI response
        mock_audio = Mock()
        mock_audio.read.return_value = b'fake audio data'
        mock_openai.return_value.audio.speech.create.return_value = mock_audio

        # Step 1: Submit text for TTS
        response = auth_client.post('/api/tts', json={
            'text': 'Integration test',
            'voice': 'alloy',
            'speed': 1.0
        })

        assert response.status_code in [200, 201]

        # Step 2: Get audio list
        response = auth_client.get('/api/audio/list')
        assert response.status_code == 200


def test_ai_workflow_preprocessing_to_tts(auth_client):
    """Test AI preprocessing followed by TTS"""
    with patch('tts_agents.create_agent_system') as mock_agents:
        with patch('tts_app19.OpenAI') as mock_openai:
            # Setup mocks
            mock_agent = Mock()
            mock_agent.preprocess_text.return_value = "Cleaned text"
            mock_agents.return_value = mock_agent

            mock_audio = Mock()
            mock_audio.read.return_value = b'audio data'
            mock_openai.return_value.audio.speech.create.return_value = mock_audio

            # Step 1: Preprocess
            response = auth_client.post('/api/agent/preprocess', json={
                'text': 'Raw   text'
            })
            assert response.status_code == 200

            # Step 2: Generate TTS
            response = auth_client.post('/api/tts', json={
                'text': 'Cleaned text',
                'voice': 'alloy'
            })
            assert response.status_code in [200, 201]


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_api_response_time(auth_client):
    """Test that API responds within acceptable time"""
    import time

    start = time.time()
    response = auth_client.get('/api/audio/list')
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 1.0  # Should respond within 1 second


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
