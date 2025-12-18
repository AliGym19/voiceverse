#!/usr/bin/env python3
"""
API Key Management System
Allows users to create and manage API keys for programmatic access
"""

import secrets
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict


class APIKeyManager:
    """Manages API keys for users"""

    def __init__(self, db_path: str = 'voiceverse.db'):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        """Create API keys table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_hash TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                rate_limit INTEGER DEFAULT 1000,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()

    def generate_key(self) -> str:
        """Generate a new API key"""
        return f"vv_{secrets.token_urlsafe(32)}"

    def hash_key(self, key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()

    def create_key(
        self,
        user_id: int,
        name: str,
        expires_days: Optional[int] = None,
        rate_limit: int = 1000
    ) -> Tuple[str, Dict]:
        """Create a new API key for a user"""
        key = self.generate_key()
        key_hash = self.hash_key(key)
        key_prefix = key[:12]

        created_at = datetime.utcnow().isoformat() + 'Z'
        expires_at = None
        if expires_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat() + 'Z'

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            '''INSERT INTO api_keys (user_id, key_hash, key_prefix, name, created_at, expires_at, rate_limit)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, key_hash, key_prefix, name, created_at, expires_at, rate_limit)
        )
        key_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return key, {
            'id': key_id,
            'prefix': key_prefix,
            'name': name,
            'created_at': created_at,
            'expires_at': expires_at,
            'rate_limit': rate_limit
        }

    def verify_key(self, key: str) -> Optional[Dict]:
        """Verify an API key and return user info"""
        key_hash = self.hash_key(key)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            '''SELECT id, user_id, name, expires_at, is_active, rate_limit
               FROM api_keys WHERE key_hash = ?''',
            (key_hash,)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return None

        key_id, user_id, name, expires_at, is_active, rate_limit = result

        # Check if active
        if not is_active:
            conn.close()
            return None

        # Check expiration
        if expires_at:
            if datetime.fromisoformat(expires_at.replace('Z', '')) < datetime.utcnow():
                conn.close()
                return None

        # Update last used
        conn.execute(
            'UPDATE api_keys SET last_used_at = ? WHERE id = ?',
            (datetime.utcnow().isoformat() + 'Z', key_id)
        )
        conn.commit()
        conn.close()

        return {
            'key_id': key_id,
            'user_id': user_id,
            'name': name,
            'rate_limit': rate_limit
        }

    def list_keys(self, user_id: int) -> List[Dict]:
        """List all API keys for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            '''SELECT id, key_prefix, name, created_at, last_used_at, expires_at, is_active, rate_limit
               FROM api_keys WHERE user_id = ? ORDER BY created_at DESC''',
            (user_id,)
        )
        results = cursor.fetchall()
        conn.close()

        return [
            {
                'id': r[0],
                'prefix': r[1],
                'name': r[2],
                'created_at': r[3],
                'last_used_at': r[4],
                'expires_at': r[5],
                'is_active': bool(r[6]),
                'rate_limit': r[7]
            }
            for r in results
        ]

    def revoke_key(self, key_id: int, user_id: int) -> bool:
        """Revoke an API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?',
            (key_id, user_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def delete_key(self, key_id: int, user_id: int) -> bool:
        """Delete an API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            'DELETE FROM api_keys WHERE id = ? AND user_id = ?',
            (key_id, user_id)
        )
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
