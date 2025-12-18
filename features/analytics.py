#!/usr/bin/env python3
"""
User Analytics and Cost Estimation
Provides insights into user behavior and API usage costs
"""

import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class UserAnalytics:
    """
    Analyze user behavior and usage patterns
    """

    def __init__(self, db_path: str = 'voiceverse.db'):
        self.db_path = db_path

    def get_user_stats(self, user_id: int, days: int = 30) -> Dict:
        """
        Get comprehensive user statistics

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Dict with user statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        # Basic user info
        cursor.execute('SELECT username, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return {'error': 'User not found'}

        stats = {
            'user_id': user_id,
            'username': user['username'],
            'member_since': user['created_at'],
            'analysis_period_days': days
        }

        # TTS generation stats
        cursor.execute('''
            SELECT
                COUNT(*) as total_generations,
                SUM(character_count) as total_characters,
                AVG(character_count) as avg_characters
            FROM tts_history
            WHERE user_id = ? AND created_at >= ?
        ''', (user_id, cutoff_date))

        tts_stats = cursor.fetchone()
        stats['tts'] = {
            'total_generations': tts_stats['total_generations'] or 0,
            'total_characters': tts_stats['total_characters'] or 0,
            'avg_characters_per_generation': round(tts_stats['avg_characters'] or 0, 2)
        }

        # Voice usage breakdown
        cursor.execute('''
            SELECT voice, COUNT(*) as count
            FROM tts_history
            WHERE user_id = ? AND created_at >= ?
            GROUP BY voice
            ORDER BY count DESC
        ''', (user_id, cutoff_date))

        voice_usage = {row['voice']: row['count'] for row in cursor.fetchall()}
        stats['voice_usage'] = voice_usage

        # Model usage breakdown
        cursor.execute('''
            SELECT model, COUNT(*) as count
            FROM tts_history
            WHERE user_id = ? AND created_at >= ?
            GROUP BY model
            ORDER BY count DESC
        ''', (user_id, cutoff_date))

        model_usage = {row['model']: row['count'] for row in cursor.fetchall()}
        stats['model_usage'] = model_usage

        # Activity timeline (daily breakdown)
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM tts_history
            WHERE user_id = ? AND created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''', (user_id, cutoff_date))

        activity_timeline = {row['date']: row['count'] for row in cursor.fetchall()}
        stats['activity_timeline'] = activity_timeline

        # Saved audio count
        cursor.execute('''
            SELECT COUNT(*) as saved_count
            FROM saved_audio
            WHERE user_id = ?
        ''', (user_id,))

        stats['saved_audio_count'] = cursor.fetchone()['saved_count']

        # Document processing stats
        cursor.execute('''
            SELECT
                COUNT(DISTINCT CASE WHEN text LIKE '%.pdf%' THEN id END) as pdf_count,
                COUNT(DISTINCT CASE WHEN text LIKE '%.docx%' THEN id END) as docx_count
            FROM tts_history
            WHERE user_id = ? AND created_at >= ?
        ''', (user_id, cutoff_date))

        doc_stats = cursor.fetchone()
        stats['document_processing'] = {
            'pdf_files': doc_stats['pdf_count'] or 0,
            'docx_files': doc_stats['docx_count'] or 0
        }

        conn.close()
        return stats

    def get_global_stats(self, days: int = 30) -> Dict:
        """
        Get platform-wide statistics

        Args:
            days: Number of days to analyze

        Returns:
            Global statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        stats = {'period_days': days}

        # Total users
        cursor.execute('SELECT COUNT(*) as count FROM users')
        stats['total_users'] = cursor.fetchone()['count']

        # Active users (generated TTS in period)
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) as count
            FROM tts_history
            WHERE created_at >= ?
        ''', (cutoff_date,))
        stats['active_users'] = cursor.fetchone()['count']

        # TTS statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_generations,
                SUM(character_count) as total_characters,
                AVG(character_count) as avg_characters
            FROM tts_history
            WHERE created_at >= ?
        ''', (cutoff_date,))

        tts_stats = cursor.fetchone()
        stats['tts'] = {
            'total_generations': tts_stats['total_generations'] or 0,
            'total_characters': tts_stats['total_characters'] or 0,
            'avg_characters': round(tts_stats['avg_characters'] or 0, 2)
        }

        # Most popular voices
        cursor.execute('''
            SELECT voice, COUNT(*) as count
            FROM tts_history
            WHERE created_at >= ?
            GROUP BY voice
            ORDER BY count DESC
            LIMIT 5
        ''', (cutoff_date,))

        stats['popular_voices'] = {row['voice']: row['count'] for row in cursor.fetchall()}

        # Most popular models
        cursor.execute('''
            SELECT model, COUNT(*) as count
            FROM tts_history
            WHERE created_at >= ?
            GROUP BY model
            ORDER BY count DESC
        ''', (cutoff_date,))

        stats['model_usage'] = {row['model']: row['count'] for row in cursor.fetchall()}

        # Top users by generation count
        cursor.execute('''
            SELECT u.username, COUNT(h.id) as generation_count
            FROM tts_history h
            JOIN users u ON h.user_id = u.id
            WHERE h.created_at >= ?
            GROUP BY h.user_id
            ORDER BY generation_count DESC
            LIMIT 10
        ''', (cutoff_date,))

        stats['top_users'] = [
            {'username': row['username'], 'generations': row['generation_count']}
            for row in cursor.fetchall()
        ]

        conn.close()
        return stats

    def get_usage_trends(self, days: int = 30) -> Dict:
        """
        Get usage trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Trend data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        # Daily generation counts
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM tts_history
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (cutoff_date,))

        daily_generations = {row['date']: row['count'] for row in cursor.fetchall()}

        # Daily character counts
        cursor.execute('''
            SELECT DATE(created_at) as date, SUM(character_count) as total
            FROM tts_history
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (cutoff_date,))

        daily_characters = {row['date']: row['total'] for row in cursor.fetchall()}

        # New user signups
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM users
            WHERE created_at >= ?
            GROUP BY DATE(created_at)
            ORDER BY date
        ''', (cutoff_date,))

        daily_signups = {row['date']: row['count'] for row in cursor.fetchall()}

        conn.close()

        return {
            'daily_generations': daily_generations,
            'daily_characters': daily_characters,
            'daily_signups': daily_signups
        }


class CostEstimator:
    """
    Estimate and track OpenAI API costs
    """

    # OpenAI TTS pricing (as of 2024)
    PRICING = {
        'tts-1': 0.015,      # $ per 1K characters
        'tts-1-hd': 0.030    # $ per 1K characters
    }

    def __init__(self, db_path: str = 'voiceverse.db'):
        self.db_path = db_path

    def estimate_cost(self, text: str, model: str = 'tts-1') -> float:
        """
        Estimate cost for a single TTS generation

        Args:
            text: Text to convert
            model: TTS model

        Returns:
            Estimated cost in USD
        """
        char_count = len(text)
        price_per_1k = self.PRICING.get(model, self.PRICING['tts-1'])

        return (char_count / 1000) * price_per_1k

    def get_user_costs(self, user_id: int, days: int = 30) -> Dict:
        """
        Calculate actual costs for a user

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Cost breakdown
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all generations with character counts
        cursor.execute('''
            SELECT model, SUM(character_count) as total_chars
            FROM tts_history
            WHERE user_id = ? AND created_at >= ?
            GROUP BY model
        ''', (user_id, cutoff_date))

        model_costs = {}
        total_cost = 0

        for row in cursor.fetchall():
            model = row['model']
            chars = row['total_chars'] or 0
            price_per_1k = self.PRICING.get(model, self.PRICING['tts-1'])
            cost = (chars / 1000) * price_per_1k

            model_costs[model] = {
                'characters': chars,
                'cost_usd': round(cost, 4)
            }
            total_cost += cost

        conn.close()

        return {
            'user_id': user_id,
            'period_days': days,
            'model_breakdown': model_costs,
            'total_cost_usd': round(total_cost, 4)
        }

    def get_global_costs(self, days: int = 30) -> Dict:
        """
        Calculate total platform costs

        Args:
            days: Number of days to analyze

        Returns:
            Global cost breakdown
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        # Get all generations
        cursor.execute('''
            SELECT model, SUM(character_count) as total_chars
            FROM tts_history
            WHERE created_at >= ?
            GROUP BY model
        ''', (cutoff_date,))

        model_costs = {}
        total_cost = 0

        for row in cursor.fetchall():
            model = row['model']
            chars = row['total_chars'] or 0
            price_per_1k = self.PRICING.get(model, self.PRICING['tts-1'])
            cost = (chars / 1000) * price_per_1k

            model_costs[model] = {
                'characters': chars,
                'cost_usd': round(cost, 4)
            }
            total_cost += cost

        # Daily cost breakdown
        cursor.execute('''
            SELECT
                DATE(created_at) as date,
                model,
                SUM(character_count) as total_chars
            FROM tts_history
            WHERE created_at >= ?
            GROUP BY DATE(created_at), model
            ORDER BY date DESC
        ''', (cutoff_date,))

        daily_costs = defaultdict(float)
        for row in cursor.fetchall():
            date = row['date']
            model = row['model']
            chars = row['total_chars'] or 0
            price_per_1k = self.PRICING.get(model, self.PRICING['tts-1'])
            cost = (chars / 1000) * price_per_1k
            daily_costs[date] += cost

        conn.close()

        return {
            'period_days': days,
            'model_breakdown': model_costs,
            'total_cost_usd': round(total_cost, 4),
            'daily_costs': {date: round(cost, 4) for date, cost in daily_costs.items()},
            'avg_daily_cost': round(total_cost / days, 4) if days > 0 else 0
        }

    def project_monthly_cost(self, days_sample: int = 7) -> Dict:
        """
        Project monthly cost based on recent usage

        Args:
            days_sample: Number of recent days to use for projection

        Returns:
            Cost projection
        """
        recent_costs = self.get_global_costs(days=days_sample)

        avg_daily = recent_costs['avg_daily_cost']
        projected_monthly = avg_daily * 30

        return {
            'sample_period_days': days_sample,
            'avg_daily_cost': avg_daily,
            'projected_monthly_cost': round(projected_monthly, 2),
            'confidence': 'high' if days_sample >= 7 else 'low'
        }

    def get_cost_by_user(self, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Get top users by cost

        Args:
            days: Number of days to analyze
            limit: Number of top users to return

        Returns:
            List of users with costs
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT
                u.username,
                h.user_id,
                h.model,
                SUM(h.character_count) as total_chars
            FROM tts_history h
            JOIN users u ON h.user_id = u.id
            WHERE h.created_at >= ?
            GROUP BY h.user_id, h.model
        ''', (cutoff_date,))

        user_costs = defaultdict(lambda: {'username': '', 'total_cost': 0, 'models': {}})

        for row in cursor.fetchall():
            user_id = row['user_id']
            username = row['username']
            model = row['model']
            chars = row['total_chars'] or 0

            price_per_1k = self.PRICING.get(model, self.PRICING['tts-1'])
            cost = (chars / 1000) * price_per_1k

            user_costs[user_id]['username'] = username
            user_costs[user_id]['total_cost'] += cost
            user_costs[user_id]['models'][model] = round(cost, 4)

        conn.close()

        # Sort by total cost
        sorted_users = sorted(
            [{'user_id': uid, **data} for uid, data in user_costs.items()],
            key=lambda x: x['total_cost'],
            reverse=True
        )[:limit]

        # Round total costs
        for user in sorted_users:
            user['total_cost'] = round(user['total_cost'], 4)

        return sorted_users


if __name__ == '__main__':
    # Test analytics
    analytics = UserAnalytics()
    estimator = CostEstimator()

    print("User Analytics and Cost Estimator initialized")
    print(f"TTS-1 pricing: ${estimator.PRICING['tts-1']} per 1K characters")
    print(f"TTS-1-HD pricing: ${estimator.PRICING['tts-1-hd']} per 1K characters")

    # Example cost estimation
    sample_text = "This is a sample text for cost estimation."
    cost = estimator.estimate_cost(sample_text, 'tts-1')
    print(f"\nSample text ({len(sample_text)} chars) estimated cost: ${cost:.6f}")
