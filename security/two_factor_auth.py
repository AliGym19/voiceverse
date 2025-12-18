#!/usr/bin/env python3
"""
Two-Factor Authentication (2FA) System using TOTP
Provides additional security layer for user accounts
"""

import pyotp
import qrcode
import io
import base64
from typing import Optional, Tuple


class TwoFactorAuth:
    """Manages 2FA/TOTP for users"""

    def __init__(self, issuer_name: str = "VoiceVerse"):
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """Generate a new TOTP secret for a user"""
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, username: str) -> str:
        """Generate TOTP URI for QR code"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=self.issuer_name
        )

    def generate_qr_code(self, secret: str, username: str) -> str:
        """Generate QR code as base64 image"""
        uri = self.get_totp_uri(secret, username)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    def verify_token(self, secret: str, token: str) -> bool:
        """Verify a TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def get_backup_codes(self, count: int = 10) -> list:
        """Generate backup codes for account recovery"""
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(count)]
