"""Write the weekly meals page for GitHub Pages publishing.

The email HTML produced by ``html_generator`` is already a complete, self-contained
document (``<!DOCTYPE>`` + inline CSS), so publishing is just writing it to a file
the web server serves. cook.sh commits + pushes that file to the gh-pages branch;
this module only produces the artifact.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def write_publish_page(email_html: str, output_path: str) -> None:
    """Write the email HTML to output_path as the standalone meals page."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(email_html)
    logger.info(f"Wrote publish page to {output_path}")
