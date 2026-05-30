"""Tests for main._monitor_site_health wiring."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import main
from config import HEALTH_SUBJECT
from site_health import STATUS_OK, STATUS_REGEX_BROKEN, RunOutcome


class TestMonitorSiteHealth:
    @patch("main.send_email")
    @patch("main.save_json")
    @patch("main.load_json")
    def test_emails_maintainer_when_regex_broken(self, mock_load, mock_save, mock_send):
        mock_load.return_value = ({}, True)
        context = {
            "run_outcomes": [
                RunOutcome(
                    key="Site A — main course", status=STATUS_REGEX_BROKEN, url_count=0
                )
            ]
        }

        main._monitor_site_health(context)

        mock_save.assert_called_once()
        assert mock_send.call_count == 1
        _, kwargs = mock_send.call_args
        assert kwargs["debug_mode"] is True
        assert kwargs["subject"] == HEALTH_SUBJECT

    @patch("main.send_email")
    @patch("main.save_json")
    @patch("main.load_json")
    def test_no_email_when_all_ok(self, mock_load, mock_save, mock_send):
        mock_load.return_value = ({}, True)
        context = {
            "run_outcomes": [
                RunOutcome(key="Site A — main course", status=STATUS_OK, url_count=5)
            ]
        }

        main._monitor_site_health(context)

        mock_save.assert_called_once()
        mock_send.assert_not_called()

    @patch("main.send_email")
    @patch("main.save_json")
    @patch("main.load_json")
    def test_no_outcomes_does_nothing(self, mock_load, mock_save, mock_send):
        context: dict = {"run_outcomes": []}

        main._monitor_site_health(context)

        mock_load.assert_not_called()
        mock_save.assert_not_called()
        mock_send.assert_not_called()

    @patch("main.send_email")
    @patch("main.save_json")
    @patch("main.load_json")
    def test_never_raises_on_failure(self, mock_load, mock_save, mock_send):
        mock_load.side_effect = OSError("disk gone")
        context = {
            "run_outcomes": [
                RunOutcome(key="Site A — main course", status=STATUS_OK, url_count=5)
            ]
        }

        main._monitor_site_health(context)

        mock_send.assert_not_called()
