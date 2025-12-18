"""
Simple Email Alert System
Sends security alerts via SMTP (Gmail, Office365, etc.) for login anomalies.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
import logging


class SimpleAlerts:
    """
    Manages email alerts for security events.

    Uses SMTP (Gmail, Office365, or other providers) for sending alerts.
    Privacy-focused: Never sends raw IPs, only hashes.
    """

    def __init__(
        self,
        smtp_email: Optional[str] = None,
        smtp_password: Optional[str] = None,
        alert_recipient: Optional[str] = None
    ):
        """
        Initialize the email alert system.

        Args:
            smtp_email: Email address for sending (or from env SMTP_EMAIL)
            smtp_password: Email password or App Password (or from env SMTP_PASSWORD)
            alert_recipient: Email to receive alerts (or from env ALERT_EMAIL)
        """
        self.smtp_email = smtp_email or os.getenv('SMTP_EMAIL')
        self.smtp_password = smtp_password or os.getenv('SMTP_PASSWORD')
        self.alert_recipient = alert_recipient or os.getenv('ALERT_EMAIL')

        # SMTP configuration (supports Gmail, Office365, and other providers)
        self.smtp_server = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

        # Validate configuration
        if not all([self.smtp_email, self.smtp_password, self.alert_recipient]):
            logging.warning(
                "Email alerts not fully configured. "
                "Set SMTP_EMAIL, SMTP_PASSWORD, and ALERT_EMAIL in .env"
            )
            self.enabled = False
        else:
            self.enabled = True

    def send_lockout_alert(
        self,
        identifier_hash: str,
        attempt_count: int,
        lockout_duration: int,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send email alert when account is locked due to failed attempts.

        Args:
            identifier_hash: Hashed identifier (IP or username)
            attempt_count: Number of failed attempts
            lockout_duration: Lockout duration in seconds
            timestamp: When the lockout occurred (default: now)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.enabled:
            logging.warning("Email alerts not enabled - skipping alert")
            return False

        timestamp = timestamp or datetime.utcnow()

        # Create email content
        subject = "🔒 VoiceVerse Security Alert: Account Locked"

        body = f"""
Security Alert: Account Lockout Triggered

A user account has been locked due to multiple failed login attempts.

Details:
---------
Identifier (Hashed): {identifier_hash}
Failed Attempts: {attempt_count}
Lockout Duration: {lockout_duration} seconds
Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
Auto-Unlock: {lockout_duration} seconds from lockout time

Action Required:
---------
This is an automated security response. The account will automatically
unlock after {lockout_duration} seconds.

If you recognize this activity, no action is needed. The lockout is a
normal security measure protecting against brute-force attacks.

If this activity is suspicious, consider:
1. Reviewing security logs
2. Checking for unusual patterns
3. Updating security rules if needed

Privacy Notice:
---------
For privacy protection, IP addresses are hashed using SHA256 with salt.
Raw IP addresses are never stored or transmitted in alerts.

---
VoiceVerse Automated Security System
This is an automated message. Do not reply to this email.
"""

        return self._send_email(subject, body)

    def send_test_alert(self) -> bool:
        """
        Send a test email to verify configuration.

        Returns:
            bool: True if test email sent successfully
        """
        if not self.enabled:
            logging.error("Email alerts not configured")
            return False

        subject = "✅ VoiceVerse Email Alerts - Test Message"

        body = f"""
Email Alert System Test

This is a test message to verify your email alert configuration.

Configuration:
---------
SMTP Server: {self.smtp_server}:{self.smtp_port}
Sender Email: {self.smtp_email}
Recipient Email: {self.alert_recipient}
Status: CONFIGURED ✓

If you received this email, your alert system is working correctly!

Next Steps:
---------
1. Confirm you received this message
2. Check that it's not in spam folder
3. Add {self.smtp_email} to your contacts
4. Your security alerts are now active

---
VoiceVerse Email Alert System
Test sent at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

        return self._send_email(subject, body)

    def _send_email(self, subject: str, body: str) -> bool:
        """
        Internal method to send email via SMTP.

        Args:
            subject: Email subject line
            body: Email body content

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = self.smtp_email
            message['To'] = self.alert_recipient
            message['Subject'] = subject

            # Attach body
            message.attach(MIMEText(body, 'plain'))

            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(self.smtp_email, self.smtp_password)

                # Send email
                server.send_message(message)

            logging.info(f"Alert email sent successfully to {self.alert_recipient}")
            return True

        except smtplib.SMTPAuthenticationError:
            logging.error(
                f"SMTP authentication failed. Check your email credentials. "
                f"Server: {self.smtp_server}:{self.smtp_port}"
            )
            return False

        except smtplib.SMTPException as e:
            logging.error(f"SMTP error sending alert email: {e}")
            return False

        except Exception as e:
            logging.error(f"Unexpected error sending alert email: {e}")
            return False

    def is_configured(self) -> bool:
        """
        Check if email alerts are properly configured.

        Returns:
            bool: True if configuration is complete
        """
        return self.enabled

    def get_configuration_status(self) -> dict:
        """
        Get detailed configuration status for debugging.

        Returns:
            dict: Configuration details
        """
        return {
            'enabled': self.enabled,
            'smtp_email': self.smtp_email if self.smtp_email else 'NOT SET',
            'smtp_password': '***' if self.smtp_password else 'NOT SET',
            'alert_recipient': self.alert_recipient if self.alert_recipient else 'NOT SET',
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port
        }


# Example usage and testing
if __name__ == '__main__':
    """
    Test the email alert system.

    Usage:
        python3 simple_alerts.py

    Make sure to set these in your .env file:
        SMTP_EMAIL=your-gmail@gmail.com
        SMTP_PASSWORD=your-app-password
        ALERT_EMAIL=recipient@example.com
    """
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("VoiceVerse Email Alert System Test")
    print("=" * 60)

    # Initialize alert system
    alerts = SimpleAlerts()

    # Check configuration
    print("\nConfiguration Status:")
    print("-" * 60)
    config = alerts.get_configuration_status()
    for key, value in config.items():
        print(f"{key:20s}: {value}")

    if not alerts.is_configured():
        print("\n❌ Email alerts not configured!")
        print("\nTo configure, add to your .env file:")
        print("  SMTP_EMAIL=your-gmail@gmail.com")
        print("  SMTP_PASSWORD=your-gmail-app-password")
        print("  ALERT_EMAIL=recipient@example.com")
        print("\nGet Gmail App Password:")
        print("  https://myaccount.google.com/apppasswords")
        sys.exit(1)

    print("\n✓ Configuration complete!")

    # Send test email
    print("\n" + "=" * 60)
    print("Sending test email...")
    print("=" * 60)

    success = alerts.send_test_alert()

    if success:
        print("\n✅ Test email sent successfully!")
        print(f"Check {alerts.alert_recipient} for the message.")
    else:
        print("\n❌ Failed to send test email.")
        print("Check the error messages above for details.")
        sys.exit(1)

    # Test lockout alert
    print("\n" + "=" * 60)
    print("Testing lockout alert...")
    print("=" * 60)

    success = alerts.send_lockout_alert(
        identifier_hash="a1b2c3d4e5f6...",
        attempt_count=10,
        lockout_duration=60
    )

    if success:
        print("\n✅ Lockout alert sent successfully!")
        print("Check your email for the security alert.")
    else:
        print("\n❌ Failed to send lockout alert.")

    print("\n" + "=" * 60)
    print("Email alert system test complete!")
    print("=" * 60)
