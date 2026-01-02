"""
Production configuration for VoiceVerse TTS
Handles environment-specific paths for Render deployment
"""

import os

# Detect if running on Render
IS_RENDER = os.getenv('RENDER') is not None

if IS_RENDER:
    # Production - use Render's persistent disk
    BASE_DATA_PATH = '/opt/render/project/src/data'
    DATABASE_PATH = os.path.join(BASE_DATA_PATH, 'voiceverse.db')
    SAVED_AUDIO_PATH = os.path.join(BASE_DATA_PATH, 'saved_audio')
    VOICE_SAMPLES_PATH = os.path.join(BASE_DATA_PATH, 'voice_samples')
    LOGS_PATH = os.path.join(BASE_DATA_PATH, 'logs')
else:
    # Development - use local directories
    BASE_DATA_PATH = '.'
    DATABASE_PATH = 'voiceverse.db'
    SAVED_AUDIO_PATH = 'saved_audio'
    VOICE_SAMPLES_PATH = 'voice_samples'
    LOGS_PATH = 'logs'

# Export configuration
__all__ = [
    'IS_RENDER',
    'DATABASE_PATH',
    'SAVED_AUDIO_PATH',
    'VOICE_SAMPLES_PATH',
    'LOGS_PATH',
]
