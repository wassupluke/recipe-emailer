"""Tests for email_sender: recipient routing + SMTP send, fully mocked."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import email_sender


def _send(debug_mode: bool):
    """Call send_email with stub credentials + a mocked SMTP server.

    Returns (sent_message, server_mock) so tests can assert on routing/login.
    """
    with (
        patch.object(email_sender, "EMAIL_SENDER", "me@example.com"),
        patch.object(email_sender, "EMAIL_PASSWORD", "app-password"),
        patch.object(email_sender, "EMAIL_BCC", "a@example.com,b@example.com"),
        patch("email_sender.smtplib.SMTP_SSL") as mock_smtp,
    ):
        server = MagicMock()
        mock_smtp.return_value = server
        email_sender.send_email("<p>hi</p>", debug_mode, "Weekly Meals")
        sent_msg = server.send_message.call_args.args[0]
        return sent_msg, server, mock_smtp


class TestSendEmailRouting:
    """Bcc routing differs between debug and normal mode."""

    def test_normal_mode_bccs_the_recipient_list(self) -> None:
        """Normal mode sends to the configured BCC list, not just the sender."""
        msg, _, _ = _send(debug_mode=False)
        assert msg["Bcc"] == "a@example.com,b@example.com"
        assert msg["From"] == "me@example.com"

    def test_debug_mode_bccs_only_the_sender(self) -> None:
        """Debug mode routes the Bcc to the sender only (no recipient list)."""
        msg, _, _ = _send(debug_mode=True)
        assert msg["Bcc"] == "me@example.com"


class TestSendEmailDelivery:
    """The message is actually built and handed to an authenticated server."""

    def test_subject_and_html_body_are_set(self) -> None:
        """Subject is applied and the body is attached as HTML."""
        msg, _, _ = _send(debug_mode=False)
        assert msg["Subject"] == "Weekly Meals"
        payload = msg.get_payload()[0]
        assert payload.get_content_type() == "text/html"
        assert "<p>hi</p>" in payload.get_payload()

    def test_logs_in_and_sends_over_ssl(self) -> None:
        """send_email connects to the SMTP server, authenticates, and quits."""
        _, server, mock_smtp = _send(debug_mode=False)
        mock_smtp.assert_called_once_with(
            email_sender.SMTP_SERVER,
            email_sender.SMTP_PORT,
            context=mock_smtp.call_args.kwargs["context"],
        )
        server.login.assert_called_once_with("me@example.com", "app-password")
        server.send_message.assert_called_once()
        server.quit.assert_called_once()
