"""
Email service — sends notifications via SMTP.

Used by background workers. Falls back gracefully when SMTP is unavailable.
"""

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    plain_body: Optional[str] = None,
) -> bool:
    """
    Send an email via SMTP.

    Returns True if sent successfully, False otherwise.
    Never raises — errors are logged and returned as False.
    """
    try:
        import aiosmtplib

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if plain_body:
            msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_TLS,
        )

        logger.info(f"Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# ───────────────── Email Templates ─────────────────

def application_confirmation_email(candidate_name: str, job_title: str) -> tuple[str, str]:
    """Returns (subject, html_body) for application confirmation."""
    subject = f"Application Received — {job_title}"
    html = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">RecruitFlow</h1>
        </div>
        <div style="padding: 30px; background: #ffffff; border: 1px solid #e2e8f0;">
            <h2 style="color: #1a202c;">Hi {candidate_name},</h2>
            <p style="color: #4a5568; line-height: 1.6;">
                Thank you for applying for the <strong>{job_title}</strong> position.
                We've received your application and our team will review it shortly.
            </p>
            <p style="color: #4a5568; line-height: 1.6;">
                You can track your application status in your dashboard at any time.
            </p>
            <div style="margin-top: 20px; padding: 15px; background: #f7fafc; border-radius: 8px;">
                <p style="color: #718096; font-size: 14px; margin: 0;">
                    This is an automated notification. Please do not reply to this email.
                </p>
            </div>
        </div>
    </div>
    """
    return subject, html


def interview_scheduled_email(
    candidate_name: str, job_title: str, interview_date: str, meeting_link: str
) -> tuple[str, str]:
    """Returns (subject, html_body) for interview scheduling."""
    subject = f"Interview Scheduled — {job_title}"
    html = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">RecruitFlow</h1>
        </div>
        <div style="padding: 30px; background: #ffffff; border: 1px solid #e2e8f0;">
            <h2 style="color: #1a202c;">Hi {candidate_name},</h2>
            <p style="color: #4a5568; line-height: 1.6;">
                Your interview for <strong>{job_title}</strong> has been scheduled.
            </p>
            <div style="margin: 20px 0; padding: 20px; background: #ebf4ff; border-radius: 8px; border-left: 4px solid #667eea;">
                <p style="margin: 0 0 8px; color: #2d3748;"><strong>Date & Time:</strong> {interview_date}</p>
                <p style="margin: 0;"><strong>Meeting Link:</strong> <a href="{meeting_link}" style="color: #667eea;">{meeting_link}</a></p>
            </div>
            <p style="color: #4a5568; line-height: 1.6;">
                Please join on time. Good luck!
            </p>
        </div>
    </div>
    """
    return subject, html


def status_change_email(candidate_name: str, job_title: str, new_status: str) -> tuple[str, str]:
    """Returns (subject, html_body) for application status change."""
    subject = f"Application Update — {job_title}"
    html = f"""
    <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">RecruitFlow</h1>
        </div>
        <div style="padding: 30px; background: #ffffff; border: 1px solid #e2e8f0;">
            <h2 style="color: #1a202c;">Hi {candidate_name},</h2>
            <p style="color: #4a5568; line-height: 1.6;">
                There's an update on your application for <strong>{job_title}</strong>.
            </p>
            <div style="text-align: center; margin: 20px 0;">
                <span style="display: inline-block; padding: 10px 24px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; font-weight: 600;">
                    {new_status}
                </span>
            </div>
            <p style="color: #4a5568; line-height: 1.6;">
                Log in to your dashboard for more details.
            </p>
        </div>
    </div>
    """
    return subject, html
