"""Routes package - Modular blueprint organization"""

from .auth import auth_bp, init_auth
from .audio import audio_bp, init_audio
from .ai_agents import ai_agents_bp, init_ai_agents
from .file_parsing import file_parsing_bp
from .analytics import analytics_bp, init_analytics
from .health import health_bp, init_health

__all__ = [
    'auth_bp',
    'audio_bp',
    'ai_agents_bp',
    'file_parsing_bp',
    'analytics_bp',
    'health_bp',
    'init_auth',
    'init_audio',
    'init_ai_agents',
    'init_analytics',
    'init_health'
]
