"""
Application Factory for VoiceVerse TTS
"""

from flask import Flask
from config import get_config
from app.extensions import init_extensions, db
from app.utils.logger import setup_logging


def create_app(config_name=None):
    """Create and configure Flask application"""

    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Initialize extensions
    init_extensions(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints (routes will be created soon)
    # We'll keep routes simple for now - single file like original

    # Import and register routes (after app context is set up)
    with app.app_context():
        from app import routes

    app.logger.info('VoiceVerse TTS Application started')

    return app
