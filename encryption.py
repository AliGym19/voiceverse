# -*- coding: utf-8 -*-
"""
API Key Encryption Utilities

Provides secure encryption/decryption for user API keys using Fernet symmetric encryption.
The encryption key is derived from the application's SECRET_KEY environment variable.
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional


def _get_encryption_key() -> bytes:
    """
    Derive a Fernet-compatible encryption key from SECRET_KEY.

    Fernet requires a 32-byte base64-encoded key. We derive this from
    the application's SECRET_KEY using SHA-256 hashing.
    """
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        raise ValueError("SECRET_KEY environment variable is required for encryption")

    # Hash the secret key to get exactly 32 bytes, then base64 encode
    key_hash = hashlib.sha256(secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for secure storage.

    Args:
        api_key: The plaintext OpenAI API key

    Returns:
        Base64-encoded encrypted string safe for database storage

    Raises:
        ValueError: If SECRET_KEY is not set
    """
    if not api_key:
        raise ValueError("API key cannot be empty")

    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(api_key.encode())
    return encrypted.decode('utf-8')


def decrypt_api_key(encrypted_key: str) -> Optional[str]:
    """
    Decrypt an encrypted API key.

    Args:
        encrypted_key: The encrypted API key from database

    Returns:
        Decrypted plaintext API key, or None if decryption fails

    Note:
        Returns None instead of raising exceptions to handle
        cases where keys were encrypted with a different SECRET_KEY
    """
    if not encrypted_key:
        return None

    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode('utf-8')
    except (InvalidToken, ValueError, Exception):
        # Key may have been encrypted with different SECRET_KEY
        # or data is corrupted
        return None


def validate_openai_api_key(api_key: str) -> bool:
    """
    Basic validation of OpenAI API key format.

    Args:
        api_key: The API key to validate

    Returns:
        True if the key matches expected format patterns
    """
    if not api_key:
        return False

    # OpenAI API keys typically start with 'sk-' and have specific patterns
    # Old format: sk-... (51 chars total)
    # New format: sk-proj-... (longer, project-specific)
    api_key = api_key.strip()

    if not api_key.startswith('sk-'):
        return False

    # Minimum length check (old format is ~51 chars, new can be longer)
    if len(api_key) < 40:
        return False

    # Check for valid characters (alphanumeric, dash, underscore)
    valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in valid_chars for c in api_key):
        return False

    return True


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key for display purposes.

    Args:
        api_key: The plaintext API key

    Returns:
        Masked version showing only first 7 and last 4 characters
        Example: sk-proj...abc1
    """
    if not api_key or len(api_key) < 12:
        return "***"

    return f"{api_key[:7]}...{api_key[-4:]}"
