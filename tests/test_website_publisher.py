"""Tests for website_publisher.write_publish_page."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import website_publisher


class TestWritePublishPage:
    """Tests for write_publish_page."""

    def test_writes_html_verbatim(self, tmp_path: Path) -> None:
        """The email HTML is written to the output path unchanged."""
        out = tmp_path / "index.html"
        html = "<!DOCTYPE html><html><body><div class='card'>Meal</div></body></html>"

        website_publisher.write_publish_page(html, str(out))

        assert out.read_text(encoding="utf-8") == html

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        """A subsequent run replaces last week's page."""
        out = tmp_path / "index.html"
        out.write_text("old page", encoding="utf-8")

        website_publisher.write_publish_page("<html>new</html>", str(out))

        assert out.read_text(encoding="utf-8") == "<html>new</html>"

    def test_preserves_unicode(self, tmp_path: Path) -> None:
        """Non-ASCII content (e.g. en-dashes) is written as UTF-8, not mangled."""
        out = tmp_path / "index.html"
        website_publisher.write_publish_page("<p>5–6 minutes</p>", str(out))
        assert "5–6" in out.read_text(encoding="utf-8")
