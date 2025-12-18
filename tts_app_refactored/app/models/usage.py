"""
Usage Tracking Models - Statistics and History
"""

from datetime import datetime
from app.extensions import db


class UsageStats(db.Model):
    """Usage statistics model"""

    __tablename__ = 'usage_stats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Statistics
    total_characters = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    files_generated = db.Column(db.Integer, default=0)

    # Monthly breakdown (JSON field)
    monthly_data = db.Column(db.JSON, default=dict)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UsageStats user_id={self.user_id}>'

    def update_stats(self, characters, cost):
        """Update usage statistics"""
        self.total_characters += characters
        self.total_cost += cost
        self.files_generated += 1

        # Update monthly data
        month_key = datetime.utcnow().strftime('%Y-%m')
        if not self.monthly_data:
            self.monthly_data = {}

        if month_key not in self.monthly_data:
            self.monthly_data[month_key] = {
                'characters': 0,
                'cost': 0.0,
                'files': 0
            }

        self.monthly_data[month_key]['characters'] += characters
        self.monthly_data[month_key]['cost'] += cost
        self.monthly_data[month_key]['files'] += 1

        db.session.commit()

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'total_characters': self.total_characters,
            'total_cost': self.total_cost,
            'files_generated': self.files_generated,
            'monthly': self.monthly_data or {}
        }

    @staticmethod
    def get_or_create(user_id):
        """Get or create usage stats for user"""
        stats = UsageStats.query.filter_by(user_id=user_id).first()

        if not stats:
            stats = UsageStats(user_id=user_id)
            db.session.add(stats)
            db.session.commit()

        return stats


class PlaybackHistory(db.Model):
    """Playback history model"""

    __tablename__ = 'playback_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    audio_id = db.Column(db.Integer, db.ForeignKey('audio_files.id'), nullable=False)

    # Playback information
    played_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    audio = db.relationship('Audio', backref='playback_records')

    def __repr__(self):
        return f'<PlaybackHistory audio_id={self.audio_id}>'

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'audio_id': self.audio_id,
            'audio_name': self.audio.display_name if self.audio else None,
            'group': self.audio.group_name if self.audio else None,
            'played_at': self.played_at.isoformat() if self.played_at else None
        }

    @staticmethod
    def add_playback(user_id, audio_id):
        """Add playback record"""
        history = PlaybackHistory(user_id=user_id, audio_id=audio_id)
        db.session.add(history)
        db.session.commit()
        return history

    @staticmethod
    def get_recent(user_id, limit=50):
        """Get recent playback history"""
        return PlaybackHistory.query.filter_by(
            user_id=user_id
        ).order_by(
            PlaybackHistory.played_at.desc()
        ).limit(limit).all()

    @staticmethod
    def clear_user_history(user_id):
        """Clear user's playback history"""
        PlaybackHistory.query.filter_by(user_id=user_id).delete()
        db.session.commit()
