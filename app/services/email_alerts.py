import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import (
    SMTP_EMAIL,
    SMTP_PASSWORD,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_FROM_EMAIL,
)
from app.models.monitor import Monitor


logger = logging.getLogger(__name__)


def send_email_alert(
    monitor: Monitor,
    is_up: bool,
    status_code,
    response_time,
    error_message,
):
    """
    Send an email when a monitor changes state.

    Returns True when the email is sent successfully.
    Returns False when email configuration is missing or sending fails.
    """

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning(
            "Email alert skipped: SMTP credentials are not configured."
        )
        return False

    if not monitor.email:
        logger.warning(
            "Email alert skipped: no alert email configured for '%s'.",
            monitor.name,
        )
        return False

    status_label = "UP" if is_up else "DOWN"

    if is_up:
        subject = f"Website Recovered: {monitor.name}"
    else:
        subject = f"Website Down: {monitor.name}"

    body = [
        "Website Uptime Monitor",
        "",
        f"Website: {monitor.name}",
        f"URL: {monitor.url}",
        f"Status: {status_label}",
        f"Expected HTTP Status: {monitor.expected_status}",
        f"Observed HTTP Status: {status_code or 'N/A'}",
        f"Response Time: {response_time if response_time is not None else 'N/A'} seconds",
    ]

    if error_message:
        body.extend(
            [
                "",
                f"Error: {error_message}",
            ]
        )

    body.extend(
        [
            "",
            "This alert was generated automatically by "
            "the Website Uptime Monitor.",
        ]
    )

    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL or SMTP_EMAIL
    message["To"] = monitor.email
    message["Subject"] = subject
    message.set_content("\n".join(body))

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20,
        ) as server:

            if SMTP_USE_TLS:
                server.starttls(context=context)

            server.login(
                SMTP_EMAIL,
                SMTP_PASSWORD,
            )

            server.send_message(message)

        logger.info(
            "Email alert sent successfully for monitor '%s'.",
            monitor.name,
        )

        return True

    except smtplib.SMTPException:
        logger.exception(
            "SMTP error while sending alert for '%s'.",
            monitor.name,
        )
        return False

    except OSError:
        logger.exception(
            "Network error while sending alert for '%s'.",
            monitor.name,
        )
        return False