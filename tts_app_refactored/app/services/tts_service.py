"""
Text-to-Speech Service
Handles OpenAI TTS API interactions
"""

import os
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from flask import current_app
from app.utils.security import validate_voice, validate_speed, validate_text_length
from app.utils.logger import log_error


class TTSService:
    """Text-to-Speech service for OpenAI API"""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize OpenAI client"""
        api_key = current_app.config.get('OPENAI_API_KEY')

        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            current_app.logger.error("OpenAI API key not configured")
            raise ValueError("OpenAI API key not configured")

        self.client = OpenAI(api_key=api_key)

    def generate_speech(self, text, voice='nova', speed=1.0, filename=None):
        """
        Generate speech from text

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            filename: Optional filename for saving

        Returns:
            dict: Result containing file_path, character_count, cost, etc.
        """
        try:
            # Validate inputs
            voice = validate_voice(voice)
            speed = validate_speed(speed)
            text, truncated = validate_text_length(text)

            if not text:
                raise ValueError("Text cannot be empty")

            # Calculate cost (OpenAI pricing: $15 per 1M characters)
            character_count = len(text)
            cost = (character_count / 1_000_000) * 15.0

            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"audio_{timestamp}.mp3"

            # Ensure filename ends with .mp3
            if not filename.endswith('.mp3'):
                filename += '.mp3'

            # Full file path
            audio_folder = Path(current_app.config['AUDIO_FOLDER'])
            audio_folder.mkdir(parents=True, exist_ok=True)
            file_path = audio_folder / filename

            # Call OpenAI TTS API
            current_app.logger.info(
                f"Generating TTS: {character_count} chars, voice={voice}, speed={speed}"
            )

            response = self.client.audio.speech.create(
                model=current_app.config.get('OPENAI_TTS_MODEL', 'tts-1'),
                voice=voice,
                input=text,
                speed=speed
            )

            # Save to file
            response.stream_to_file(str(file_path))

            current_app.logger.info(f"TTS generated successfully: {filename}")

            return {
                'success': True,
                'filename': filename,
                'file_path': str(file_path),
                'character_count': character_count,
                'cost': cost,
                'voice': voice,
                'speed': speed,
                'truncated': truncated
            }

        except Exception as e:
            current_app.logger.error(f"TTS generation failed: {str(e)}", exc_info=True)
            log_error(current_app, e)

            return {
                'success': False,
                'error': str(e)
            }

    def validate_audio_file(self, file_path):
        """Validate that audio file exists and is accessible"""
        path = Path(file_path)
        return path.exists() and path.is_file() and path.stat().st_size > 0

    def delete_audio_file(self, filename):
        """Delete audio file from filesystem"""
        try:
            file_path = Path(current_app.config['AUDIO_FOLDER']) / filename

            if file_path.exists():
                file_path.unlink()
                current_app.logger.info(f"Deleted audio file: {filename}")
                return True

            return False

        except Exception as e:
            current_app.logger.error(f"Failed to delete audio file {filename}: {str(e)}")
            return False

    def get_file_size(self, filename):
        """Get audio file size in bytes"""
        try:
            file_path = Path(current_app.config['AUDIO_FOLDER']) / filename
            return file_path.stat().st_size if file_path.exists() else 0
        except Exception:
            return 0

    def get_available_voices(self):
        """Get list of available voices"""
        return list(current_app.config.get('VALID_VOICES', {
            'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'
        }))

    def get_voice_info(self):
        """Get detailed voice information"""
        return {
            'alloy': {
                'name': 'Alloy',
                'description': 'Neutral, balanced',
                'best_for': 'General content, tutorials, documentation'
            },
            'echo': {
                'name': 'Echo',
                'description': 'Male, clear',
                'best_for': 'Technical content, professional narration'
            },
            'fable': {
                'name': 'Fable',
                'description': 'British, expressive',
                'best_for': 'Storytelling, audiobooks, dramatic content'
            },
            'onyx': {
                'name': 'Onyx',
                'description': 'Deep, authoritative',
                'best_for': 'Authority, news, formal presentations'
            },
            'nova': {
                'name': 'Nova',
                'description': 'Female, friendly',
                'best_for': 'Friendly content, guides, casual narration'
            },
            'shimmer': {
                'name': 'Shimmer',
                'description': 'Soft, warm',
                'best_for': 'Soothing content, meditations, calm narration'
            }
        }


# Global service instance
_tts_service = None


def get_tts_service():
    """Get or create TTS service instance"""
    global _tts_service

    if _tts_service is None:
        _tts_service = TTSService()

    return _tts_service
