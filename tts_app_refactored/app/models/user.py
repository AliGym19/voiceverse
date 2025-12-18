"""
User Model - Handles user authentication and management
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """User account model"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    audio_files = db.relationship('Audio', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    usage_stats = db.relationship('UsageStats', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    playback_history = db.relationship('PlaybackHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        }

    @staticmethod
    def create_user(username, password, email=None):
        """Create a new user"""
        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")

        if email and User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")

        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def authenticate(username, password):
        """Authenticate user"""
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            user.update_last_login()
            return user

        return None
