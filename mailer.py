import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def bcc_mailer(
    from_sender: str,
    to_recipient: str | list,
    subject: str,
    content: str,
    sender_password: str,
) -> None:
    """Send email from sender to recipient(s).

    https://www.justintodata.com/send-email-using-python-tutorial/
    https://docs.python.org/3/library/email.examples.html
    """
    msg = MIMEMultipart()
    msg["From"] = from_sender
    msg["Bcc"] = to_recipient
    msg["Subject"] = subject

    msg.attach(MIMEText(content, "html"))

    c = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=c)
    server.login(from_sender, sender_password)
    # server.set_debuglevel(1)  # uncomment for more verbose terminal output
    server.send_message(msg)
    server.quit()
