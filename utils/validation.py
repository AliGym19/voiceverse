"""Validation utilities - Password validation, voice validation, input sanitization"""

import re
import html

def validate_password(password):
    """
    Security: Validate password strength.

    Requirements:
    - At least 12 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character

    Args:
        password: Password string to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If valid, error_message will be empty string
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    return True, ""

def validate_voice(voice):
    """
    Validate that the voice is one of the allowed OpenAI TTS voices.

    Allowed voices:
    - alloy: Neutral, versatile
    - echo: Male, clear
    - fable: British male
    - onyx: Deep male
    - nova: Female, warm
    - shimmer: Soft female

    Args:
        voice: Voice name string

    Returns:
        bool: True if valid voice, False otherwise
    """
    allowed_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    return voice in allowed_voices

def sanitize_display_name(name):
    """
    Remove .mp3 extension and replace underscores with spaces for display.

    Args:
        name: Filename string

    Returns:
        Sanitized display name
    """
    return name.replace('.mp3', '').replace('_', ' ')

def sanitize_html(text):
    """
    Escape HTML characters to prevent XSS attacks.

    Args:
        text: Text that may contain HTML

    Returns:
        HTML-escaped text safe for display
    """
    return html.escape(text)

def validate_text_length(text, min_length=1, max_length=100000):
    """
    Validate text length is within acceptable bounds.

    Args:
        text: Text to validate
        min_length: Minimum allowed length (default: 1)
        max_length: Maximum allowed length (default: 100000)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not text or len(text) < min_length:
        return False, f"Text must be at least {min_length} character(s)"
    if len(text) > max_length:
        return False, f"Text must not exceed {max_length} characters"
    return True, ""

def validate_speed(speed):
    """
    Validate TTS speed is within OpenAI's acceptable range.

    Args:
        speed: Speed multiplier (float)

    Returns:
        Tuple of (is_valid: bool, error_message: str, normalized_speed: float)
    """
    try:
        speed_float = float(speed)
        if speed_float < 0.25:
            return False, "Speed must be at least 0.25x", 0.25
        if speed_float > 4.0:
            return False, "Speed must not exceed 4.0x", 4.0
        return True, "", speed_float
    except (ValueError, TypeError):
        return False, "Invalid speed value", 1.0
