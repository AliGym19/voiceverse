#!/usr/bin/env python3
"""
VoiceVerse Alerting System
Monitors metrics and logs, triggers alerts when thresholds are exceeded

Usage:
    from monitoring.alerting_system import AlertingSystem

    alerts = AlertingSystem()

    # Define alert rules
    alerts.add_rule('high_cpu', metric='cpu_percent', threshold=90, severity='warning')
    alerts.add_rule('disk_full', metric='disk_percent', threshold=95, severity='critical')

    # Check for alerts
    triggered_alerts = alerts.check_all_rules()

    # Send notifications
    alerts.send_notifications(triggered_alerts)
"""

import os
import json
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from monitoring.metrics_collector import get_metrics_collector
from monitoring.log_analyzer import LogAnalyzer
from pathlib import Path


class AlertRule:
    """Represents an alert rule"""

    def __init__(
        self,
        name: str,
        metric: str,
        threshold: float,
        operator: str = '>',
        severity: str = 'warning',
        description: str = '',
        cooldown_minutes: int = 60
    ):
        self.name = name
        self.metric = metric
        self.threshold = threshold
        self.operator = operator
        self.severity = severity
        self.description = description or f"{metric} {operator} {threshold}"
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered = None

    def check(self, value: float) -> bool:
        """Check if the rule is triggered"""
        # Check cooldown
        if self.last_triggered:
            time_since = datetime.now() - self.last_triggered
            if time_since.total_seconds() < (self.cooldown_minutes * 60):
                return False

        # Evaluate condition
        if self.operator == '>':
            return value > self.threshold
        elif self.operator == '<':
            return value < self.threshold
        elif self.operator == '>=':
            return value >= self.threshold
        elif self.operator == '<=':
            return value <= self.threshold
        elif self.operator == '==':
            return value == self.threshold
        else:
            return False

    def trigger(self):
        """Mark rule as triggered"""
        self.last_triggered = datetime.now()


class AlertingSystem:
    """Manages alert rules and notifications"""

    def __init__(self, config_file: Optional[str] = None):
        self.rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict] = []
        self.config_file = config_file or 'monitoring/alert_config.json'

        # Email configuration
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', '')

        # Slack webhook (optional)
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')

        # Load default rules
        self._load_default_rules()

        # Try to load custom rules from config file
        if os.path.exists(self.config_file):
            self.load_rules_from_file(self.config_file)

    def _load_default_rules(self):
        """Load default alert rules"""
        # System resource alerts
        self.add_rule(
            name='high_cpu_usage',
            metric='cpu_percent',
            threshold=90,
            operator='>',
            severity='warning',
            description='CPU usage above 90%'
        )

        self.add_rule(
            name='critical_cpu_usage',
            metric='cpu_percent',
            threshold=95,
            operator='>',
            severity='critical',
            description='CPU usage above 95%'
        )

        self.add_rule(
            name='high_memory_usage',
            metric='memory_percent',
            threshold=85,
            operator='>',
            severity='warning',
            description='Memory usage above 85%'
        )

        self.add_rule(
            name='critical_memory_usage',
            metric='memory_percent',
            threshold=95,
            operator='>',
            severity='critical',
            description='Memory usage above 95%'
        )

        self.add_rule(
            name='disk_almost_full',
            metric='disk_percent',
            threshold=90,
            operator='>',
            severity='warning',
            description='Disk usage above 90%'
        )

        self.add_rule(
            name='disk_critical',
            metric='disk_percent',
            threshold=95,
            operator='>',
            severity='critical',
            description='Disk usage above 95%'
        )

        # Application alerts
        self.add_rule(
            name='high_error_rate',
            metric='error_rate_per_hour',
            threshold=100,
            operator='>',
            severity='warning',
            description='More than 100 errors per hour'
        )

        self.add_rule(
            name='tts_failure_rate',
            metric='tts_failure_rate',
            threshold=5,
            operator='>',
            severity='warning',
            description='TTS failure rate above 5%'
        )

        self.add_rule(
            name='high_failed_logins',
            metric='failed_logins',
            threshold=50,
            operator='>',
            severity='warning',
            description='More than 50 failed logins'
        )

        self.add_rule(
            name='brute_force_detected',
            metric='brute_force_attempts',
            threshold=0,
            operator='>',
            severity='critical',
            description='Brute force attack attempts detected',
            cooldown_minutes=30
        )

    def add_rule(
        self,
        name: str,
        metric: str,
        threshold: float,
        operator: str = '>',
        severity: str = 'warning',
        description: str = '',
        cooldown_minutes: int = 60
    ):
        """Add an alert rule"""
        self.rules[name] = AlertRule(
            name=name,
            metric=metric,
            threshold=threshold,
            operator=operator,
            severity=severity,
            description=description,
            cooldown_minutes=cooldown_minutes
        )

    def remove_rule(self, name: str):
        """Remove an alert rule"""
        if name in self.rules:
            del self.rules[name]

    def get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current value of a metric"""
        try:
            metrics = get_metrics_collector()
            metrics_data = metrics.export_json()

            # System metrics
            if metric_name == 'cpu_percent':
                return metrics_data['system']['cpu_percent']
            elif metric_name == 'memory_percent':
                return metrics_data['system']['memory_percent']
            elif metric_name == 'disk_percent':
                return metrics_data['system']['disk_percent']

            # Error metrics
            elif metric_name == 'error_rate_per_hour':
                return metrics_data['errors']['last_hour']

            # TTS metrics
            elif metric_name == 'tts_failure_rate':
                total = metrics_data['tts']['total']
                failures = metrics_data['tts']['failure']
                return (failures / total * 100) if total > 0 else 0

            # User metrics
            elif metric_name == 'failed_logins':
                return metrics_data['users']['failed_logins']

            # Security metrics (from log analyzer)
            elif metric_name == 'brute_force_attempts':
                analyzer = LogAnalyzer()
                analysis = analyzer.analyze_security_logs(hours=1)
                return len(analysis.get('brute_force_attempts', []))

            return None
        except Exception as e:
            print(f"Error getting metric {metric_name}: {e}")
            return None

    def check_all_rules(self) -> List[Dict]:
        """Check all rules and return triggered alerts"""
        triggered_alerts = []

        for rule_name, rule in self.rules.items():
            value = self.get_metric_value(rule.metric)

            if value is not None and rule.check(value):
                alert = {
                    'rule_name': rule.name,
                    'metric': rule.metric,
                    'current_value': value,
                    'threshold': rule.threshold,
                    'operator': rule.operator,
                    'severity': rule.severity,
                    'description': rule.description,
                    'timestamp': datetime.now().isoformat()
                }

                triggered_alerts.append(alert)
                rule.trigger()

                # Add to history
                self.alert_history.append(alert)

                # Keep only last 1000 alerts
                if len(self.alert_history) > 1000:
                    self.alert_history = self.alert_history[-1000:]

        return triggered_alerts

    def send_email_alert(self, alerts: List[Dict]) -> bool:
        """Send email notification for alerts"""
        if not self.smtp_user or not self.alert_email:
            print("Email not configured, skipping email alert")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"VoiceVerse Alert: {len(alerts)} issue(s) detected"
            msg['From'] = self.smtp_user
            msg['To'] = self.alert_email

            # Create HTML content
            html = self._generate_alert_email_html(alerts)

            msg.attach(MIMEText(html, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"Alert email sent successfully to {self.alert_email}")
            return True
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False

    def _generate_alert_email_html(self, alerts: List[Dict]) -> str:
        """Generate HTML email content for alerts"""
        severity_colors = {
            'critical': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }

        html = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #667eea; color: white; padding: 20px; border-radius: 5px; }
        .alert-box { margin: 15px 0; padding: 15px; border-left: 4px solid; border-radius: 5px; }
        .critical { background: #fee; border-color: #dc3545; }
        .warning { background: #fff4e5; border-color: #ffc107; }
        .info { background: #e7f3ff; border-color: #17a2b8; }
        .metric { font-weight: bold; font-size: 18px; }
        .details { color: #666; font-size: 14px; margin-top: 5px; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🚨 VoiceVerse Alert</h2>
            <p>Detected ''' + str(len(alerts)) + ''' issue(s)</p>
        </div>
        '''

        for alert in alerts:
            severity_class = alert['severity']
            html += f'''
        <div class="alert-box {severity_class}">
            <div class="metric">{alert['description']}</div>
            <div class="details">
                Current value: {alert['current_value']:.2f} {alert['operator']} {alert['threshold']}<br>
                Severity: {alert['severity'].upper()}<br>
                Time: {alert['timestamp']}
            </div>
        </div>
            '''

        html += '''
        <div class="footer">
            <p>This is an automated alert from VoiceVerse monitoring system.</p>
            <p>Please review the metrics dashboard for more details.</p>
        </div>
    </div>
</body>
</html>
        '''

        return html

    def send_slack_alert(self, alerts: List[Dict]) -> bool:
        """Send Slack notification for alerts"""
        if not self.slack_webhook:
            print("Slack webhook not configured, skipping Slack alert")
            return False

        try:
            import requests

            # Build message
            text = f"🚨 *VoiceVerse Alert*\nDetected {len(alerts)} issue(s):\n\n"

            for alert in alerts:
                emoji = '🔴' if alert['severity'] == 'critical' else '⚠️'
                text += f"{emoji} *{alert['description']}*\n"
                text += f"   Current: {alert['current_value']:.2f} | Threshold: {alert['threshold']}\n\n"

            payload = {
                'text': text,
                'username': 'VoiceVerse Monitor'
            }

            response = requests.post(self.slack_webhook, json=payload)

            if response.status_code == 200:
                print("Slack alert sent successfully")
                return True
            else:
                print(f"Failed to send Slack alert: {response.status_code}")
                return False
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            return False

    def send_notifications(self, alerts: List[Dict]):
        """Send all configured notifications for alerts"""
        if not alerts:
            return

        print(f"\n⚠️  Sending notifications for {len(alerts)} alert(s)...")

        # Send email
        self.send_email_alert(alerts)

        # Send Slack
        self.send_slack_alert(alerts)

        # Log to console
        for alert in alerts:
            severity_icon = '🔴' if alert['severity'] == 'critical' else '⚠️'
            print(f"{severity_icon} {alert['description']} | Value: {alert['current_value']:.2f}")

    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Get alert history for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)

        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) >= cutoff
        ]

    def save_rules_to_file(self, filename: Optional[str] = None):
        """Save current rules to JSON file"""
        if filename is None:
            filename = self.config_file

        rules_data = {
            rule_name: {
                'name': rule.name,
                'metric': rule.metric,
                'threshold': rule.threshold,
                'operator': rule.operator,
                'severity': rule.severity,
                'description': rule.description,
                'cooldown_minutes': rule.cooldown_minutes
            }
            for rule_name, rule in self.rules.items()
        }

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(rules_data, f, indent=2)

        print(f"Alert rules saved to {filename}")

    def load_rules_from_file(self, filename: str):
        """Load rules from JSON file"""
        try:
            with open(filename, 'r') as f:
                rules_data = json.load(f)

            for rule_name, rule_config in rules_data.items():
                self.add_rule(**rule_config)

            print(f"Loaded {len(rules_data)} alert rules from {filename}")
        except Exception as e:
            print(f"Failed to load rules from {filename}: {e}")

    def get_status(self) -> Dict:
        """Get alerting system status"""
        return {
            'total_rules': len(self.rules),
            'active_rules': [
                {
                    'name': rule.name,
                    'metric': rule.metric,
                    'threshold': rule.threshold,
                    'severity': rule.severity
                }
                for rule in self.rules.values()
            ],
            'alerts_last_24h': len(self.get_alert_history(hours=24)),
            'email_configured': bool(self.smtp_user and self.alert_email),
            'slack_configured': bool(self.slack_webhook)
        }


def run_continuous_monitoring(check_interval_seconds: int = 300):
    """
    Run continuous monitoring loop
    Check rules every N seconds and send alerts
    """
    print(f"Starting continuous monitoring (check interval: {check_interval_seconds}s)")

    alerts_system = AlertingSystem()

    while True:
        try:
            triggered_alerts = alerts_system.check_all_rules()

            if triggered_alerts:
                alerts_system.send_notifications(triggered_alerts)

            # Wait for next check
            time.sleep(check_interval_seconds)
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(check_interval_seconds)


def main():
    """CLI interface for alerting system"""
    import argparse

    parser = argparse.ArgumentParser(description='VoiceVerse Alerting System')
    parser.add_argument(
        'command',
        choices=['check', 'monitor', 'status', 'history'],
        help='Command to execute'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Monitoring check interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Hours of history to show (default: 24)'
    )

    args = parser.parse_args()

    alerts = AlertingSystem()

    if args.command == 'check':
        print("Checking all alert rules...")
        triggered = alerts.check_all_rules()

        if triggered:
            print(f"\n⚠️  {len(triggered)} alert(s) triggered:\n")
            for alert in triggered:
                print(f"  • {alert['description']}")
                print(f"    Value: {alert['current_value']:.2f} (threshold: {alert['threshold']})")
                print(f"    Severity: {alert['severity'].upper()}\n")

            alerts.send_notifications(triggered)
        else:
            print("✓ All checks passed, no alerts triggered")

    elif args.command == 'monitor':
        run_continuous_monitoring(check_interval_seconds=args.interval)

    elif args.command == 'status':
        status = alerts.get_status()
        print("\n" + "=" * 60)
        print("Alerting System Status")
        print("=" * 60 + "\n")
        print(f"Total Rules: {status['total_rules']}")
        print(f"Alerts (24h): {status['alerts_last_24h']}")
        print(f"Email Configured: {'✓' if status['email_configured'] else '✗'}")
        print(f"Slack Configured: {'✓' if status['slack_configured'] else '✗'}")

        print("\nActive Rules:")
        for rule in status['active_rules']:
            print(f"  • {rule['name']}: {rule['metric']} (threshold: {rule['threshold']})")

        print("\n" + "=" * 60 + "\n")

    elif args.command == 'history':
        history = alerts.get_alert_history(hours=args.hours)

        print(f"\nAlert History (last {args.hours} hours):")
        print("=" * 60 + "\n")

        if history:
            for alert in history:
                print(f"{alert['timestamp']}")
                print(f"  {alert['description']}")
                print(f"  Value: {alert['current_value']:.2f} | Severity: {alert['severity'].upper()}\n")
        else:
            print("No alerts in the specified time period.")

        print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
