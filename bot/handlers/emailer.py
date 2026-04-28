import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bot.utils.logger import get_logger

logger = get_logger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

TO_EMAIL = "michaelogaje033@gmail.com"


def send_new_user_email(telegram_id: int, username: str, first_name: str):
    try:
        subject = "🚀 New Bot User Alert"

        body = f"""
New user started your bot:

Name: {first_name}
Username: @{username}
Telegram ID: {telegram_id}
"""

        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = TO_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # 🔥 FIX: explicit connect()
        server = smtplib.SMTP()
        server.connect(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        server.send_message(msg)
        server.quit()

        print("[EMAIL] ✅ Sent successfully")

    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        print(f"[EMAIL] ❌ Failed: {e}")