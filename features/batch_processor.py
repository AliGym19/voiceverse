#!/usr/bin/env python3
"""
Batch TTS Processing System
Allows processing multiple text inputs in a single operation
"""

import os
import json
import time
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import threading
from queue import Queue


class BatchProcessor:
    """
    Handles batch TTS processing operations
    """

    def __init__(self, db_path: str = 'voiceverse.db'):
        self.db_path = db_path
        self.processing_queue = Queue()
        self.results = {}
        self.init_database()

    def init_database(self):
        """Initialize batch processing tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Batch jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                total_items INTEGER DEFAULT 0,
                completed_items INTEGER DEFAULT 0,
                failed_items INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Batch items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS batch_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_job_id INTEGER NOT NULL,
                item_order INTEGER NOT NULL,
                text TEXT NOT NULL,
                voice TEXT NOT NULL,
                model TEXT NOT NULL,
                speed REAL DEFAULT 1.0,
                status TEXT DEFAULT 'pending',
                audio_path TEXT,
                duration REAL,
                error_message TEXT,
                processed_at TIMESTAMP,
                FOREIGN KEY (batch_job_id) REFERENCES batch_jobs(id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_batch_job(self, user_id: int, name: str, items: List[Dict]) -> int:
        """
        Create a new batch job

        Args:
            user_id: User ID
            name: Job name
            items: List of dicts with keys: text, voice, model, speed

        Returns:
            Job ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create job
        cursor.execute('''
            INSERT INTO batch_jobs (user_id, name, total_items, status)
            VALUES (?, ?, ?, 'pending')
        ''', (user_id, name, len(items)))

        job_id = cursor.lastrowid

        # Create items
        for idx, item in enumerate(items):
            cursor.execute('''
                INSERT INTO batch_items
                (batch_job_id, item_order, text, voice, model, speed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                idx,
                item['text'],
                item.get('voice', 'alloy'),
                item.get('model', 'tts-1'),
                item.get('speed', 1.0)
            ))

        conn.commit()
        conn.close()

        return job_id

    def get_batch_job(self, job_id: int) -> Optional[Dict]:
        """Get batch job details"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM batch_jobs WHERE id = ?
        ''', (job_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_batch_items(self, job_id: int) -> List[Dict]:
        """Get all items for a batch job"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM batch_items
            WHERE batch_job_id = ?
            ORDER BY item_order
        ''', (job_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_job_status(self, job_id: int, status: str,
                         error_message: Optional[str] = None):
        """Update job status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        update_fields = ['status = ?']
        params = [status]

        if status == 'processing' and error_message is None:
            update_fields.append('started_at = CURRENT_TIMESTAMP')
        elif status in ('completed', 'failed'):
            update_fields.append('completed_at = CURRENT_TIMESTAMP')

        if error_message:
            update_fields.append('error_message = ?')
            params.append(error_message)

        params.append(job_id)

        cursor.execute(f'''
            UPDATE batch_jobs
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)

        conn.commit()
        conn.close()

    def update_item_status(self, item_id: int, status: str,
                          audio_path: Optional[str] = None,
                          duration: Optional[float] = None,
                          error_message: Optional[str] = None):
        """Update batch item status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        update_fields = ['status = ?']
        params = [status]

        if audio_path:
            update_fields.append('audio_path = ?')
            params.append(audio_path)

        if duration is not None:
            update_fields.append('duration = ?')
            params.append(duration)

        if error_message:
            update_fields.append('error_message = ?')
            params.append(error_message)

        if status in ('completed', 'failed'):
            update_fields.append('processed_at = CURRENT_TIMESTAMP')

        params.append(item_id)

        cursor.execute(f'''
            UPDATE batch_items
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)

        # Update job counts
        cursor.execute('''
            SELECT batch_job_id FROM batch_items WHERE id = ?
        ''', (item_id,))

        job_id = cursor.fetchone()[0]

        cursor.execute('''
            UPDATE batch_jobs
            SET completed_items = (
                SELECT COUNT(*) FROM batch_items
                WHERE batch_job_id = ? AND status = 'completed'
            ),
            failed_items = (
                SELECT COUNT(*) FROM batch_items
                WHERE batch_job_id = ? AND status = 'failed'
            )
            WHERE id = ?
        ''', (job_id, job_id, job_id))

        conn.commit()
        conn.close()

    def get_user_jobs(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get all batch jobs for a user"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM batch_jobs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def delete_batch_job(self, job_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Delete a batch job and its items

        Returns:
            (success, message)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Verify ownership
        cursor.execute('''
            SELECT user_id FROM batch_jobs WHERE id = ?
        ''', (job_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Job not found"

        if row[0] != user_id:
            conn.close()
            return False, "Unauthorized"

        # Delete items first
        cursor.execute('DELETE FROM batch_items WHERE batch_job_id = ?', (job_id,))

        # Delete job
        cursor.execute('DELETE FROM batch_jobs WHERE id = ?', (job_id,))

        conn.commit()
        conn.close()

        return True, "Job deleted successfully"

    def get_job_progress(self, job_id: int) -> Dict:
        """Get progress information for a job"""
        job = self.get_batch_job(job_id)

        if not job:
            return {'error': 'Job not found'}

        total = job['total_items']
        completed = job['completed_items']
        failed = job['failed_items']

        progress_pct = 0
        if total > 0:
            progress_pct = ((completed + failed) / total) * 100

        return {
            'job_id': job_id,
            'name': job['name'],
            'status': job['status'],
            'total_items': total,
            'completed_items': completed,
            'failed_items': failed,
            'pending_items': total - completed - failed,
            'progress_percentage': round(progress_pct, 2),
            'created_at': job['created_at'],
            'started_at': job['started_at'],
            'completed_at': job['completed_at'],
            'error_message': job['error_message']
        }

    def export_batch_results(self, job_id: int, format: str = 'json') -> Optional[str]:
        """
        Export batch results

        Args:
            job_id: Batch job ID
            format: 'json' or 'csv'

        Returns:
            Export data as string
        """
        job = self.get_batch_job(job_id)
        items = self.get_batch_items(job_id)

        if not job:
            return None

        if format == 'json':
            data = {
                'job': job,
                'items': items
            }
            return json.dumps(data, indent=2, default=str)

        elif format == 'csv':
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                'Item Order', 'Text', 'Voice', 'Model', 'Speed',
                'Status', 'Audio Path', 'Duration', 'Error'
            ])

            # Data rows
            for item in items:
                writer.writerow([
                    item['item_order'],
                    item['text'][:50] + '...' if len(item['text']) > 50 else item['text'],
                    item['voice'],
                    item['model'],
                    item['speed'],
                    item['status'],
                    item['audio_path'] or '',
                    item['duration'] or '',
                    item['error_message'] or ''
                ])

            return output.getvalue()

        return None


if __name__ == '__main__':
    # Test batch processor
    processor = BatchProcessor()
    print("Batch Processor initialized successfully")

    # Example: Create a test batch job
    test_items = [
        {'text': 'Hello world', 'voice': 'alloy', 'model': 'tts-1', 'speed': 1.0},
        {'text': 'This is a test', 'voice': 'echo', 'model': 'tts-1', 'speed': 1.0}
    ]

    # Would need a valid user_id from database
    print("Batch Processor ready for integration")
