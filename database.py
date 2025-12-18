"""
VoiceVerse TTS - Database Abstraction Layer
Created: October 24, 2025
Purpose: Provide ACID-compliant database operations for replacing JSON files
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any


class Database:
    """
    Lightweight database wrapper for SQLite operations.
    Provides parameterized queries to prevent SQL injection.
    """

    def __init__(self, db_path='voiceverse.db'):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialize_schema()

    def _get_connection(self):
        """Get database connection with foreign keys enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor with automatic commit/rollback"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_schema(self):
        """Initialize database schema if it doesn't exist"""
        schema_file = os.path.join(os.path.dirname(__file__), 'database_schema.sql')

        # Try to load from file first
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
        else:
            # Fallback to inline schema for testing or when file is missing
            schema_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                openai_api_key TEXT,
                api_key_set_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                CONSTRAINT username_length CHECK (length(username) >= 3)
            );

            CREATE TABLE IF NOT EXISTS audio_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                voice TEXT NOT NULL,
                category TEXT,
                text TEXT,
                character_count INTEGER NOT NULL,
                duration REAL,
                cost REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                characters_used INTEGER NOT NULL,
                cost REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS playback_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES audio_files(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                username TEXT,
                ip_address TEXT NOT NULL,
                details TEXT,
                success BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_audio_owner ON audio_files(owner_id);
            CREATE INDEX IF NOT EXISTS idx_audio_created ON audio_files(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_audio_filename ON audio_files(filename);
            CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage_stats(user_id, year, month);
            CREATE INDEX IF NOT EXISTS idx_playback_user ON playback_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_playback_file ON playback_history(file_id);
            CREATE INDEX IF NOT EXISTS idx_playback_timestamp ON playback_history(played_at DESC);
            CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_logs(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_security_type ON security_logs(event_type);
            CREATE INDEX IF NOT EXISTS idx_security_user ON security_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

            PRAGMA foreign_keys = ON;
            """

        # Execute the schema
        with self._get_cursor() as cursor:
            cursor.executescript(schema_sql)

    def execute(self, query: str, params: Optional[Tuple] = None) -> sqlite3.Cursor:
        """
        Execute a query with optional parameters.

        Args:
            query: SQL query with ? placeholders
            params: Tuple of parameters to bind

        Returns:
            Cursor after execution
        """
        with self._get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor

    def fetchone(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
        """
        Fetch one row from query results.

        Args:
            query: SQL query with ? placeholders
            params: Tuple of parameters to bind

        Returns:
            Dictionary of column:value pairs or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def fetchall(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        Fetch all rows from query results.

        Args:
            query: SQL query with ? placeholders
            params: Tuple of parameters to bind

        Returns:
            List of dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ==================== User Operations ====================

    def create_user(self, username: str, password_hash: str) -> Optional[int]:
        """
        Create a new user.

        Args:
            username: Unique username (min 3 chars)
            password_hash: Hashed password

        Returns:
            User ID if successful, None if username exists
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Username already exists
            return None

    def get_user(self, username: str) -> Optional[Dict]:
        """
        Get user by username.

        Args:
            username: Username to look up

        Returns:
            User dictionary or None
        """
        return self.fetchone(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Get user by ID.

        Args:
            user_id: User ID to look up

        Returns:
            User dictionary or None
        """
        return self.fetchone(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )

    def update_last_login(self, user_id: int) -> bool:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )
                return cursor.rowcount > 0
        except Exception:
            return False

    def list_users(self) -> List[Dict]:
        """
        Get all users.

        Returns:
            List of user dictionaries
        """
        return self.fetchall("SELECT id, username, created_at, last_login, is_active FROM users")

    def set_user_api_key(self, user_id: int, encrypted_api_key: str) -> bool:
        """
        Set or update user's OpenAI API key (should be encrypted before storing).

        Args:
            user_id: User ID
            encrypted_api_key: Encrypted API key string

        Returns:
            True if successful
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """UPDATE users
                       SET openai_api_key = ?, api_key_set_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (encrypted_api_key, user_id)
                )
                return cursor.rowcount > 0
        except Exception:
            return False

    def get_user_api_key(self, user_id: int) -> Optional[str]:
        """
        Get user's encrypted OpenAI API key.

        Args:
            user_id: User ID

        Returns:
            Encrypted API key or None
        """
        result = self.fetchone(
            "SELECT openai_api_key FROM users WHERE id = ?",
            (user_id,)
        )
        return result['openai_api_key'] if result else None

    def has_api_key(self, user_id: int) -> bool:
        """
        Check if user has set their API key.

        Args:
            user_id: User ID

        Returns:
            True if API key is set
        """
        result = self.fetchone(
            "SELECT openai_api_key FROM users WHERE id = ?",
            (user_id,)
        )
        return result is not None and result['openai_api_key'] is not None

    def delete_user_api_key(self, user_id: int) -> bool:
        """
        Delete user's API key.

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET openai_api_key = NULL, api_key_set_at = NULL WHERE id = ?",
                    (user_id,)
                )
                return cursor.rowcount > 0
        except Exception:
            return False

    # ==================== Audio File Operations ====================

    def create_audio_file(
        self,
        filename: str,
        display_name: str,
        owner_id: int,
        voice: str,
        category: Optional[str],
        text: Optional[str],
        character_count: int,
        cost: float,
        duration: Optional[float] = None
    ) -> Optional[int]:
        """
        Create a new audio file record.

        Args:
            filename: Unique filename
            display_name: Display name for UI
            owner_id: User ID of owner
            voice: Voice used for TTS
            category: Category/group
            text: Original text
            character_count: Number of characters
            cost: Cost in USD
            duration: Duration in seconds

        Returns:
            File ID if successful, None if filename exists
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO audio_files
                       (filename, display_name, owner_id, voice, category, text,
                        character_count, cost, duration)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (filename, display_name, owner_id, voice, category, text,
                     character_count, cost, duration)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Filename already exists
            return None

    def get_audio_file(self, filename: str) -> Optional[Dict]:
        """
        Get audio file by filename.

        Args:
            filename: Filename to look up

        Returns:
            Audio file dictionary or None
        """
        return self.fetchone(
            "SELECT * FROM audio_files WHERE filename = ?",
            (filename,)
        )

    def get_audio_file_by_id(self, file_id: int) -> Optional[Dict]:
        """
        Get audio file by ID.

        Args:
            file_id: File ID to look up

        Returns:
            Audio file dictionary or None
        """
        return self.fetchone(
            "SELECT * FROM audio_files WHERE id = ?",
            (file_id,)
        )

    def get_audio_files_by_owner(self, owner_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all audio files for a user.

        Args:
            owner_id: User ID
            limit: Maximum number of files to return

        Returns:
            List of audio file dictionaries
        """
        query = "SELECT * FROM audio_files WHERE owner_id = ? ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"

        return self.fetchall(query, (owner_id,))

    def get_all_audio_files(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all audio files (for migration/admin purposes).

        Args:
            limit: Maximum number of files to return

        Returns:
            List of audio file dictionaries
        """
        query = "SELECT * FROM audio_files ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {int(limit)}"

        return self.fetchall(query)

    def update_audio_file(self, file_id: int, **kwargs) -> bool:
        """
        Update audio file fields.

        Args:
            file_id: File ID to update
            **kwargs: Fields to update (display_name, category, etc.)

        Returns:
            True if successful
        """
        if not kwargs:
            return False

        # Build SET clause dynamically
        set_clauses = []
        values = []
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)

        # Always update updated_at
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        values.append(file_id)

        query = f"UPDATE audio_files SET {', '.join(set_clauses)} WHERE id = ?"

        try:
            with self._get_cursor() as cursor:
                cursor.execute(query, tuple(values))
                return cursor.rowcount > 0
        except Exception:
            return False

    def delete_audio_file(self, file_id: int) -> bool:
        """
        Delete audio file record.

        Args:
            file_id: File ID to delete

        Returns:
            True if successful
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM audio_files WHERE id = ?", (file_id,))
                return cursor.rowcount > 0
        except Exception:
            return False

    # ==================== Usage Statistics ====================

    def record_usage(self, user_id: int, characters: int, cost: float) -> Optional[int]:
        """
        Record usage statistics for a user.

        Args:
            user_id: User ID
            characters: Number of characters processed
            cost: Cost in USD

        Returns:
            Record ID if successful
        """
        now = datetime.now()
        month = now.strftime('%Y-%m')
        year = now.year

        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO usage_stats
                       (user_id, characters_used, cost, month, year)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, characters, cost, month, year)
                )
                return cursor.lastrowid
        except Exception:
            return None

    def get_monthly_usage(self, user_id: int, year: int, month: str) -> Dict[str, Any]:
        """
        Get usage statistics for a specific month.

        Args:
            user_id: User ID
            year: Year (YYYY)
            month: Month (YYYY-MM format)

        Returns:
            Dictionary with total_characters and total_cost
        """
        result = self.fetchone(
            """SELECT
                   SUM(characters_used) as total_characters,
                   SUM(cost) as total_cost,
                   COUNT(*) as request_count
               FROM usage_stats
               WHERE user_id = ? AND year = ? AND month = ?""",
            (user_id, year, month)
        )

        if result and result['total_characters']:
            return result
        else:
            return {'total_characters': 0, 'total_cost': 0.0, 'request_count': 0}

    def get_all_time_usage(self, user_id: int) -> Dict[str, Any]:
        """
        Get all-time usage statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with total_characters and total_cost
        """
        result = self.fetchone(
            """SELECT
                   SUM(characters_used) as total_characters,
                   SUM(cost) as total_cost,
                   COUNT(*) as request_count
               FROM usage_stats
               WHERE user_id = ?""",
            (user_id,)
        )

        if result and result['total_characters']:
            return result
        else:
            return {'total_characters': 0, 'total_cost': 0.0, 'request_count': 0}

    def get_system_wide_usage(self) -> Dict[str, Any]:
        """
        Get system-wide usage statistics across ALL users.

        Returns:
            Dictionary with total_characters and total_cost for all users
        """
        result = self.fetchone(
            """SELECT
                   SUM(characters_used) as total_characters,
                   SUM(cost) as total_cost,
                   COUNT(*) as request_count
               FROM usage_stats"""
        )

        if result and result['total_characters']:
            return result
        else:
            return {'total_characters': 0, 'total_cost': 0.0, 'request_count': 0}

    # ==================== Playback History ====================

    def record_playback(self, user_id: int, file_id: int) -> Optional[int]:
        """
        Record a playback event.

        Args:
            user_id: User ID
            file_id: Audio file ID

        Returns:
            Record ID if successful
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO playback_history (user_id, file_id) VALUES (?, ?)",
                    (user_id, file_id)
                )
                return cursor.lastrowid
        except Exception:
            return None

    def get_playback_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get playback history for a user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return

        Returns:
            List of playback records with file details
        """
        return self.fetchall(
            """SELECT
                   ph.id, ph.played_at,
                   af.filename, af.display_name, af.voice, af.category
               FROM playback_history ph
               JOIN audio_files af ON ph.file_id = af.id
               WHERE ph.user_id = ?
               ORDER BY ph.played_at DESC
               LIMIT ?""",
            (user_id, limit)
        )

    # ==================== Security Logging ====================

    def log_security_event(
        self,
        event_type: str,
        ip_address: str,
        success: bool,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[str] = None
    ) -> Optional[int]:
        """
        Log a security event.

        Args:
            event_type: Type of event (AUTH_LOGIN, FILE_ACCESS, etc.)
            ip_address: IP address of request
            success: Whether the action succeeded
            user_id: User ID (if applicable)
            username: Username (if user_id not available)
            details: Additional details

        Returns:
            Log ID if successful
        """
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO security_logs
                       (event_type, user_id, username, ip_address, details, success)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (event_type, user_id, username, ip_address, details, success)
                )
                return cursor.lastrowid
        except Exception:
            return None

    def get_security_logs(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        user_id: Optional[int] = None,
        success: Optional[bool] = None
    ) -> List[Dict]:
        """
        Get security logs with optional filtering.

        Args:
            limit: Maximum number of logs to return
            event_type: Filter by event type
            user_id: Filter by user ID
            success: Filter by success status

        Returns:
            List of security log dictionaries
        """
        query = "SELECT * FROM security_logs WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)

        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        return self.fetchall(query, tuple(params))

    def get_failed_login_attempts(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get recent failed login attempts for security monitoring.

        Args:
            hours: Look back this many hours
            limit: Maximum number of records to return

        Returns:
            List of failed login attempts
        """
        return self.fetchall(
            """SELECT * FROM security_logs
               WHERE event_type IN ('AUTH_FAILURE', 'AUTH_LOGIN')
                 AND success = 0
                 AND timestamp > datetime('now', '-' || ? || ' hours')
               ORDER BY timestamp DESC
               LIMIT ?""",
            (hours, limit)
        )

    # ==================== Database Maintenance ====================

    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.

        Returns:
            Dictionary with record counts
        """
        return {
            'users': self.fetchone("SELECT COUNT(*) as count FROM users")['count'],
            'audio_files': self.fetchone("SELECT COUNT(*) as count FROM audio_files")['count'],
            'usage_records': self.fetchone("SELECT COUNT(*) as count FROM usage_stats")['count'],
            'playback_records': self.fetchone("SELECT COUNT(*) as count FROM playback_history")['count'],
            'security_logs': self.fetchone("SELECT COUNT(*) as count FROM security_logs")['count']
        }

    def vacuum(self):
        """
        Vacuum database to reclaim space and optimize performance.
        Should be run periodically.
        """
        conn = self._get_connection()
        conn.execute("VACUUM")
        conn.close()

    def backup(self, backup_path: str) -> bool:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for backup file

        Returns:
            True if successful
        """
        try:
            source = self._get_connection()
            backup = sqlite3.connect(backup_path)
            source.backup(backup)
            backup.close()
            source.close()
            return True
        except Exception:
            return False
