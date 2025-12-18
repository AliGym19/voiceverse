#!/usr/bin/env python3
"""
VoiceVerse Metrics Collector
Collects and exposes metrics in Prometheus format

Usage:
    from monitoring.metrics_collector import MetricsCollector

    metrics = MetricsCollector()
    metrics.record_request('/api/tts', method='POST', status_code=200, duration=0.5)
    metrics.record_tts_generation(duration=2.3, voice='alloy', success=True)

    # Get Prometheus-format metrics
    prometheus_output = metrics.export_prometheus()
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from pathlib import Path
import sqlite3
import os


class MetricsCollector:
    """Collects application metrics for monitoring and alerting"""

    def __init__(self, db_path: str = 'voiceverse.db'):
        self.db_path = db_path
        self.start_time = time.time()

        # Request metrics
        self.request_count = defaultdict(int)
        self.request_duration = defaultdict(list)
        self.status_codes = defaultdict(int)

        # TTS metrics
        self.tts_total = 0
        self.tts_success = 0
        self.tts_failure = 0
        self.tts_duration = deque(maxlen=1000)
        self.tts_by_voice = defaultdict(int)

        # User metrics
        self.active_sessions = set()
        self.login_attempts = defaultdict(int)
        self.failed_logins = defaultdict(int)

        # Database metrics
        self.db_query_count = 0
        self.db_query_duration = deque(maxlen=1000)

        # Error metrics
        self.errors_by_type = defaultdict(int)
        self.errors_last_hour = deque(maxlen=1000)

        # Rate limiting metrics
        self.rate_limit_hits = defaultdict(int)

        # System metrics cache (updated every 60 seconds)
        self.system_metrics_cache = {}
        self.last_system_update = 0
        self.cache_duration = 60

        # Lock for thread safety
        self.lock = threading.Lock()

    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration: float
    ):
        """Record HTTP request metrics"""
        with self.lock:
            key = f"{method}_{endpoint}"
            self.request_count[key] += 1
            self.request_duration[key].append(duration)
            self.status_codes[status_code] += 1

    def record_tts_generation(
        self,
        duration: float,
        voice: str,
        success: bool = True
    ):
        """Record TTS generation metrics"""
        with self.lock:
            self.tts_total += 1
            if success:
                self.tts_success += 1
            else:
                self.tts_failure += 1

            self.tts_duration.append(duration)
            self.tts_by_voice[voice] += 1

    def record_user_session(self, username: str, action: str):
        """Record user session events"""
        with self.lock:
            if action == 'login':
                self.active_sessions.add(username)
                self.login_attempts[username] += 1
            elif action == 'logout':
                self.active_sessions.discard(username)
            elif action == 'failed_login':
                self.failed_logins[username] += 1

    def record_db_query(self, duration: float):
        """Record database query metrics"""
        with self.lock:
            self.db_query_count += 1
            self.db_query_duration.append(duration)

    def record_error(self, error_type: str):
        """Record error occurrence"""
        with self.lock:
            self.errors_by_type[error_type] += 1
            self.errors_last_hour.append(time.time())

    def record_rate_limit_hit(self, endpoint: str):
        """Record rate limit hit"""
        with self.lock:
            self.rate_limit_hits[endpoint] += 1

    def get_system_metrics(self) -> Dict:
        """Get current system resource metrics (cached)"""
        current_time = time.time()

        # Return cached metrics if still valid
        if current_time - self.last_system_update < self.cache_duration:
            return self.system_metrics_cache

        # Update metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        self.system_metrics_cache = {
            'cpu_percent': cpu_percent,
            'memory_used_mb': memory.used / (1024 * 1024),
            'memory_total_mb': memory.total / (1024 * 1024),
            'memory_percent': memory.percent,
            'disk_used_gb': disk.used / (1024 ** 3),
            'disk_total_gb': disk.total / (1024 ** 3),
            'disk_percent': disk.percent
        }

        self.last_system_update = current_time
        return self.system_metrics_cache

    def get_database_metrics(self) -> Dict:
        """Get database statistics"""
        try:
            if not os.path.exists(self.db_path):
                return {
                    'size_mb': 0,
                    'user_count': 0,
                    'audio_file_count': 0,
                    'security_event_count': 0
                }

            # Database file size
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)

            # Query counts
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM audio_files")
            audio_count = cursor.fetchone()[0]

            # Check if security_events table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='security_events'"
            )
            has_security_events = cursor.fetchone() is not None

            if has_security_events:
                cursor.execute("SELECT COUNT(*) FROM security_events")
                security_count = cursor.fetchone()[0]
            else:
                security_count = 0

            conn.close()

            return {
                'size_mb': size_mb,
                'user_count': user_count,
                'audio_file_count': audio_count,
                'security_event_count': security_count
            }
        except Exception as e:
            return {
                'size_mb': 0,
                'user_count': 0,
                'audio_file_count': 0,
                'security_event_count': 0,
                'error': str(e)
            }

    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time

    def get_error_rate(self) -> float:
        """Get error rate in last hour"""
        with self.lock:
            one_hour_ago = time.time() - 3600
            recent_errors = [t for t in self.errors_last_hour if t > one_hour_ago]

            # Clear old errors
            while self.errors_last_hour and self.errors_last_hour[0] < one_hour_ago:
                self.errors_last_hour.popleft()

            return len(recent_errors)

    def calculate_percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        # Application info
        lines.append("# HELP voiceverse_info Application information")
        lines.append("# TYPE voiceverse_info gauge")
        lines.append(f'voiceverse_info{{version="1.0.0"}} 1')

        # Uptime
        uptime = self.get_uptime()
        lines.append("\n# HELP voiceverse_uptime_seconds Application uptime in seconds")
        lines.append("# TYPE voiceverse_uptime_seconds counter")
        lines.append(f"voiceverse_uptime_seconds {uptime:.2f}")

        # HTTP requests
        lines.append("\n# HELP voiceverse_http_requests_total Total HTTP requests")
        lines.append("# TYPE voiceverse_http_requests_total counter")
        with self.lock:
            for key, count in self.request_count.items():
                method, endpoint = key.split('_', 1)
                lines.append(
                    f'voiceverse_http_requests_total{{method="{method}",endpoint="{endpoint}"}} {count}'
                )

        # HTTP status codes
        lines.append("\n# HELP voiceverse_http_status_total HTTP responses by status code")
        lines.append("# TYPE voiceverse_http_status_total counter")
        with self.lock:
            for status_code, count in self.status_codes.items():
                lines.append(f'voiceverse_http_status_total{{code="{status_code}"}} {count}')

        # Request duration
        lines.append("\n# HELP voiceverse_http_duration_seconds HTTP request duration")
        lines.append("# TYPE voiceverse_http_duration_seconds summary")
        with self.lock:
            for key, durations in self.request_duration.items():
                if durations:
                    method, endpoint = key.split('_', 1)
                    p50 = self.calculate_percentile(durations, 50)
                    p95 = self.calculate_percentile(durations, 95)
                    p99 = self.calculate_percentile(durations, 99)

                    lines.append(
                        f'voiceverse_http_duration_seconds{{method="{method}",endpoint="{endpoint}",quantile="0.5"}} {p50:.4f}'
                    )
                    lines.append(
                        f'voiceverse_http_duration_seconds{{method="{method}",endpoint="{endpoint}",quantile="0.95"}} {p95:.4f}'
                    )
                    lines.append(
                        f'voiceverse_http_duration_seconds{{method="{method}",endpoint="{endpoint}",quantile="0.99"}} {p99:.4f}'
                    )

        # TTS metrics
        lines.append("\n# HELP voiceverse_tts_total Total TTS generations")
        lines.append("# TYPE voiceverse_tts_total counter")
        lines.append(f"voiceverse_tts_total {self.tts_total}")

        lines.append("\n# HELP voiceverse_tts_success_total Successful TTS generations")
        lines.append("# TYPE voiceverse_tts_success_total counter")
        lines.append(f"voiceverse_tts_success_total {self.tts_success}")

        lines.append("\n# HELP voiceverse_tts_failure_total Failed TTS generations")
        lines.append("# TYPE voiceverse_tts_failure_total counter")
        lines.append(f"voiceverse_tts_failure_total {self.tts_failure}")

        # TTS by voice
        lines.append("\n# HELP voiceverse_tts_by_voice_total TTS generations by voice")
        lines.append("# TYPE voiceverse_tts_by_voice_total counter")
        with self.lock:
            for voice, count in self.tts_by_voice.items():
                lines.append(f'voiceverse_tts_by_voice_total{{voice="{voice}"}} {count}')

        # TTS duration
        if self.tts_duration:
            lines.append("\n# HELP voiceverse_tts_duration_seconds TTS generation duration")
            lines.append("# TYPE voiceverse_tts_duration_seconds summary")
            p50 = self.calculate_percentile(list(self.tts_duration), 50)
            p95 = self.calculate_percentile(list(self.tts_duration), 95)
            p99 = self.calculate_percentile(list(self.tts_duration), 99)

            lines.append(f'voiceverse_tts_duration_seconds{{quantile="0.5"}} {p50:.4f}')
            lines.append(f'voiceverse_tts_duration_seconds{{quantile="0.95"}} {p95:.4f}')
            lines.append(f'voiceverse_tts_duration_seconds{{quantile="0.99"}} {p99:.4f}')

        # User metrics
        lines.append("\n# HELP voiceverse_active_sessions Active user sessions")
        lines.append("# TYPE voiceverse_active_sessions gauge")
        lines.append(f"voiceverse_active_sessions {len(self.active_sessions)}")

        lines.append("\n# HELP voiceverse_login_attempts_total Total login attempts")
        lines.append("# TYPE voiceverse_login_attempts_total counter")
        with self.lock:
            total_logins = sum(self.login_attempts.values())
        lines.append(f"voiceverse_login_attempts_total {total_logins}")

        lines.append("\n# HELP voiceverse_failed_logins_total Failed login attempts")
        lines.append("# TYPE voiceverse_failed_logins_total counter")
        with self.lock:
            total_failed = sum(self.failed_logins.values())
        lines.append(f"voiceverse_failed_logins_total {total_failed}")

        # Database metrics
        lines.append("\n# HELP voiceverse_db_queries_total Total database queries")
        lines.append("# TYPE voiceverse_db_queries_total counter")
        lines.append(f"voiceverse_db_queries_total {self.db_query_count}")

        if self.db_query_duration:
            lines.append("\n# HELP voiceverse_db_query_duration_seconds Database query duration")
            lines.append("# TYPE voiceverse_db_query_duration_seconds summary")
            p50 = self.calculate_percentile(list(self.db_query_duration), 50)
            p95 = self.calculate_percentile(list(self.db_query_duration), 95)
            p99 = self.calculate_percentile(list(self.db_query_duration), 99)

            lines.append(f'voiceverse_db_query_duration_seconds{{quantile="0.5"}} {p50:.4f}')
            lines.append(f'voiceverse_db_query_duration_seconds{{quantile="0.95"}} {p95:.4f}')
            lines.append(f'voiceverse_db_query_duration_seconds{{quantile="0.99"}} {p99:.4f}')

        # Database statistics
        db_metrics = self.get_database_metrics()
        lines.append("\n# HELP voiceverse_db_size_mb Database file size in MB")
        lines.append("# TYPE voiceverse_db_size_mb gauge")
        lines.append(f"voiceverse_db_size_mb {db_metrics['size_mb']:.2f}")

        lines.append("\n# HELP voiceverse_users_total Total registered users")
        lines.append("# TYPE voiceverse_users_total gauge")
        lines.append(f"voiceverse_users_total {db_metrics['user_count']}")

        lines.append("\n# HELP voiceverse_audio_files_total Total audio files")
        lines.append("# TYPE voiceverse_audio_files_total gauge")
        lines.append(f"voiceverse_audio_files_total {db_metrics['audio_file_count']}")

        # Error metrics
        lines.append("\n# HELP voiceverse_errors_total Total errors by type")
        lines.append("# TYPE voiceverse_errors_total counter")
        with self.lock:
            for error_type, count in self.errors_by_type.items():
                lines.append(f'voiceverse_errors_total{{type="{error_type}"}} {count}')

        error_rate = self.get_error_rate()
        lines.append("\n# HELP voiceverse_errors_last_hour Errors in last hour")
        lines.append("# TYPE voiceverse_errors_last_hour gauge")
        lines.append(f"voiceverse_errors_last_hour {error_rate}")

        # Rate limit metrics
        lines.append("\n# HELP voiceverse_rate_limit_hits_total Rate limit hits")
        lines.append("# TYPE voiceverse_rate_limit_hits_total counter")
        with self.lock:
            for endpoint, count in self.rate_limit_hits.items():
                lines.append(f'voiceverse_rate_limit_hits_total{{endpoint="{endpoint}"}} {count}')

        # System metrics
        system = self.get_system_metrics()

        lines.append("\n# HELP voiceverse_cpu_percent CPU usage percentage")
        lines.append("# TYPE voiceverse_cpu_percent gauge")
        lines.append(f"voiceverse_cpu_percent {system['cpu_percent']:.2f}")

        lines.append("\n# HELP voiceverse_memory_used_mb Memory used in MB")
        lines.append("# TYPE voiceverse_memory_used_mb gauge")
        lines.append(f"voiceverse_memory_used_mb {system['memory_used_mb']:.2f}")

        lines.append("\n# HELP voiceverse_memory_percent Memory usage percentage")
        lines.append("# TYPE voiceverse_memory_percent gauge")
        lines.append(f"voiceverse_memory_percent {system['memory_percent']:.2f}")

        lines.append("\n# HELP voiceverse_disk_used_gb Disk used in GB")
        lines.append("# TYPE voiceverse_disk_used_gb gauge")
        lines.append(f"voiceverse_disk_used_gb {system['disk_used_gb']:.2f}")

        lines.append("\n# HELP voiceverse_disk_percent Disk usage percentage")
        lines.append("# TYPE voiceverse_disk_percent gauge")
        lines.append(f"voiceverse_disk_percent {system['disk_percent']:.2f}")

        return '\n'.join(lines) + '\n'

    def export_json(self) -> Dict:
        """Export metrics as JSON"""
        system = self.get_system_metrics()
        db_metrics = self.get_database_metrics()

        with self.lock:
            return {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'uptime_seconds': self.get_uptime(),
                'http': {
                    'total_requests': sum(self.request_count.values()),
                    'requests_by_endpoint': dict(self.request_count),
                    'status_codes': dict(self.status_codes)
                },
                'tts': {
                    'total': self.tts_total,
                    'success': self.tts_success,
                    'failure': self.tts_failure,
                    'by_voice': dict(self.tts_by_voice)
                },
                'users': {
                    'active_sessions': len(self.active_sessions),
                    'total_logins': sum(self.login_attempts.values()),
                    'failed_logins': sum(self.failed_logins.values())
                },
                'database': {
                    'query_count': self.db_query_count,
                    'size_mb': db_metrics['size_mb'],
                    'user_count': db_metrics['user_count'],
                    'audio_file_count': db_metrics['audio_file_count']
                },
                'errors': {
                    'by_type': dict(self.errors_by_type),
                    'last_hour': self.get_error_rate()
                },
                'system': system
            }


# Global metrics instance
_metrics_instance = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
