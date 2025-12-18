"""
Test Database Models
"""

import pytest
from datetime import datetime
from app.models import User, Audio, UsageStats, PlaybackHistory
from app.extensions import db


class TestUserModel:
    """Test User model"""

    def test_create_user(self, _db):
        """Test user creation"""
        user = User.create_user('testuser', 'password123', 'test@example.com')

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.check_password('password123')

    def test_duplicate_username(self, _db, user):
        """Test duplicate username prevention"""
        with pytest.raises(ValueError, match="Username already exists"):
            User.create_user('testuser', 'password123')

    def test_password_hashing(self, _db):
        """Test password is hashed"""
        user = User.create_user('testuser', 'password123')

        assert user.password_hash != 'password123'
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')

    def test_short_password(self, _db):
        """Test short password rejection"""
        user = User(username='testuser')

        with pytest.raises(ValueError, match="at least 6 characters"):
            user.set_password('12345')

    def test_authenticate_success(self, _db, user):
        """Test successful authentication"""
        authenticated_user = User.authenticate('testuser', 'testpass123')

        assert authenticated_user is not None
        assert authenticated_user.id == user.id

    def test_authenticate_failure(self, _db, user):
        """Test failed authentication"""
        result = User.authenticate('testuser', 'wrongpassword')
        assert result is None

        result = User.authenticate('nonexistent', 'password')
        assert result is None

    def test_user_to_dict(self, _db, user):
        """Test user serialization"""
        user_dict = user.to_dict()

        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert 'password_hash' not in user_dict


class TestAudioModel:
    """Test Audio model"""

    def test_create_audio(self, _db, user):
        """Test audio creation"""
        audio = Audio(
            user_id=user.id,
            filename='test.mp3',
            display_name='Test Audio',
            file_path='/path/to/test.mp3',
            voice='nova',
            character_count=100,
            cost=0.0015
        )
        _db.session.add(audio)
        _db.session.commit()

        assert audio.id is not None
        assert audio.user_id == user.id
        assert audio.group_name == 'Uncategorized'

    def test_soft_delete(self, _db, sample_audio):
        """Test soft delete functionality"""
        assert not sample_audio.is_deleted

        sample_audio.soft_delete()

        assert sample_audio.is_deleted
        assert sample_audio.deleted_at is not None

    def test_restore(self, _db, sample_audio):
        """Test restore soft-deleted audio"""
        sample_audio.soft_delete()
        sample_audio.restore()

        assert not sample_audio.is_deleted
        assert sample_audio.deleted_at is None

    def test_get_user_audio(self, _db, user, sample_audio):
        """Test getting user's audio files"""
        # Create another audio
        audio2 = Audio(
            user_id=user.id,
            filename='test2.mp3',
            display_name='Test Audio 2',
            file_path='/path/to/test2.mp3',
            voice='fable',
            character_count=200,
            cost=0.003
        )
        _db.session.add(audio2)
        _db.session.commit()

        audios = Audio.get_user_audio(user.id)

        assert len(audios) == 2

    def test_get_user_audio_excludes_deleted(self, _db, user, sample_audio):
        """Test deleted audio exclusion"""
        sample_audio.soft_delete()

        audios = Audio.get_user_audio(user.id)

        assert len(audios) == 0

    def test_get_by_group(self, _db, user, sample_audio):
        """Test getting audio by group"""
        audios = Audio.get_by_group(user.id, 'Test Group')

        assert len(audios) == 1
        assert audios[0].id == sample_audio.id

    def test_get_groups(self, _db, user, sample_audio):
        """Test getting groups with counts"""
        # Create audio in different group
        audio2 = Audio(
            user_id=user.id,
            filename='test2.mp3',
            display_name='Test Audio 2',
            file_path='/path/to/test2.mp3',
            group_name='Another Group',
            voice='nova',
            character_count=100,
            cost=0.0015
        )
        _db.session.add(audio2)
        _db.session.commit()

        groups = Audio.get_groups(user.id)

        assert len(groups) == 2
        assert groups['Test Group'] == 1
        assert groups['Another Group'] == 1

    def test_search(self, _db, user, sample_audio):
        """Test audio search"""
        results = Audio.search(user.id, 'Test')

        assert len(results) == 1
        assert results[0].id == sample_audio.id

    def test_audio_to_dict(self, _db, sample_audio):
        """Test audio serialization"""
        audio_dict = sample_audio.to_dict()

        assert audio_dict['display_name'] == 'Test Audio'
        assert audio_dict['voice'] == 'nova'
        assert audio_dict['characters'] == 100


class TestUsageStatsModel:
    """Test UsageStats model"""

    def test_get_or_create(self, _db, user):
        """Test get or create usage stats"""
        stats = UsageStats.get_or_create(user.id)

        assert stats is not None
        assert stats.user_id == user.id
        assert stats.total_characters == 0
        assert stats.total_cost == 0.0

    def test_update_stats(self, _db, usage_stats):
        """Test updating statistics"""
        usage_stats.update_stats(characters=100, cost=0.0015)

        assert usage_stats.total_characters == 100
        assert usage_stats.total_cost == 0.0015
        assert usage_stats.files_generated == 1

    def test_monthly_data(self, _db, usage_stats):
        """Test monthly data tracking"""
        usage_stats.update_stats(characters=100, cost=0.0015)

        month_key = datetime.utcnow().strftime('%Y-%m')
        assert month_key in usage_stats.monthly_data
        assert usage_stats.monthly_data[month_key]['characters'] == 100

    def test_stats_to_dict(self, _db, usage_stats):
        """Test stats serialization"""
        usage_stats.update_stats(100, 0.0015)
        stats_dict = usage_stats.to_dict()

        assert stats_dict['total_characters'] == 100
        assert stats_dict['files_generated'] == 1
        assert 'monthly' in stats_dict


class TestPlaybackHistoryModel:
    """Test PlaybackHistory model"""

    def test_add_playback(self, _db, user, sample_audio):
        """Test adding playback record"""
        history = PlaybackHistory.add_playback(user.id, sample_audio.id)

        assert history.id is not None
        assert history.user_id == user.id
        assert history.audio_id == sample_audio.id

    def test_get_recent(self, _db, user, sample_audio):
        """Test getting recent playback history"""
        PlaybackHistory.add_playback(user.id, sample_audio.id)
        PlaybackHistory.add_playback(user.id, sample_audio.id)

        history = PlaybackHistory.get_recent(user.id, limit=10)

        assert len(history) == 2

    def test_clear_history(self, _db, user, sample_audio):
        """Test clearing playback history"""
        PlaybackHistory.add_playback(user.id, sample_audio.id)
        PlaybackHistory.clear_user_history(user.id)

        history = PlaybackHistory.get_recent(user.id)

        assert len(history) == 0

    def test_playback_to_dict(self, _db, user, sample_audio):
        """Test playback serialization"""
        history = PlaybackHistory.add_playback(user.id, sample_audio.id)
        history_dict = history.to_dict()

        assert history_dict['audio_id'] == sample_audio.id
        assert history_dict['audio_name'] == 'Test Audio'
        assert 'played_at' in history_dict
