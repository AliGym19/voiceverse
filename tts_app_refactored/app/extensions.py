"""
Flask Extensions Initialization
Centralized location for all Flask extensions
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


def init_extensions(app):
    """Initialize Flask extensions with app"""

    # Database
    db.init_app(app)

    # Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Rate Limiter
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
