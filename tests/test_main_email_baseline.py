"""Tests for main.py's email wrappers: _generate_and_send_email + _send_error_notification."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import main


class TestGenerateAndSendEmail:
    """Tests for _generate_and_send_email."""

    @patch("main.send_email")
    @patch("main.generate_html_email")
    def test_builds_html_and_sends_with_subject(self, mock_generate, mock_send) -> None:
        """Generates HTML from meals, sends it under SUBJECT, returns the HTML."""
        mock_generate.return_value = "<html>menu</html>"
        context = {"unused_mains": {"a": {}, "b": {}}, "unused_sides": {"c": {}}}
        meals = [{"type": "single_main", "obj": {"u": {}}}]

        result = main._generate_and_send_email(context, meals, 123.0, debug_mode=False)

        assert result == "<html>menu</html>"
        # HTML built from the meals + remaining pool counts
        mock_generate.assert_called_once_with(meals, 123.0, 2, 1)
        # Sent with the generated body, the run's debug flag, and the menu subject
        mock_send.assert_called_once_with("<html>menu</html>", False, main.SUBJECT)

    @patch("main.send_email")
    @patch("main.generate_html_email", return_value="<html>x</html>")
    def test_passes_debug_flag_through_to_send(self, _mock_generate, mock_send) -> None:
        """The debug flag reaches send_email so debug runs only Bcc the sender."""
        main._generate_and_send_email(
            {"unused_mains": {}, "unused_sides": {}}, [], 0.0, debug_mode=True
        )
        assert mock_send.call_args.args[1] is True


class TestSendErrorNotification:
    """Tests for _send_error_notification."""

    @patch("main.send_email")
    def test_sends_to_sender_only_with_default_subject(self, mock_send) -> None:
        """Errors are emailed in debug mode (sender only) under the default subject."""
        main._send_error_notification(ValueError("boom"))

        mock_send.assert_called_once()
        body = mock_send.call_args.args[0]
        assert mock_send.call_args.kwargs["debug_mode"] is True  # never BCCs the list
        assert mock_send.call_args.kwargs["subject"] == "Recipe Emailer Error"
        assert "ValueError: boom" in body

    @patch("main.send_email")
    def test_custom_subject_and_escaped_traceback(self, mock_send) -> None:
        """A custom subject is used and the error text is HTML-escaped."""
        main._send_error_notification(
            ValueError("<script>"), subject="Website Publish Error"
        )
        body = mock_send.call_args.args[0]
        assert mock_send.call_args.kwargs["subject"] == "Website Publish Error"
        assert "&lt;script&gt;" in body  # escaped, not raw
        assert "<script>" not in body.replace("&lt;script&gt;", "")

    @patch("main.logger")
    @patch("main.send_email", side_effect=RuntimeError("smtp down"))
    def test_swallows_send_failure(self, _mock_send, mock_logger) -> None:
        """If the notification email itself fails, it logs and does not raise."""
        # Must not propagate -- error notification is best-effort.
        main._send_error_notification(ValueError("boom"))
        mock_logger.error.assert_called_once()
