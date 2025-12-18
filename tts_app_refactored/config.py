"""
Configuration Management for VoiceVerse TTS Application
Handles different environments: development, testing, production
"""

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())

    # Security
    SESSION_COOKIE_SECURE = True  # HTTPS only in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per hour"

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # File Upload
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'docx', 'pdf'}

    # Audio Storage
    AUDIO_FOLDER = BASE_DIR / 'saved_audio'

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_TTS_MODEL = 'tts-1'
    OPENAI_MAX_CHARS = 4096

    # Logging
    LOG_FOLDER = BASE_DIR / 'logs'
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # TTS Settings
    VALID_VOICES = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}
    DEFAULT_VOICE = 'nova'
    MIN_SPEED = 0.25
    MAX_SPEED = 4.0

    # Character Limits
    UI_CHAR_LIMIT = 50000
    API_CHAR_LIMIT = 4096

    # Pagination
    ITEMS_PER_PAGE = 50

    @staticmethod
    def init_app(app):
        """Initialize application configuration"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        f'sqlite:///{BASE_DIR / "dev_database.db"}'
    )

    # Security (relaxed for development)
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing

    # Logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True

    # Database (in-memory)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Security
    WTF_CSRF_ENABLED = False

    # Rate Limiting (disabled for tests)
    RATELIMIT_ENABLED = False

    # Logging
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR / "production.db"}'
    )

    # Security (strict)
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True

    # Logging
    LOG_LEVEL = 'WARNING'

    # Rate Limiting (stricter)
    RATELIMIT_DEFAULT = "50 per hour"

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # Email errors to admins
        import logging
        from logging.handlers import SMTPHandler

        credentials = None
        secure = None

        if getattr(cls, 'MAIL_USERNAME', None):
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.ADMIN_EMAIL],
            subject='VoiceVerse Application Error',
            credentials=credentials,
            secure=secure
        )

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])
