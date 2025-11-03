"""
Email alerter module for MongoDB PHI Masker.

This module provides an email alerting system to notify about process completion,
errors, and important events.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EmailAlerter:
    """Email alerter for sending notifications."""

    def __init__(self, config: Dict[str, Any], env: Dict[str, str]):
        """
        Initialize the email alerter.

        Args:
            config: Application configuration.
            env: Environment variables.
        """
        self.config = config
        self.env = env
        self.enabled = self._get_bool_env('EMAIL_ENABLED', False)
        
        # SMTP Configuration
        self.smtp_server = env.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(env.get('SMTP_PORT', 587))
        self.smtp_user = env.get('EMAIL_SENDER', '')
        self.smtp_password = env.get('EMAIL_PASSWORD', '')
        
        # Email Configuration
        self.sender = env.get('EMAIL_SENDER', '')
        self.recipients = self._parse_recipients(env.get('EMAIL_RECIPIENT', ''))
        
        if self.enabled:
            self._validate_email_config()
            logger.info(f"Email alerter initialized with server {self.smtp_server}:{self.smtp_port}")
        else:
            logger.info("Email alerter is disabled")

    def send_completion_alert(self, stats: Dict[str, Any], elapsed_time: float) -> bool:
        """
        Send a completion alert with processing statistics.

        Args:
            stats: Dictionary containing processing statistics.
            elapsed_time: Total processing time in seconds.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.info("Email alerts disabled, skipping completion notification")
            return False

        subject = f"[PHI Masking] Process Completed Successfully"
        
        # Format the elapsed time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Build email content
        content = f"""
        <html>
        <body>
            <h2>PHI Masking Process Completed</h2>
            <p>The PHI masking process has completed successfully.</p>
            
            <h3>Processing Statistics:</h3>
            <ul>
                <li><strong>Documents Processed:</strong> {stats.get('documents_processed', 0)}</li>
                <li><strong>Documents Masked:</strong> {stats.get('documents_masked', 0)}</li>
                <li><strong>Documents Skipped:</strong> {stats.get('documents_skipped', 0)}</li>
                <li><strong>Fields Masked:</strong> {stats.get('fields_masked', 0)}</li>
                <li><strong>Processing Time:</strong> {time_str}</li>
                <li><strong>Processing Rate:</strong> {stats.get('processing_rate', 0):.2f} docs/sec</li>
            </ul>
            
            <h3>Collections:</h3>
            <ul>
                <li><strong>Source:</strong> {stats.get('source_db', '')}.{stats.get('source_collection', '')}</li>
                <li><strong>Destination:</strong> {stats.get('destination_db', '')}.{stats.get('destination_collection', '')}</li>
            </ul>
            
            <p>For more details, please check the log files.</p>
        </body>
        </html>
        """
        
        return self._send_email(subject, content, is_html=True)

    def send_error_alert(self, error_message: str, context: Dict[str, Any] = None) -> bool:
        """
        Send an error alert.

        Args:
            error_message: Error message to include in the alert.
            context: Additional context information about the error.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not self.enabled:
            logger.info("Email alerts disabled, skipping error notification")
            return False

        subject = f"[PHI Masking] Error Alert"
        
        # Build email content
        content = f"""
        <html>
        <body>
            <h2>PHI Masking Process Error</h2>
            <p>An error occurred during the PHI masking process:</p>
            
            <div style="background-color: #ffeeee; padding: 10px; border-left: 4px solid #ff0000;">
                <pre>{error_message}</pre>
            </div>
        """
        
        if context:
            content += "<h3>Error Context:</h3><ul>"
            for key, value in context.items():
                content += f"<li><strong>{key}:</strong> {value}</li>"
            content += "</ul>"
        
        content += """
            <p>Please check the log files for more details.</p>
        </body>
        </html>
        """
        
        return self._send_email(subject, content, is_html=True)

    def _send_email(self, subject: str, body: str, is_html: bool = False) -> bool:
        """
        Send an email.

        Args:
            subject: Email subject.
            body: Email body content.
            is_html: Whether the body is HTML content.

        Returns:
            True if email was sent successfully, False otherwise.
        """
        if not self.enabled or not self.recipients:
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = ", ".join(self.recipients)
            msg['Subject'] = subject
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {len(self.recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
            return False

    def _validate_email_config(self) -> bool:
        """
        Validate email configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        if not self.smtp_server:
            logger.warning("SMTP server not configured")
            return False
            
        if not self.sender:
            logger.warning("Email sender not configured")
            return False
            
        if not self.recipients:
            logger.warning("No email recipients configured")
            return False
            
        return True

    def _parse_recipients(self, recipients_str: str) -> List[str]:
        """
        Parse recipients string into a list.

        Args:
            recipients_str: Comma-separated list of email recipients.

        Returns:
            List of email addresses.
        """
        if not recipients_str:
            return []
            
        return [email.strip() for email in recipients_str.split(',') if email.strip()]

    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """
        Get boolean value from environment variables.

        Args:
            key: Environment variable key.
            default: Default value if key not found.

        Returns:
            Boolean value.
        """
        value = self.env.get(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'y', 't') 