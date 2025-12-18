"""
Pytest Configuration and Fixtures
"""

import pytest
import os
import tempfile
from pathlib import Path
from app import create_app
from app.extensions import db
from app.models import User, Audio, UsageStats


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'

    # Create temp directories
    temp_dir = tempfile.mkdtemp()
    audio_dir = Path(temp_dir) / 'audio'
    audio_dir.mkdir()

    # Create app
    app = create_app('testing')

    # Override config
    app.config['AUDIO_FOLDER'] = audio_dir
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    # Create application context
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def _db(app):
    """Create database for testing"""
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


@pytest.fixture(scope='function')
def client(app, _db):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def user(_db):
    """Create test user"""
    user = User.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    return user


@pytest.fixture
def admin_user(_db):
    """Create admin user"""
    user = User.create_user(
        username='admin',
        password='adminpass123',
        email='admin@example.com'
    )
    user.is_admin = True
    _db.session.commit()
    return user


@pytest.fixture
def auth_client(client, user):
    """Authenticated client"""
    with client:
        client.post('/auth/login', data={
            'username': user.username,
            'password': 'testpass123'
        })
        yield client


@pytest.fixture
def sample_audio(user, _db):
    """Create sample audio file"""
    audio = Audio(
        user_id=user.id,
        filename='test_audio.mp3',
        display_name='Test Audio',
        file_path='/path/to/test_audio.mp3',
        group_name='Test Group',
        voice='nova',
        speed=1.0,
        character_count=100,
        cost=0.0015
    )
    _db.session.add(audio)
    _db.session.commit()
    return audio


@pytest.fixture
def usage_stats(user, _db):
    """Create usage stats"""
    stats = UsageStats.get_or_create(user.id)
    return stats


@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI client"""
    mock_client = mocker.patch('app.services.tts_service.OpenAI')
    mock_response = mocker.MagicMock()
    mock_response.stream_to_file = mocker.MagicMock()
    mock_client.return_value.audio.speech.create.return_value = mock_response
    return mock_client
