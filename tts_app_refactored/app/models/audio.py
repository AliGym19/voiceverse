"""
Audio Model - Handles audio file management
"""

from datetime import datetime
from app.extensions import db


class Audio(db.Model):
    """Audio file model"""

    __tablename__ = 'audio_files'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # File Information
    filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes

    # Metadata
    group_name = db.Column(db.String(100), default='Uncategorized', index=True)
    voice = db.Column(db.String(50), nullable=False)
    speed = db.Column(db.Float, default=1.0)

    # Content Statistics
    character_count = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Float, nullable=False)  # in USD

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Audio {self.display_name}>'

    def to_dict(self):
        """Convert audio to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'display_name': self.display_name,
            'group': self.group_name,
            'voice': self.voice,
            'speed': self.speed,
            'characters': self.character_count,
            'cost': self.cost,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def soft_delete(self):
        """Soft delete the audio file"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        db.session.commit()

    def restore(self):
        """Restore soft-deleted audio file"""
        self.is_deleted = False
        self.deleted_at = None
        db.session.commit()

    @staticmethod
    def get_user_audio(user_id, include_deleted=False):
        """Get all audio files for a user"""
        query = Audio.query.filter_by(user_id=user_id)

        if not include_deleted:
            query = query.filter_by(is_deleted=False)

        return query.order_by(Audio.created_at.desc()).all()

    @staticmethod
    def get_by_group(user_id, group_name):
        """Get audio files by group"""
        return Audio.query.filter_by(
            user_id=user_id,
            group_name=group_name,
            is_deleted=False
        ).order_by(Audio.created_at.desc()).all()

    @staticmethod
    def get_groups(user_id):
        """Get all groups for a user with counts"""
        from sqlalchemy import func

        groups = db.session.query(
            Audio.group_name,
            func.count(Audio.id).label('count')
        ).filter_by(
            user_id=user_id,
            is_deleted=False
        ).group_by(Audio.group_name).all()

        return {group: count for group, count in groups}

    @staticmethod
    def search(user_id, query):
        """Search audio files"""
        search_term = f'%{query}%'
        return Audio.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).filter(
            db.or_(
                Audio.display_name.like(search_term),
                Audio.group_name.like(search_term)
            )
        ).order_by(Audio.created_at.desc()).all()
