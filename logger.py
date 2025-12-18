#!/usr/bin/env python3
"""
Security Logger Module for VoiceVerse TTS Application
Provides comprehensive security event logging with PII sanitization
"""

import logging
import logging.config
import json
import hashlib
import os
from datetime import datetime
from typing import Optional


class SecurityLogger:
    """
    Security logger that logs events to both files and database

    Features:
    - JSON-formatted security audit logs
    - PII sanitization (email masking, IP hashing)
    - Database persistence for security events
    - Multiple log levels (INFO, WARNING, ERROR)
    """

    def __init__(self, db):
        """
        Initialize security logger

        Args:
            db: Database instance for logging security events
        """
        self.db = db

        # Load logging configuration if available
        config_path = os.path.join(os.path.dirname(__file__), 'logging_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    logging.config.dictConfig(config)
            except Exception as e:
                print(f"Warning: Could not load logging config: {e}")
                # Fallback to basic config
                logging.basicConfig(level=logging.INFO)
        else:
            # Fallback to basic config if file doesn't exist
            logging.basicConfig(level=logging.INFO)

        self.logger = logging.getLogger('security')

    def _sanitize_pii(self, data: Optional[str]) -> str:
        """
        Mask PII in log data

        Args:
            data: String that may contain PII

        Returns:
            Sanitized string with PII masked

        Examples:
            user@domain.com → u***@domain.com
            192.168.1.1 → 192.168.xxx.xxx (optional, based on policy)
        """
        if not data:
            return 'N/A'

        # Mask email addresses
        if isinstance(data, str) and '@' in data:
            parts = data.split('@')
            if len(parts) == 2:
                # Mask username part: keep first char, mask rest
                username = parts[0]
                if len(username) > 0:
                    return username[0] + '***@' + parts[1]

        return str(data)

    def _hash_ip(self, ip_address: Optional[str]) -> str:
        """
        Create a non-reversible hash of IP address for privacy

        Args:
            ip_address: IP address to hash

        Returns:
            SHA256 hash of IP (first 16 characters)
        """
        if not ip_address:
            return 'unknown'

        # Create hash with salt (use environment variable in production)
        salt = os.getenv('IP_HASH_SALT', 'voiceverse-security-salt')
        combined = f"{ip_address}{salt}"
        hash_obj = hashlib.sha256(combined.encode())
        return hash_obj.hexdigest()[:16]

    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[str] = None,
        success: bool = True,
        level: str = 'INFO'
    ):
        """
        Log security event to both file and database

        Event types:
        - AUTH_LOGIN: Successful login attempt
        - AUTH_LOGOUT: User logout
        - AUTH_REGISTER: New user registration
        - AUTH_FAILURE: Failed login attempt
        - FILE_ACCESS: File accessed successfully
        - FILE_UPLOAD: File uploaded
        - FILE_DOWNLOAD: File downloaded
        - FILE_DELETE: File deleted
        - FILE_ACCESS_DENIED: Unauthorized file access attempt
        - RATE_LIMIT_HIT: Rate limit warning threshold reached
        - RATE_LIMIT_EXCEEDED: Rate limit exceeded
        - CSRF_FAILURE: CSRF validation failed
        - CSRF_SUCCESS: CSRF validation passed
        - OWNERSHIP_VIOLATION: Attempt to access file owned by another user
        - SUSPICIOUS_ACTIVITY: Detected suspicious behavior

        Args:
            event_type: Type of security event
            user_id: Database ID of user (optional)
            username: Username (will be sanitized)
            ip_address: IP address of request
            details: Additional event details
            success: Whether the event succeeded
            level: Log level (INFO, WARNING, ERROR)
        """

        # Create structured log data
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'user_id': user_id if user_id else None,
            'username': self._sanitize_pii(username) if username else 'anonymous',
            'ip_hash': self._hash_ip(ip_address),
            'details': details if details else '',
            'success': success
        }

        # Log to file (JSON format)
        log_message = json.dumps(log_data)

        if success:
            if level == 'WARNING':
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
        else:
            if level == 'ERROR':
                self.logger.error(log_message)
            else:
                self.logger.warning(log_message)

        # Log to database
        try:
            if hasattr(self.db, 'log_security_event'):
                self.db.log_security_event(
                    event_type=event_type,
                    user_id=user_id,
                    ip_address=ip_address if ip_address else 'unknown',
                    details=details,
                    success=success
                )
        except Exception as e:
            # If database logging fails, log the error but don't crash
            self.logger.error(f"Failed to log to database: {e}")

    def log_authentication(
        self,
        username: str,
        ip_address: str,
        success: bool,
        details: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """
        Convenience method for authentication events

        Args:
            username: Username attempting authentication
            ip_address: IP address of request
            success: Whether authentication succeeded
            details: Optional additional details
            user_id: User ID if authentication succeeded
        """
        event_type = 'AUTH_LOGIN' if success else 'AUTH_FAILURE'
        level = 'INFO' if success else 'WARNING'

        self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=success,
            level=level
        )

    def log_registration(
        self,
        username: str,
        ip_address: str,
        success: bool,
        details: Optional[str] = None,
        user_id: Optional[int] = None
    ):
        """
        Convenience method for registration events

        Args:
            username: Username being registered
            ip_address: IP address of request
            success: Whether registration succeeded
            details: Optional additional details
            user_id: User ID if registration succeeded
        """
        self.log_event(
            event_type='AUTH_REGISTER',
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=success,
            level='INFO' if success else 'WARNING'
        )

    def log_logout(
        self,
        username: str,
        ip_address: str,
        user_id: Optional[int] = None
    ):
        """
        Convenience method for logout events

        Args:
            username: Username logging out
            ip_address: IP address of request
            user_id: User ID
        """
        self.log_event(
            event_type='AUTH_LOGOUT',
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details='User logged out',
            success=True,
            level='INFO'
        )

    def log_file_access(
        self,
        filename: str,
        username: str,
        ip_address: str,
        success: bool,
        action: str = 'ACCESS',
        user_id: Optional[int] = None
    ):
        """
        Convenience method for file access events

        Args:
            filename: Name of file being accessed
            username: Username accessing file
            ip_address: IP address of request
            success: Whether access was granted
            action: Type of access (ACCESS, DOWNLOAD, DELETE, UPLOAD)
            user_id: User ID
        """
        if success:
            event_type = f'FILE_{action}'
        else:
            event_type = 'FILE_ACCESS_DENIED'

        details = f"File: {filename}, Action: {action}"

        self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=success,
            level='INFO' if success else 'WARNING'
        )

    def log_rate_limit(
        self,
        username: str,
        ip_address: str,
        endpoint: str,
        exceeded: bool = True,
        user_id: Optional[int] = None
    ):
        """
        Convenience method for rate limit events

        Args:
            username: Username hitting rate limit
            ip_address: IP address of request
            endpoint: Endpoint that was rate limited
            exceeded: Whether limit was exceeded (True) or just approaching (False)
            user_id: User ID
        """
        event_type = 'RATE_LIMIT_EXCEEDED' if exceeded else 'RATE_LIMIT_HIT'
        details = f"Endpoint: {endpoint}"

        self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=not exceeded,
            level='WARNING' if exceeded else 'INFO'
        )

    def log_ownership_violation(
        self,
        filename: str,
        username: str,
        ip_address: str,
        owner_username: str,
        user_id: Optional[int] = None
    ):
        """
        Log attempt to access file owned by another user

        Args:
            filename: Name of file
            username: Username attempting access
            ip_address: IP address of request
            owner_username: Actual owner of the file
            user_id: User ID of violator
        """
        details = f"File: {filename}, Owner: {owner_username}"

        self.log_event(
            event_type='OWNERSHIP_VIOLATION',
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=False,
            level='WARNING'
        )

    def log_error(
        self,
        error_type: str,
        username: Optional[str],
        ip_address: str,
        details: str,
        user_id: Optional[int] = None
    ):
        """
        Log application errors

        Args:
            error_type: Type of error (e.g., 'DATABASE_ERROR', 'VALIDATION_ERROR')
            username: Username if applicable
            ip_address: IP address of request
            details: Error details
            user_id: User ID if applicable
        """
        self.log_event(
            event_type=error_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            success=False,
            level='ERROR'
        )


# Convenience function to create logger instance
def create_security_logger(db):
    """
    Factory function to create SecurityLogger instance

    Args:
        db: Database instance

    Returns:
        SecurityLogger instance
    """
    return SecurityLogger(db)
