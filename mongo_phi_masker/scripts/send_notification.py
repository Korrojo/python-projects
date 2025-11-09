#!/usr/bin/env python3
"""
Email Notification Script for PHI Masking Orchestration

Sends HTML-formatted email notifications for orchestration workflow success/failure.

Usage:
    python scripts/send_notification.py success \
        --collection Patients \
        --duration "5m 23s" \
        --src-env PROD \
        --proc-env DEV \
        --dst-env PROD \
        --artifacts "backup1,backup2" \
        --log-file "path/to/log"

    python scripts/send_notification.py failure \
        --collection Patients \
        --step "3" \
        --step-name "Mask Data" \
        --error "Connection timeout" \
        --log-file "path/to/log" \
        --src-env PROD \
        --proc-env DEV
"""

import argparse
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Optional


def load_env_config() -> dict:
    """Load email configuration from shared_config/.env"""
    config = {}
    env_file = Path(__file__).parent.parent.parent / "shared_config" / ".env"

    if not env_file.exists():
        print(f"Warning: .env file not found at {env_file}")
        return config

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    return config


def get_config_value(config: dict, key: str, default: str = "") -> str:
    """Get configuration value with default"""
    return config.get(key, default)


def create_success_email_html(
    collection: str,
    duration: str,
    src_env: str,
    proc_env: str,
    dst_env: str,
    artifacts: List[str],
    log_file: str,
    timestamp: str,
) -> str:
    """Create HTML email body for successful orchestration"""

    artifacts_html = ""
    for artifact in artifacts:
        artifacts_html += f"            <li style='margin: 5px 0; color: #555;'>{artifact}</li>\n"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
        .header .icon {{ font-size: 48px; margin-bottom: 10px; }}
        .content {{ background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none; }}
        .section {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 6px; border-left: 4px solid #28a745; }}
        .section h2 {{ margin: 0 0 15px 0; color: #28a745; font-size: 18px; font-weight: 600; }}
        .info-row {{ display: flex; margin-bottom: 12px; }}
        .info-label {{ font-weight: 600; width: 140px; color: #666; }}
        .info-value {{ color: #333; flex: 1; }}
        .artifacts {{ background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 10px; }}
        .artifacts ul {{ margin: 10px 0; padding-left: 20px; }}
        .footer {{ background: #343a40; color: #adb5bd; padding: 20px; border-radius: 0 0 8px 8px; text-align: center; font-size: 13px; }}
        .footer a {{ color: #20c997; text-decoration: none; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .badge-success {{ background: #d4edda; color: #155724; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">✅</div>
            <h1>PHI Masking Workflow Complete</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">All steps completed successfully</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>Workflow Summary</h2>
                <div class="info-row">
                    <div class="info-label">Collection:</div>
                    <div class="info-value"><strong>{collection}</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Status:</div>
                    <div class="info-value"><span class="badge badge-success">SUCCESS</span></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Duration:</div>
                    <div class="info-value">{duration}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Completed:</div>
                    <div class="info-value">{timestamp}</div>
                </div>
            </div>

            <div class="section">
                <h2>Data Flow</h2>
                <div class="info-row">
                    <div class="info-label">Source:</div>
                    <div class="info-value">{src_env}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Processing:</div>
                    <div class="info-value">{proc_env}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Destination:</div>
                    <div class="info-value">{dst_env}</div>
                </div>
            </div>

            <div class="section">
                <h2>Artifacts Created</h2>
                <div class="artifacts">
                    <ul>
{artifacts_html}
                    </ul>
                </div>
            </div>

            <div class="section">
                <h2>Log File</h2>
                <div class="info-row">
                    <div class="info-value" style="font-family: monospace; font-size: 13px; word-break: break-all;">{log_file}</div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p style="margin: 0 0 10px 0;">MongoDB PHI Masking Orchestration System</p>
            <p style="margin: 0; font-size: 12px;">
                This is an automated notification. For issues, contact your system administrator.
            </p>
        </div>
    </div>
</body>
</html>
"""
    return html


def create_failure_email_html(
    collection: str,
    step: str,
    step_name: str,
    error: str,
    log_file: str,
    src_env: str,
    proc_env: str,
    dst_env: Optional[str],
    timestamp: str,
) -> str:
    """Create HTML email body for failed orchestration"""

    dst_env_html = ""
    if dst_env:
        dst_env_html = f"""
                <div class="info-row">
                    <div class="info-label">Destination:</div>
                    <div class="info-value">{dst_env}</div>
                </div>
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 650px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; font-weight: 600; }}
        .header .icon {{ font-size: 48px; margin-bottom: 10px; }}
        .content {{ background: #f8f9fa; padding: 30px; border: 1px solid #dee2e6; border-top: none; }}
        .section {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 6px; border-left: 4px solid #dc3545; }}
        .section h2 {{ margin: 0 0 15px 0; color: #dc3545; font-size: 18px; font-weight: 600; }}
        .info-row {{ display: flex; margin-bottom: 12px; }}
        .info-label {{ font-weight: 600; width: 140px; color: #666; }}
        .info-value {{ color: #333; flex: 1; }}
        .error-box {{ background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 15px; border-radius: 4px; margin-top: 10px; font-family: monospace; font-size: 13px; word-break: break-word; }}
        .footer {{ background: #343a40; color: #adb5bd; padding: 20px; border-radius: 0 0 8px 8px; text-align: center; font-size: 13px; }}
        .footer a {{ color: #dc3545; text-decoration: none; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .action-required {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-top: 20px; border-radius: 4px; }}
        .action-required h3 {{ margin: 0 0 10px 0; color: #856404; font-size: 16px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">❌</div>
            <h1>PHI Masking Workflow Failed</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Action required - workflow incomplete</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>Failure Summary</h2>
                <div class="info-row">
                    <div class="info-label">Collection:</div>
                    <div class="info-value"><strong>{collection}</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Status:</div>
                    <div class="info-value"><span class="badge badge-danger">FAILED</span></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Failed Step:</div>
                    <div class="info-value">Step {step}: {step_name}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Time:</div>
                    <div class="info-value">{timestamp}</div>
                </div>
            </div>

            <div class="section">
                <h2>Error Details</h2>
                <div class="error-box">
                    {error}
                </div>
            </div>

            <div class="section">
                <h2>Environment Details</h2>
                <div class="info-row">
                    <div class="info-label">Source:</div>
                    <div class="info-value">{src_env}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Processing:</div>
                    <div class="info-value">{proc_env}</div>
                </div>
{dst_env_html}
            </div>

            <div class="section">
                <h2>Log File</h2>
                <div class="info-row">
                    <div class="info-value" style="font-family: monospace; font-size: 13px; word-break: break-all;">{log_file}</div>
                </div>
            </div>

            <div class="action-required">
                <h3>⚠️ Action Required</h3>
                <p style="margin: 0; color: #856404;">
                    Please review the log file and address the error before re-running the workflow.
                    The masking process did not complete successfully.
                </p>
            </div>
        </div>

        <div class="footer">
            <p style="margin: 0 0 10px 0;">MongoDB PHI Masking Orchestration System</p>
            <p style="margin: 0; font-size: 12px;">
                This is an automated notification. For urgent issues, contact your system administrator immediately.
            </p>
        </div>
    </div>
</body>
</html>
"""
    return html


def send_email(recipients: List[str], subject: str, html_body: str, config: dict) -> bool:
    """Send HTML email via SMTP"""

    # Get SMTP configuration
    smtp_host = get_config_value(config, "SMTP_HOST")
    smtp_port = int(get_config_value(config, "SMTP_PORT", "587"))
    smtp_use_tls = get_config_value(config, "SMTP_USE_TLS", "true").lower() == "true"
    smtp_username = get_config_value(config, "SMTP_USERNAME")
    smtp_password = get_config_value(config, "SMTP_PASSWORD")
    sender = get_config_value(config, "EMAIL_SENDER", smtp_username)
    sender_name = get_config_value(config, "EMAIL_SENDER_NAME", "PHI Masking System")

    # Validate required settings
    if not smtp_host:
        print("Error: SMTP_HOST not configured in .env")
        return False

    if not recipients:
        print("Error: No email recipients specified")
        return False

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender}>"
    msg["To"] = ", ".join(recipients)

    # Attach HTML body
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port)

        # Use STARTTLS if enabled
        if smtp_use_tls:
            server.starttls()

        # Login if credentials provided
        if smtp_username and smtp_password:
            server.login(smtp_username, smtp_password)

        # Send email
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()

        print(f"✓ Email sent successfully to: {', '.join(recipients)}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"Error: SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"Error: SMTP error occurred: {e}")
        return False
    except Exception as e:
        print(f"Error: Failed to send email: {e}")
        return False


def send_success_notification(args, config: dict) -> bool:
    """Send success notification email"""

    # Parse recipients
    recipients_str = get_config_value(config, "EMAIL_RECIPIENTS")
    if not recipients_str:
        print("Warning: EMAIL_RECIPIENTS not configured, skipping notification")
        return True

    recipients = [r.strip() for r in recipients_str.split(",")]

    # Parse artifacts
    artifacts = []
    if args.artifacts:
        artifacts = [a.strip() for a in args.artifacts.split(",")]

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create email subject
    subject_prefix = get_config_value(config, "EMAIL_SUBJECT_PREFIX", "[PHI Masker]")
    env_name = get_config_value(config, "EMAIL_ENV_NAME", get_config_value(config, "APP_ENV", "Unknown"))
    subject = f"{subject_prefix} SUCCESS - {args.collection} masking complete ({env_name})"

    # Create HTML body
    html_body = create_success_email_html(
        collection=args.collection,
        duration=args.duration,
        src_env=args.src_env,
        proc_env=args.proc_env,
        dst_env=args.dst_env,
        artifacts=artifacts,
        log_file=args.log_file,
        timestamp=timestamp,
    )

    # Send email
    return send_email(recipients, subject, html_body, config)


def send_failure_notification(args, config: dict) -> bool:
    """Send failure notification email"""

    # Parse recipients
    recipients_str = get_config_value(config, "EMAIL_RECIPIENTS")
    if not recipients_str:
        print("Warning: EMAIL_RECIPIENTS not configured, skipping notification")
        return True

    recipients = [r.strip() for r in recipients_str.split(",")]

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create email subject
    subject_prefix = get_config_value(config, "EMAIL_SUBJECT_PREFIX", "[PHI Masker]")
    env_name = get_config_value(config, "EMAIL_ENV_NAME", get_config_value(config, "APP_ENV", "Unknown"))
    subject = f"{subject_prefix} FAILURE - {args.collection} masking failed at Step {args.step} ({env_name})"

    # Create HTML body
    html_body = create_failure_email_html(
        collection=args.collection,
        step=args.step,
        step_name=args.step_name,
        error=args.error,
        log_file=args.log_file,
        src_env=args.src_env,
        proc_env=args.proc_env,
        dst_env=getattr(args, "dst_env", None),
        timestamp=timestamp,
    )

    # Send email
    return send_email(recipients, subject, html_body, config)


def main():
    parser = argparse.ArgumentParser(
        description="Send email notifications for PHI masking orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="notification_type", help="Notification type")

    # Success notification
    success_parser = subparsers.add_parser("success", help="Send success notification")
    success_parser.add_argument("--collection", required=True, help="Collection name")
    success_parser.add_argument("--duration", required=True, help='Total duration (e.g., "5m 23s")')
    success_parser.add_argument("--src-env", required=True, help="Source environment")
    success_parser.add_argument("--proc-env", required=True, help="Processing environment")
    success_parser.add_argument("--dst-env", required=True, help="Destination environment")
    success_parser.add_argument("--artifacts", required=False, help="Comma-separated artifacts created")
    success_parser.add_argument("--log-file", required=True, help="Path to log file")

    # Failure notification
    failure_parser = subparsers.add_parser("failure", help="Send failure notification")
    failure_parser.add_argument("--collection", required=True, help="Collection name")
    failure_parser.add_argument("--step", required=True, help="Failed step number")
    failure_parser.add_argument("--step-name", required=True, help="Failed step name")
    failure_parser.add_argument("--error", required=True, help="Error message")
    failure_parser.add_argument("--log-file", required=True, help="Path to log file")
    failure_parser.add_argument("--src-env", required=True, help="Source environment")
    failure_parser.add_argument("--proc-env", required=True, help="Processing environment")
    failure_parser.add_argument("--dst-env", required=False, help="Destination environment (optional)")

    args = parser.parse_args()

    if not args.notification_type:
        parser.print_help()
        return 1

    # Load configuration
    config = load_env_config()

    # Check if notifications are enabled
    enabled = get_config_value(config, "EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    if not enabled:
        print("Email notifications are disabled (EMAIL_NOTIFICATIONS_ENABLED=false)")
        return 0

    # Send notification
    if args.notification_type == "success":
        success = send_success_notification(args, config)
    else:
        success = send_failure_notification(args, config)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
