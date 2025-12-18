#!/usr/bin/env python3
"""
VoiceVerse Configuration Manager
Validates and generates configuration for production deployment

Usage:
    python3 scripts/config_manager.py generate    # Generate new secrets
    python3 scripts/config_manager.py validate    # Validate current configuration
    python3 scripts/config_manager.py create-env  # Create .env from template
    python3 scripts/config_manager.py check-all   # Run all checks
"""

import os
import sys
import secrets
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional, Dict, List

# Color codes for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


class ConfigManager:
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the configuration manager"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.env_file = self.project_root / '.env'
        self.env_example = self.project_root / '.env.example'
        self.env_production = self.project_root / '.env.production'

    def print_success(self, message: str):
        """Print success message in green"""
        print(f"{GREEN}✓ {message}{NC}")

    def print_warning(self, message: str):
        """Print warning message in yellow"""
        print(f"{YELLOW}⚠ {message}{NC}")

    def print_error(self, message: str):
        """Print error message in red"""
        print(f"{RED}✗ {message}{NC}")

    def print_info(self, message: str):
        """Print info message in blue"""
        print(f"{BLUE}ℹ {message}{NC}")

    def generate_secret_key(self, length: int = 32) -> str:
        """Generate a secure random secret key"""
        return secrets.token_hex(length)

    def generate_ip_salt(self) -> str:
        """Generate a URL-safe random salt for IP hashing"""
        return secrets.token_urlsafe(32)

    def validate_env_file(self) -> Tuple[bool, List[str]]:
        """
        Validate that all required environment variables are set
        Returns: (success, missing_vars)
        """
        required_vars = [
            'SECRET_KEY',
            'OPENAI_API_KEY',
            'IP_HASH_SALT',
        ]

        # Load .env file
        if not self.env_file.exists():
            return False, ['File not found: .env']

        env_vars = {}
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        missing = []
        for var in required_vars:
            if var not in env_vars or not env_vars[var] or env_vars[var].startswith('your-'):
                missing.append(var)

        return len(missing) == 0, missing

    def test_database_connection(self, db_path: str = 'voiceverse.db') -> Tuple[bool, str]:
        """
        Test database connectivity
        Returns: (success, message)
        """
        db_full_path = self.project_root / db_path

        if not db_full_path.exists():
            return False, f"Database file not found: {db_path}"

        try:
            conn = sqlite3.connect(str(db_full_path))
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = ['users', 'audio_files', 'security_events']

            missing_tables = [t for t in required_tables if t not in tables]

            conn.close()

            if missing_tables:
                return False, f"Missing tables: {', '.join(missing_tables)}"

            return True, "Database connection successful, all required tables present"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    def test_openai_api_key(self, api_key: Optional[str] = None) -> Tuple[bool, str]:
        """
        Test OpenAI API key validity
        Returns: (success, message)
        """
        if api_key is None:
            # Try to load from .env
            if not self.env_file.exists():
                return False, "No .env file found"

            with open(self.env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

        if not api_key:
            return False, "OPENAI_API_KEY not set"

        if api_key.startswith('your-') or api_key == 'sk-your-key-here':
            return False, "OPENAI_API_KEY is still set to placeholder value"

        if not api_key.startswith('sk-'):
            return False, "OPENAI_API_KEY appears to be invalid (should start with 'sk-')"

        # Basic format check
        if len(api_key) < 40:
            return False, "OPENAI_API_KEY appears to be too short"

        return True, "OPENAI_API_KEY format appears valid"

    def check_ssl_certificate(self, cert_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        Check SSL certificate validity
        Returns: (success, message)
        """
        if cert_path is None:
            # Try to load from .env
            if not self.env_file.exists():
                return False, "No .env file found"

            with open(self.env_file, 'r') as f:
                for line in f:
                    if line.startswith('SSL_CERT_PATH='):
                        cert_path = line.split('=', 1)[1].strip()
                        break

        if not cert_path:
            return True, "SSL not configured (optional for development)"

        cert_full_path = self.project_root / cert_path

        if not cert_full_path.exists():
            return False, f"SSL certificate not found: {cert_path}"

        try:
            import subprocess
            result = subprocess.run(
                ['openssl', 'x509', '-in', str(cert_full_path), '-noout', '-dates'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return True, "SSL certificate is valid"
            else:
                return False, f"SSL certificate validation failed: {result.stderr}"
        except FileNotFoundError:
            return True, "OpenSSL not installed (skipping cert validation)"
        except subprocess.TimeoutExpired:
            return False, "SSL certificate validation timed out"
        except Exception as e:
            return False, f"SSL certificate check failed: {str(e)}"

    def check_file_permissions(self) -> Tuple[bool, List[str]]:
        """
        Check file permissions for sensitive files
        Returns: (success, issues)
        """
        issues = []

        # Check .env file permissions
        if self.env_file.exists():
            stat_info = os.stat(self.env_file)
            mode = stat_info.st_mode & 0o777

            # Should be 600 or 640 (owner read/write only, or owner read/write + group read)
            if mode not in [0o600, 0o640]:
                issues.append(f".env has insecure permissions: {oct(mode)} (should be 0o600 or 0o640)")

        # Check database file
        db_path = self.project_root / 'voiceverse.db'
        if db_path.exists():
            stat_info = os.stat(db_path)
            mode = stat_info.st_mode & 0o777

            if mode not in [0o600, 0o640, 0o660]:
                issues.append(f"voiceverse.db has insecure permissions: {oct(mode)} (should be 0o600, 0o640, or 0o660)")

        return len(issues) == 0, issues

    def create_production_env(self, output_path: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Create production .env file from template
        Returns: (success, message)
        """
        if output_path is None:
            output_path = self.env_file

        if not self.env_example.exists():
            return False, ".env.example template not found"

        if output_path.exists():
            backup_path = output_path.parent / f"{output_path.name}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_path.rename(backup_path)
            self.print_warning(f"Existing .env backed up to {backup_path.name}")

        # Read template
        with open(self.env_example, 'r') as f:
            template = f.read()

        # Generate secrets
        secret_key = self.generate_secret_key()
        ip_salt = self.generate_ip_salt()

        # Replace placeholders
        config = template
        config = config.replace('your-secret-key-here-generate-a-random-64-character-hex-string', secret_key)
        config = config.replace('your-random-salt-here-change-in-production', ip_salt)

        # Write new .env
        with open(output_path, 'w') as f:
            f.write(config)

        # Set secure permissions
        os.chmod(output_path, 0o600)

        return True, f"Production .env created at {output_path}"

    def validate_production_readiness(self) -> Dict[str, Tuple[bool, str]]:
        """
        Run all validation checks for production readiness
        Returns: dict of check_name: (success, message)
        """
        checks = {}

        # Environment variables
        success, missing = self.validate_env_file()
        if success:
            checks['env_vars'] = (True, "All required environment variables are set")
        else:
            checks['env_vars'] = (False, f"Missing variables: {', '.join(missing)}")

        # Database
        checks['database'] = self.test_database_connection()

        # OpenAI API
        checks['openai_api'] = self.test_openai_api_key()

        # SSL Certificate
        checks['ssl_cert'] = self.check_ssl_certificate()

        # File Permissions
        success, issues = self.check_file_permissions()
        if success:
            checks['permissions'] = (True, "File permissions are secure")
        else:
            checks['permissions'] = (False, f"Permission issues: {'; '.join(issues)}")

        return checks

    def print_validation_report(self, checks: Dict[str, Tuple[bool, str]]):
        """Print a formatted validation report"""
        print("\n" + "=" * 60)
        print("VoiceVerse Configuration Validation Report")
        print("=" * 60 + "\n")

        all_passed = True
        for check_name, (success, message) in checks.items():
            label = check_name.replace('_', ' ').title()
            if success:
                self.print_success(f"{label}: {message}")
            else:
                self.print_error(f"{label}: {message}")
                all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            self.print_success("All checks passed! ✨")
            print("=" * 60 + "\n")
            return 0
        else:
            self.print_error("Some checks failed. Please fix the issues above.")
            print("=" * 60 + "\n")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description='VoiceVerse Configuration Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    Generate new secrets:
        python3 scripts/config_manager.py generate

    Validate current configuration:
        python3 scripts/config_manager.py validate

    Create .env from template:
        python3 scripts/config_manager.py create-env

    Run all checks:
        python3 scripts/config_manager.py check-all
        """
    )

    parser.add_argument(
        'command',
        choices=['generate', 'validate', 'create-env', 'check-all'],
        help='Command to execute'
    )

    parser.add_argument(
        '--project-root',
        type=str,
        default=None,
        help='Project root directory (default: parent of script directory)'
    )

    args = parser.parse_args()

    # Initialize manager
    manager = ConfigManager(args.project_root)

    if args.command == 'generate':
        print("\n" + "=" * 60)
        print("Generating New Secrets")
        print("=" * 60 + "\n")

        secret_key = manager.generate_secret_key()
        ip_salt = manager.generate_ip_salt()

        print(f"SECRET_KEY={secret_key}")
        print(f"IP_HASH_SALT={ip_salt}")

        print("\n" + YELLOW + "Add these to your .env file!" + NC + "\n")
        return 0

    elif args.command == 'validate':
        checks = manager.validate_production_readiness()
        return manager.print_validation_report(checks)

    elif args.command == 'create-env':
        success, message = manager.create_production_env()
        if success:
            manager.print_success(message)
            manager.print_warning("Don't forget to add your OPENAI_API_KEY!")

            # Run validation
            print("\nRunning validation checks...\n")
            checks = manager.validate_production_readiness()
            return manager.print_validation_report(checks)
        else:
            manager.print_error(message)
            return 1

    elif args.command == 'check-all':
        checks = manager.validate_production_readiness()
        return manager.print_validation_report(checks)

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
