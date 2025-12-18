"""Helper utilities - Cost calculations, formatting, OpenAI client management"""

import os
from openai import OpenAI
from datetime import datetime

# Global OpenAI client (singleton pattern)
_openai_client = None
_agent_system = None

def get_openai_client():
    """
    Get or create OpenAI client singleton.

    Returns:
        OpenAI: OpenAI client instance
    """
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

def get_agent_system():
    """
    Get or create AI agent system singleton.

    Returns:
        TTSAgentSystem: AI agent system instance
    """
    global _agent_system
    if _agent_system is None:
        from tts_agents import create_agent_system
        _agent_system = create_agent_system()
    return _agent_system

def calculate_cost(characters, model='tts-1'):
    """
    Calculate the cost of TTS generation based on character count.

    Pricing (as of 2024):
    - TTS-1: $0.015 per 1,000 characters
    - TTS-1-HD: $0.030 per 1,000 characters

    Args:
        characters: Number of characters
        model: TTS model ('tts-1' or 'tts-1-hd')

    Returns:
        float: Cost in USD
    """
    rate_per_1k = 0.015 if model == 'tts-1' else 0.030
    return (characters / 1000) * rate_per_1k

def estimate_audio_duration(characters, words_per_minute=150):
    """
    Estimate audio duration based on character/word count.

    Args:
        characters: Number of characters
        words_per_minute: Average speaking rate (default: 150 WPM)

    Returns:
        float: Estimated duration in minutes
    """
    # Rough estimate: 5 characters per word
    estimated_words = characters / 5
    return estimated_words / words_per_minute

def format_timestamp(timestamp=None):
    """
    Format a timestamp for display.

    Args:
        timestamp: datetime object or None for current time

    Returns:
        str: Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def format_file_size(size_bytes):
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Formatted file size (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def truncate_text(text, max_length=100, suffix='...'):
    """
    Truncate text to a maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncated (default: '...')

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_voice_description(voice):
    """
    Get human-readable description of a voice.

    Args:
        voice: Voice name

    Returns:
        str: Voice description
    """
    descriptions = {
        'alloy': 'Neutral, versatile - Good for tutorials and documentation',
        'echo': 'Male, clear - Professional technical content',
        'fable': 'British male - Storytelling and audiobooks',
        'onyx': 'Deep male - Authority, news, formal content',
        'nova': 'Female, warm - Friendly content and guides',
        'shimmer': 'Soft female - Meditation and calm narration'
    }
    return descriptions.get(voice, 'Unknown voice')

def parse_bool_env(env_var, default=False):
    """
    Parse a boolean environment variable.

    Args:
        env_var: Environment variable name
        default: Default value if not set

    Returns:
        bool: Parsed boolean value
    """
    value = os.getenv(env_var, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def chunk_text(text, max_chars=4000):
    """
    Simple text chunking at paragraph/sentence boundaries.

    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk

    Returns:
        list: List of text chunks
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + '\n\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + '\n\n'

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
