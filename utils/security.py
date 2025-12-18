"""Security utilities - IP hashing, security headers, logging"""

import hashlib
import os
from flask import request

def hash_ip(ip_address: str) -> str:
    """
    Hash IP address with salt for privacy-preserving logging.

    Args:
        ip_address: The IP address to hash

    Returns:
        Hashed IP address (first 16 chars of SHA256 hash)
    """
    salt = os.getenv('IP_HASH_SALT', 'default-salt-change-this')
    return hashlib.sha256(f"{ip_address}{salt}".encode()).hexdigest()[:16]

def set_security_headers(response):
    """
    Add security headers to protect against common web vulnerabilities.

    Headers added:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Force HTTPS (if enabled)
    - Content-Security-Policy: Restrict resource loading

    Args:
        response: Flask response object

    Returns:
        Modified response object with security headers
    """
    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Enable XSS filter
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Force HTTPS (if USE_HTTPS is enabled)
    use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
    if use_https:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:;"
    )

    return response

def log_security_event(security_logger, event_type, details, username=None, ip_address=None, success=True):
    """
    Log a security event using the security logger.

    Args:
        security_logger: SecurityLogger instance
        event_type: Type of security event (e.g., 'LOGIN_SUCCESS', 'LOGIN_FAILED')
        details: Details about the event
        username: Username associated with the event (optional)
        ip_address: IP address (optional, will use request.remote_addr if not provided)
        success: Whether the event was successful (default: True)
    """
    if security_logger:
        if ip_address is None and request:
            ip_address = request.remote_addr
        # Call log_event with proper keyword arguments to avoid parameter mismatch
        security_logger.log_event(
            event_type=event_type,
            username=username or 'anonymous',
            ip_address=ip_address,
            details=details,
            success=success
        )
