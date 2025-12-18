#!/usr/bin/env python3
"""
Core Tests for VoiceVerse
Tests critical functionality
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_imports():
    """Test that all modules can be imported"""
    from database import Database
    from logger import SecurityLogger
    from monitoring.metrics_collector import get_metrics_collector
    from monitoring.log_analyzer import LogAnalyzer
    from monitoring.alerting_system import AlertingSystem
    from security.two_factor_auth import TwoFactorAuth
    from security.api_key_manager import APIKeyManager
    assert True


def test_metrics_collector():
    """Test metrics collector initialization"""
    from monitoring.metrics_collector import get_metrics_collector

    metrics = get_metrics_collector()
    assert metrics is not None
    assert metrics.get_uptime() >= 0


def test_2fa_generation():
    """Test 2FA secret and token generation"""
    from security.two_factor_auth import TwoFactorAuth

    tfa = TwoFactorAuth()
    secret = tfa.generate_secret()

    assert secret is not None
    assert len(secret) == 32

    # Test QR code generation
    qr_code = tfa.generate_qr_code(secret, "testuser")
    assert qr_code is not None
    assert len(qr_code) > 0


def test_api_key_generation():
    """Test API key generation"""
    from security.api_key_manager import APIKeyManager

    manager = APIKeyManager(':memory:')
    key = manager.generate_key()

    assert key.startswith('vv_')
    assert len(key) > 30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
