"""Email sending functionality."""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_BCC,
)


def mailer(content: str, debug_mode: bool) -> None:
    """Email pretty formatted meals to recipents, can do BCC.

    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html.
    """
    msg = MIMEMultipart()
    msg["Subject"] = "Weekly Meals"
    # Set msg['Bcc'] to SENDER if in debug mode
    if debug_mode:
        msg["Bcc"] = EMAIL_SENDER
    else:
        msg["Bcc"] = EMAIL_BCC

    msg["From"] = EMAIL_SENDER
    msg.attach(MIMEText(content, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=c)
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    # server.set_debuglevel(1)  # uncomment for more verbose terminal output
    server.send_message(msg)
    server.quit()