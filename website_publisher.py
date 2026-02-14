"""Website publishing functionality for the meals page."""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)


def publish_meals_page(email_html: str, website_repo_path: str) -> None:
    """Write meals.html to the website repo and push changes.

    Takes the email HTML content, wraps it in the website's template,
    writes it to meals.html, and commits/pushes to the website repo.
    """
    logger.info("Publishing meals page to website repo")

    meals_html = generate_meals_page_html(email_html, website_repo_path)

    meals_path = os.path.join(website_repo_path, "meals.html")
    with open(meals_path, "w", encoding="utf-8") as f:
        f.write(meals_html)
    logger.info(f"Wrote meals page to {meals_path}")

    _git_commit_and_push(website_repo_path)


def generate_meals_page_html(email_html: str, website_repo_path: str) -> str:
    """Generate a website-compatible meals.html page from email HTML content."""
    # Extract recipe card content from email HTML body
    body_start = email_html.index("<body>") + len("<body>")
    body_end = email_html.index("</body>")
    recipe_content = email_html[body_start:body_end].strip()

    # Read navbar template from website repo
    navbar_path = os.path.join(website_repo_path, "templates", "navbar.html")
    with open(navbar_path, encoding="utf-8") as f:
        navbar = f.read()

    year = datetime.now().year

    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEALS</title>
    <link rel="stylesheet" href="styles/default.css">
    <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet" type="text/css">
    <link href="https://fonts.googleapis.com/css?family=Kaushan+Script" rel="stylesheet" type="text/css">
    <style>
      .meals-content {{
        font-family: "Roboto", sans-serif;
        background-color: #f8f4f0;
        color: #494949;
        padding: 20px;
        border-radius: 10px;
      }}
      .meals-content h1 {{
        font-family: "Kaushan Script", cursive;
        color: #e07a5f;
        margin: 0;
        font-size: 1.8rem;
        text-align: left;
      }}
      .meals-content h2 {{
        font-family: "Kaushan Script", cursive;
        color: #6d6875;
        margin-bottom: 10px;
        background-color: transparent;
        font-size: 1.4rem;
      }}
      .meals-content i {{
        color: #888;
        display: block;
        margin-top: 0;
      }}
      .meals-content p {{
        color: #555;
        margin-top: 0;
      }}
      .meals-content ul {{
        list-style-type: none;
        padding: 0;
      }}
      .meals-content li {{
        color: #666;
        margin-bottom: 5px;
      }}
      .meals-content .card {{
        background-color: #fbe2d4;
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 30px;
      }}
      .meals-content .polaroid {{
        margin: 10px;
        position: relative;
        width: 220px;
      }}
      .meals-content .polaroid img {{
        max-width: 250px;
        max-height: 250px;
        border-radius: 2px;
        border: 10px solid #fff;
        border-bottom: 35px solid #fff;
      }}
    </style>
  </head>
  <body>
    {navbar}
    <div class="container">
      <header><h1>Weekly Meals</h1></header>
      <div class="meals-content">
        {recipe_content}
      </div>
    </div>
    <footer>
      <p>&copy; {year} Luke Wass | Whatever you do, work at it with all your heart, as working for the Lord, not for men.</p>
    </footer>
  </body>
  <script src="static/js/nav.js"></script>
</html>
"""


def _git_commit_and_push(repo_path: str) -> None:
    """Add, commit, and push meals.html in the website repo."""

    def run_git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )

    run_git("add", "meals.html")

    # Check if there are staged changes
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_path,
        capture_output=True,
    )

    if result.returncode == 0:
        logger.info("No changes to meals.html, skipping commit")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    run_git("commit", "-m", f"Update weekly meals {date_str}")
    run_git("push")
    logger.info("Successfully pushed meals page update")
