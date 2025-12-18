"""
Security Utilities
Input validation, sanitization, and security helpers
"""

import re
import bleach
from werkzeug.utils import secure_filename as werkzeug_secure_filename
from flask import current_app
import secrets


def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    # Remove path components
    filename = werkzeug_secure_filename(filename)

    # Additional sanitization
    filename = re.sub(r'[^\w\s\.-]', '', filename)
    filename = re.sub(r'\.+', '.', filename)  # Remove multiple dots
    filename = filename.strip()

    if not filename:
        return f"file_{secrets.token_hex(8)}"

    return filename


def sanitize_display_name(name, max_length=100):
    """Sanitize user input for display names"""
    if not name:
        return ""

    # Remove HTML tags and dangerous characters
    name = bleach.clean(name, tags=[], strip=True)

    # Limit length
    name = name[:max_length]

    # Remove control characters
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)

    return name.strip()


def sanitize_group_name(group_name, max_length=50):
    """Sanitize group names"""
    if not group_name:
        return "Uncategorized"

    group_name = sanitize_display_name(group_name, max_length)

    # Replace special characters with spaces
    group_name = re.sub(r'[^\w\s-]', ' ', group_name)

    # Normalize whitespace
    group_name = ' '.join(group_name.split())

    return group_name if group_name else "Uncategorized"


def validate_voice(voice):
    """Validate voice selection"""
    valid_voices = current_app.config.get('VALID_VOICES', {
        'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'
    })

    return voice if voice in valid_voices else current_app.config.get('DEFAULT_VOICE', 'nova')


def validate_speed(speed):
    """Validate speed parameter"""
    try:
        speed = float(speed)
        min_speed = current_app.config.get('MIN_SPEED', 0.25)
        max_speed = current_app.config.get('MAX_SPEED', 4.0)

        return max(min_speed, min(speed, max_speed))
    except (ValueError, TypeError):
        return 1.0


def validate_text_length(text, ui_limit=None, api_limit=None):
    """Validate and truncate text"""
    if not text:
        return "", False

    if ui_limit is None:
        ui_limit = current_app.config.get('UI_CHAR_LIMIT', 50000)

    if api_limit is None:
        api_limit = current_app.config.get('API_CHAR_LIMIT', 4096)

    # First check against UI limit
    if len(text) > ui_limit:
        return text[:ui_limit], True

    # Check against API limit for actual processing
    truncated = False
    if len(text) > api_limit:
        text = text[:api_limit]
        truncated = True

    return text, truncated


def validate_file_extension(filename, allowed_extensions=None):
    """Validate file extension"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'txt', 'docx', 'pdf'})

    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


def generate_secure_token(length=32):
    """Generate secure random token"""
    return secrets.token_urlsafe(length)


def is_safe_redirect(url):
    """Check if redirect URL is safe"""
    if not url:
        return False

    # Only allow relative URLs
    if url.startswith('/'):
        # Check for protocol-relative URLs
        if url.startswith('//'):
            return False
        return True

    return False


class CSRFProtection:
    """CSRF Protection helper"""

    @staticmethod
    def generate_token():
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_token(token, session_token):
        """Validate CSRF token"""
        if not token or not session_token:
            return False

        return secrets.compare_digest(token, session_token)


def rate_limit_key(user_id=None):
    """Generate rate limit key"""
    if user_id:
        return f"user_{user_id}"
    return "anonymous"


def validate_username(username):
    """Validate username format"""
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 80:
        return False, "Username must be less than 80 characters"

    # Alphanumeric and underscore only
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscore"

    return True, ""


def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"

    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    if len(password) > 255:
        return False, "Password is too long"

    # Optional: Check for password strength
    # has_upper = any(c.isupper() for c in password)
    # has_lower = any(c.islower() for c in password)
    # has_digit = any(c.isdigit() for c in password)
    #
    # if not (has_upper and has_lower and has_digit):
    #     return False, "Password must contain uppercase, lowercase, and digits"

    return True, ""


def sanitize_html(html_content):
    """Sanitize HTML content"""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
    allowed_attributes = {'a': ['href', 'title']}

    return bleach.clean(
        html_content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )


def check_file_size(file, max_size=None):
    """Check file size"""
    if max_size is None:
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)

    # Seek to end to get size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)  # Reset to beginning

    return size <= max_size, size
