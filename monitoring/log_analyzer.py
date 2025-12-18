#!/usr/bin/env python3
"""
VoiceVerse Log Analyzer
Analyzes security and application logs for patterns, anomalies, and threats

Usage:
    from monitoring.log_analyzer import LogAnalyzer

    analyzer = LogAnalyzer()

    # Analyze security logs
    threats = analyzer.analyze_security_logs(hours=24)

    # Detect anomalies
    anomalies = analyzer.detect_anomalies()

    # Get summary report
    report = analyzer.generate_report()
"""

import os
import re
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter


class LogAnalyzer:
    """Analyzes application and security logs"""

    def __init__(
        self,
        security_log_path: str = 'logs/security_audit.log',
        app_log_path: str = 'logs/application.log',
        error_log_path: str = 'logs/errors.log',
        db_path: str = 'voiceverse.db'
    ):
        self.security_log_path = security_log_path
        self.app_log_path = app_log_path
        self.error_log_path = error_log_path
        self.db_path = db_path

        # Patterns for log parsing
        self.security_pattern = re.compile(
            r'\[(.*?)\] \[(.*?)\] (.*?) - User: (.*?), IP: (.*?)(?:, Details: (.*))?$'
        )

        # Threat indicators
        self.threat_patterns = [
            r'SQL.*injection',
            r'<script>',
            r'\.\./',
            r'union.*select',
            r'cmd\.exe',
            r'/etc/passwd',
            r'base64_decode',
            r'eval\(',
        ]

        # Known attack IP patterns (simple examples)
        self.known_bad_ips = set()

    def parse_security_log_line(self, line: str) -> Optional[Dict]:
        """Parse a single security log line"""
        match = self.security_pattern.match(line.strip())
        if not match:
            return None

        timestamp_str, level, event_type, username, ip, details = match.groups()

        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

        return {
            'timestamp': timestamp,
            'level': level,
            'event_type': event_type,
            'username': username,
            'ip': ip,
            'details': details or ''
        }

    def read_log_file(self, log_path: str, hours: Optional[int] = None) -> List[Dict]:
        """Read and parse log file"""
        if not os.path.exists(log_path):
            return []

        cutoff_time = None
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)

        entries = []
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    entry = self.parse_security_log_line(line)
                    if entry:
                        if cutoff_time is None or entry['timestamp'] >= cutoff_time:
                            entries.append(entry)
        except Exception as e:
            print(f"Error reading log file {log_path}: {e}")

        return entries

    def analyze_security_logs(self, hours: int = 24) -> Dict:
        """Analyze security logs for threats and patterns"""
        entries = self.read_log_file(self.security_log_path, hours)

        if not entries:
            return {
                'total_events': 0,
                'threats_detected': [],
                'failed_logins': [],
                'brute_force_attempts': [],
                'suspicious_ips': [],
                'event_summary': {}
            }

        # Count events by type
        event_counts = Counter(e['event_type'] for e in entries)

        # Find failed logins
        failed_logins = [
            e for e in entries
            if e['event_type'] in ['AUTH_FAILURE', 'LOGIN_FAILED']
        ]

        # Detect brute force attempts (multiple failed logins from same IP)
        failed_by_ip = defaultdict(list)
        for event in failed_logins:
            failed_by_ip[event['ip']].append(event)

        brute_force_attempts = [
            {
                'ip': ip,
                'attempts': len(events),
                'usernames': list(set(e['username'] for e in events)),
                'first_attempt': min(e['timestamp'] for e in events),
                'last_attempt': max(e['timestamp'] for e in events)
            }
            for ip, events in failed_by_ip.items()
            if len(events) >= 5
        ]

        # Detect threats based on patterns
        threats = []
        for entry in entries:
            details = entry.get('details', '')
            for pattern in self.threat_patterns:
                if re.search(pattern, details, re.IGNORECASE):
                    threats.append({
                        'timestamp': entry['timestamp'],
                        'ip': entry['ip'],
                        'username': entry['username'],
                        'event_type': entry['event_type'],
                        'threat_pattern': pattern,
                        'details': details
                    })
                    break

        # Find suspicious IPs (multiple different attack types)
        ip_events = defaultdict(set)
        for entry in entries:
            if entry['level'] in ['WARNING', 'ERROR', 'CRITICAL']:
                ip_events[entry['ip']].add(entry['event_type'])

        suspicious_ips = [
            {
                'ip': ip,
                'event_types': list(event_types),
                'event_count': len(event_types)
            }
            for ip, event_types in ip_events.items()
            if len(event_types) >= 3
        ]

        return {
            'total_events': len(entries),
            'time_range': {
                'start': min(e['timestamp'] for e in entries).isoformat(),
                'end': max(e['timestamp'] for e in entries).isoformat()
            },
            'event_summary': dict(event_counts),
            'threats_detected': threats,
            'failed_logins': {
                'total': len(failed_logins),
                'recent': [
                    {
                        'timestamp': e['timestamp'].isoformat(),
                        'ip': e['ip'],
                        'username': e['username']
                    }
                    for e in sorted(failed_logins, key=lambda x: x['timestamp'], reverse=True)[:10]
                ]
            },
            'brute_force_attempts': brute_force_attempts,
            'suspicious_ips': suspicious_ips
        }

    def detect_anomalies(self, hours: int = 24) -> Dict:
        """Detect anomalous behavior patterns"""
        entries = self.read_log_file(self.security_log_path, hours)

        if not entries:
            return {
                'anomalies': [],
                'summary': 'No log entries found'
            }

        anomalies = []

        # Anomaly 1: Rapid successive requests from single IP
        requests_by_ip = defaultdict(list)
        for entry in entries:
            requests_by_ip[entry['ip']].append(entry['timestamp'])

        for ip, timestamps in requests_by_ip.items():
            if len(timestamps) >= 100:
                # Check if requests are very rapid
                sorted_times = sorted(timestamps)
                intervals = [
                    (sorted_times[i+1] - sorted_times[i]).total_seconds()
                    for i in range(len(sorted_times) - 1)
                ]
                avg_interval = sum(intervals) / len(intervals) if intervals else 0

                if avg_interval < 1.0:  # Less than 1 second average
                    anomalies.append({
                        'type': 'RAPID_REQUESTS',
                        'severity': 'HIGH',
                        'ip': ip,
                        'request_count': len(timestamps),
                        'avg_interval_seconds': avg_interval,
                        'description': f'IP {ip} made {len(timestamps)} requests with average interval of {avg_interval:.2f}s'
                    })

        # Anomaly 2: Access to multiple user accounts from single IP
        accounts_by_ip = defaultdict(set)
        for entry in entries:
            if entry['username'] != 'unknown':
                accounts_by_ip[entry['ip']].add(entry['username'])

        for ip, usernames in accounts_by_ip.items():
            if len(usernames) >= 5:
                anomalies.append({
                    'type': 'MULTIPLE_ACCOUNTS',
                    'severity': 'MEDIUM',
                    'ip': ip,
                    'account_count': len(usernames),
                    'usernames': list(usernames)[:10],
                    'description': f'IP {ip} accessed {len(usernames)} different accounts'
                })

        # Anomaly 3: After-hours activity
        after_hours_events = []
        for entry in entries:
            hour = entry['timestamp'].hour
            # Consider after-hours as 10 PM to 6 AM
            if hour >= 22 or hour < 6:
                after_hours_events.append(entry)

        if len(after_hours_events) > 50:
            anomalies.append({
                'type': 'AFTER_HOURS_ACTIVITY',
                'severity': 'LOW',
                'event_count': len(after_hours_events),
                'percentage': (len(after_hours_events) / len(entries)) * 100,
                'description': f'{len(after_hours_events)} events ({(len(after_hours_events) / len(entries)) * 100:.1f}%) occurred after hours'
            })

        # Anomaly 4: Unusual geographic patterns (would need GeoIP database in production)
        # Placeholder for now

        return {
            'anomalies': anomalies,
            'summary': f'Found {len(anomalies)} anomalies in {len(entries)} log entries'
        }

    def get_error_statistics(self, hours: int = 24) -> Dict:
        """Analyze error logs"""
        if not os.path.exists(self.error_log_path):
            return {
                'total_errors': 0,
                'errors_by_type': {},
                'recent_errors': []
            }

        cutoff_time = datetime.now() - timedelta(hours=hours)
        errors = []
        error_types = Counter()

        try:
            with open(self.error_log_path, 'r') as f:
                for line in f:
                    # Simple error parsing (customize based on your format)
                    if 'ERROR' in line or 'CRITICAL' in line:
                        errors.append(line.strip())

                        # Try to categorize error
                        if 'Database' in line or 'SQL' in line:
                            error_types['database'] += 1
                        elif 'OpenAI' in line or 'API' in line:
                            error_types['api'] += 1
                        elif 'Permission' in line or 'Access' in line:
                            error_types['permission'] += 1
                        else:
                            error_types['other'] += 1
        except Exception as e:
            print(f"Error reading error log: {e}")

        return {
            'total_errors': len(errors),
            'errors_by_type': dict(error_types),
            'recent_errors': errors[-10:] if errors else []
        }

    def get_database_events(self, hours: int = 24) -> Dict:
        """Query security events from database"""
        if not os.path.exists(self.db_path):
            return {
                'total_events': 0,
                'events_by_type': {},
                'recent_events': []
            }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if security_events table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='security_events'"
            )
            if not cursor.fetchone():
                conn.close()
                return {
                    'total_events': 0,
                    'events_by_type': {},
                    'recent_events': [],
                    'note': 'security_events table not found'
                }

            # Get events from last N hours
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat() + 'Z'

            cursor.execute(
                "SELECT COUNT(*) FROM security_events WHERE timestamp >= ?",
                (cutoff,)
            )
            total_events = cursor.fetchone()[0]

            # Events by type
            cursor.execute(
                """
                SELECT event_type, COUNT(*) as count
                FROM security_events
                WHERE timestamp >= ?
                GROUP BY event_type
                ORDER BY count DESC
                """,
                (cutoff,)
            )
            events_by_type = dict(cursor.fetchall())

            # Recent events
            cursor.execute(
                """
                SELECT timestamp, event_type, username, ip_address, details
                FROM security_events
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 20
                """,
                (cutoff,)
            )
            recent = cursor.fetchall()

            conn.close()

            return {
                'total_events': total_events,
                'events_by_type': events_by_type,
                'recent_events': [
                    {
                        'timestamp': r[0],
                        'event_type': r[1],
                        'username': r[2],
                        'ip_address': r[3],
                        'details': r[4]
                    }
                    for r in recent
                ]
            }
        except Exception as e:
            return {
                'total_events': 0,
                'events_by_type': {},
                'recent_events': [],
                'error': str(e)
            }

    def get_top_users(self, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Get most active users"""
        entries = self.read_log_file(self.security_log_path, hours)

        if not entries:
            return []

        user_activity = defaultdict(int)
        for entry in entries:
            if entry['username'] != 'unknown':
                user_activity[entry['username']] += 1

        top_users = sorted(
            [
                {'username': username, 'activity_count': count}
                for username, count in user_activity.items()
            ],
            key=lambda x: x['activity_count'],
            reverse=True
        )

        return top_users[:limit]

    def get_top_ips(self, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Get most active IP addresses"""
        entries = self.read_log_file(self.security_log_path, hours)

        if not entries:
            return []

        ip_activity = defaultdict(int)
        for entry in entries:
            ip_activity[entry['ip']] += 1

        top_ips = sorted(
            [
                {'ip': ip, 'request_count': count}
                for ip, count in ip_activity.items()
            ],
            key=lambda x: x['request_count'],
            reverse=True
        )

        return top_ips[:limit]

    def generate_report(self, hours: int = 24) -> Dict:
        """Generate comprehensive analysis report"""
        return {
            'report_generated': datetime.now().isoformat(),
            'time_window_hours': hours,
            'security_analysis': self.analyze_security_logs(hours),
            'anomaly_detection': self.detect_anomalies(hours),
            'error_statistics': self.get_error_statistics(hours),
            'database_events': self.get_database_events(hours),
            'top_users': self.get_top_users(hours),
            'top_ips': self.get_top_ips(hours)
        }

    def export_report_json(self, hours: int = 24, output_file: Optional[str] = None) -> str:
        """Export report as JSON"""
        report = self.generate_report(hours)

        json_output = json.dumps(report, indent=2, default=str)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_output)

        return json_output

    def get_security_summary(self, hours: int = 24) -> str:
        """Get human-readable security summary"""
        analysis = self.analyze_security_logs(hours)

        summary_lines = [
            "=" * 60,
            "SECURITY LOG ANALYSIS SUMMARY",
            "=" * 60,
            f"\nTime Range: Last {hours} hours",
            f"Total Events: {analysis['total_events']}",
            "\nEvent Breakdown:"
        ]

        for event_type, count in sorted(
            analysis['event_summary'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            summary_lines.append(f"  {event_type}: {count}")

        summary_lines.append(f"\nFailed Logins: {analysis['failed_logins']['total']}")
        summary_lines.append(f"Brute Force Attempts: {len(analysis['brute_force_attempts'])}")
        summary_lines.append(f"Threats Detected: {len(analysis['threats_detected'])}")
        summary_lines.append(f"Suspicious IPs: {len(analysis['suspicious_ips'])}")

        if analysis['brute_force_attempts']:
            summary_lines.append("\n⚠️  BRUTE FORCE ATTEMPTS DETECTED:")
            for attempt in analysis['brute_force_attempts'][:5]:
                summary_lines.append(
                    f"  IP: {attempt['ip']} - {attempt['attempts']} attempts - "
                    f"Targets: {', '.join(attempt['usernames'][:3])}"
                )

        if analysis['threats_detected']:
            summary_lines.append("\n⚠️  THREATS DETECTED:")
            for threat in analysis['threats_detected'][:5]:
                summary_lines.append(
                    f"  {threat['timestamp'].isoformat()} - IP: {threat['ip']} - "
                    f"Pattern: {threat['threat_pattern']}"
                )

        summary_lines.append("\n" + "=" * 60)

        return '\n'.join(summary_lines)


def main():
    """CLI interface for log analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description='VoiceVerse Log Analyzer')
    parser.add_argument(
        'command',
        choices=['analyze', 'anomalies', 'summary', 'report'],
        help='Command to execute'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to analyze (default: 24)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for JSON report'
    )

    args = parser.parse_args()

    analyzer = LogAnalyzer()

    if args.command == 'analyze':
        analysis = analyzer.analyze_security_logs(args.hours)
        print(json.dumps(analysis, indent=2, default=str))

    elif args.command == 'anomalies':
        anomalies = analyzer.detect_anomalies(args.hours)
        print(json.dumps(anomalies, indent=2, default=str))

    elif args.command == 'summary':
        print(analyzer.get_security_summary(args.hours))

    elif args.command == 'report':
        if args.output:
            analyzer.export_report_json(args.hours, args.output)
            print(f"Report saved to {args.output}")
        else:
            print(analyzer.export_report_json(args.hours))


if __name__ == '__main__':
    main()
