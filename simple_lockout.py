"""
Simple Security Lockout System
Locks accounts after multiple failed login attempts with automatic unlock.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading


class SimpleLockout:
    """
    Manages login attempt tracking and account lockouts.

    Behavior:
    - Locks after 10 failed attempts within 10 seconds
    - Lockout duration: 60 seconds
    - Auto-unlock after timeout
    - Privacy: Identifiers should be hashed before storage
    """

    def __init__(self, db_path: str = "lockouts.db"):
        """
        Initialize the lockout system.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Table for login attempts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)

            # Table for active locks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locks (
                    identifier TEXT PRIMARY KEY,
                    locked_until TEXT NOT NULL
                )
            """)

            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attempts_identifier
                ON attempts(identifier, timestamp)
            """)

            conn.commit()

    def check_and_record(self, identifier: str) -> Dict[str, any]:
        """
        Check if identifier is locked and record the attempt.

        This is the main method called for each login attempt.

        Args:
            identifier: Unique identifier (hashed IP or username)

        Returns:
            dict with keys:
                - allowed (bool): Whether login attempt is allowed
                - locked (bool): Whether account is currently locked
                - remaining_seconds (int): Seconds until unlock (0 if not locked)
                - attempt_count (int): Number of recent attempts
                - should_alert (bool): Whether to send email alert
                - attempts_remaining (int): Attempts left before lockout
        """
        with self._lock:
            # Check if currently locked
            locked_until = self._get_lock_status(identifier)

            if locked_until:
                remaining = self._calculate_remaining_seconds(locked_until)

                if remaining > 0:
                    # Still locked
                    return {
                        'allowed': False,
                        'locked': True,
                        'remaining_seconds': remaining,
                        'attempt_count': 0,
                        'should_alert': False,
                        'attempts_remaining': 0
                    }
                else:
                    # Lock expired, remove it
                    self._remove_lock(identifier)

            # Record this attempt
            self._record_attempt(identifier)

            # Count attempts in last 10 seconds
            attempt_count = self._count_recent_attempts(identifier, seconds=10)

            # Check if we should trigger lockout
            if attempt_count >= 10:
                # Trigger lockout
                self._create_lock(identifier, duration_seconds=60)

                return {
                    'allowed': False,
                    'locked': True,
                    'remaining_seconds': 60,
                    'attempt_count': attempt_count,
                    'should_alert': True,  # Send email alert
                    'attempts_remaining': 0
                }

            # Attempt allowed
            return {
                'allowed': True,
                'locked': False,
                'remaining_seconds': 0,
                'attempt_count': attempt_count,
                'should_alert': False,
                'attempts_remaining': 10 - attempt_count
            }

    def clear_attempts(self, identifier: str):
        """
        Clear all login attempts for an identifier.

        Call this after successful login to reset the counter.

        Args:
            identifier: Unique identifier to clear
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Remove all attempts
                cursor.execute(
                    "DELETE FROM attempts WHERE identifier = ?",
                    (identifier,)
                )

                # Remove any active lock
                cursor.execute(
                    "DELETE FROM locks WHERE identifier = ?",
                    (identifier,)
                )

                conn.commit()

    def cleanup_old_data(self, days: int = 7):
        """
        Remove old attempt records and expired locks.

        Call this periodically (e.g., daily) to keep database clean.

        Args:
            days: Remove attempts older than this many days
        """
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            cutoff_str = cutoff_time.isoformat()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Remove old attempts
                cursor.execute(
                    "DELETE FROM attempts WHERE timestamp < ?",
                    (cutoff_str,)
                )

                # Remove expired locks
                current_time = datetime.utcnow().isoformat()
                cursor.execute(
                    "DELETE FROM locks WHERE locked_until < ?",
                    (current_time,)
                )

                conn.commit()

                # Vacuum to reclaim space
                cursor.execute("VACUUM")

    def _get_lock_status(self, identifier: str) -> Optional[str]:
        """Get locked_until timestamp if identifier is locked."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT locked_until FROM locks WHERE identifier = ?",
                (identifier,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def _create_lock(self, identifier: str, duration_seconds: int):
        """Create a new lock for identifier."""
        locked_until = datetime.utcnow() + timedelta(seconds=duration_seconds)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO locks (identifier, locked_until) VALUES (?, ?)",
                (identifier, locked_until.isoformat())
            )
            conn.commit()

    def _remove_lock(self, identifier: str):
        """Remove lock for identifier."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM locks WHERE identifier = ?",
                (identifier,)
            )
            conn.commit()

    def _record_attempt(self, identifier: str):
        """Record a login attempt with current timestamp."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO attempts (identifier, timestamp) VALUES (?, ?)",
                (identifier, datetime.utcnow().isoformat())
            )
            conn.commit()

    def _count_recent_attempts(self, identifier: str, seconds: int) -> int:
        """Count attempts for identifier in last N seconds."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=seconds)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM attempts WHERE identifier = ? AND timestamp > ?",
                (identifier, cutoff_time.isoformat())
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def _calculate_remaining_seconds(self, locked_until_str: str) -> int:
        """Calculate remaining seconds until unlock."""
        locked_until = datetime.fromisoformat(locked_until_str)
        remaining = (locked_until - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))

    def get_stats(self, identifier: str) -> Dict[str, any]:
        """
        Get statistics for an identifier (useful for debugging).

        Args:
            identifier: Unique identifier

        Returns:
            dict with attempt count, lock status, etc.
        """
        with self._lock:
            locked_until = self._get_lock_status(identifier)
            attempt_count = self._count_recent_attempts(identifier, seconds=10)

            return {
                'identifier': identifier,
                'locked': bool(locked_until),
                'locked_until': locked_until,
                'remaining_seconds': self._calculate_remaining_seconds(locked_until) if locked_until else 0,
                'recent_attempts': attempt_count,
                'total_attempts': self._count_total_attempts(identifier)
            }

    def _count_total_attempts(self, identifier: str) -> int:
        """Count all attempts for identifier (for stats)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM attempts WHERE identifier = ?",
                (identifier,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    # ==================== Compatibility Methods ====================
    # These methods provide backward compatibility with old API

    def check_lockout(self, identifier: str) -> Dict[str, any]:
        """
        Check if identifier is currently locked out (compatibility method).

        Args:
            identifier: Unique identifier (IP address or username hash)

        Returns:
            dict with keys:
                - locked_out (bool): Whether currently locked
                - time_remaining (str): Human-readable time until unlock
                - attempt_count (int): Number of recent attempts
        """
        with self._lock:
            locked_until = self._get_lock_status(identifier)

            if locked_until:
                remaining = self._calculate_remaining_seconds(locked_until)

                if remaining > 0:
                    return {
                        'locked_out': True,
                        'time_remaining': f"{remaining} seconds",
                        'attempt_count': self._count_recent_attempts(identifier, seconds=10)
                    }
                else:
                    # Lock expired
                    self._remove_lock(identifier)

            # Not locked
            return {
                'locked_out': False,
                'time_remaining': '0 seconds',
                'attempt_count': self._count_recent_attempts(identifier, seconds=10)
            }

    def record_failure(self, identifier: str):
        """
        Record a failed login attempt (compatibility method).

        This will record the attempt and potentially trigger a lockout
        if too many attempts are made.

        Args:
            identifier: Unique identifier (IP address or username hash)
        """
        result = self.check_and_record(identifier)
        return result

    def record_success(self, identifier: str):
        """
        Record a successful login (compatibility method).

        This clears all attempts and any active lockout for the identifier.

        Args:
            identifier: Unique identifier (IP address or username hash)
        """
        self.clear_attempts(identifier)
