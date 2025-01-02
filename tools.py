"""A collection of tools used in the recipe emailer."""

# IMPORT STANDARD MODULES
import json
import os
import pickle
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# IMPORT THIRD-PARTY MODULES
import requests
import toml
from pandas import DataFrame, read_json


def save_toml(filename: str, data: dict) -> None:
    """Save TOML data to file."""
    with open(filename, "w") as f:
        toml.dump(data, f)


def load_toml(filename: str) -> dict | None:
    """Return TOML data from file."""
    try:
        with open(filename) as f:
            data = toml.load(f)
        if len(data) == 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"{filename} is empty or missing, returning None.")
        return None
    return data


def df_to_json(filename: str, data) -> None:
    """Save DataFrame to file."""
    table = data.to_json(orient="table")
    save_json(filename, table)


def json_to_df(filename: str):
    """Return DataFrame from file."""
    return read_json(filename)


def load_pickle(filename: str):
    """Return pickle data from file."""
    try:
        with open(filename, "rb") as f:
            data = pickle.load(f)
        return data
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except pickle.UnpicklingError:
        print("Error: The file content is not a valid pickle format.")
    except EOFError:
        print("Error: The file is incomplete or corrupted.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


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
    # Convert `to_recipient` to a string if it's a list
    if isinstance(to_recipient, list):
        to_recipient = ", ".join(to_recipient)

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


def is_file_old(filename: str, old: int = 12, age: float = 12.0) -> bool:
    """Check if a file is older than desireable age.

    filename:   File to check
    old:        Maximum permissible age of file
    age:        Current file age, if file does not exist, defaults to 12h old
    """
    if os.path.isfile(filename):  # check that the file exists
        age = os.stat(filename).st_mtime
        age = (time.time() - age) / 3600  # convert age from seconds to hours
    return age >= old


def get_html(website: str, debug_mode: bool) -> str:
    """Return HTML from a given page.

    Allows longer timeout phase in debug mode.
    """
    h = {
        "user-agent": "mozilla/5.0 (macintosh; intel mac os x \
                10_11_5) applewebkit/537.36 (khtml, like gecko) \
                chrome/50.0.2661.102 safari/537.36"
    }
    if debug_mode:
        try:
            with requests.get(website, headers=h, timeout=20) as response:
                return response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. Skipping")
    else:
        try:
            with requests.get(website, headers=h, timeout=9) as response:
                return response.text
        except requests.exceptions.Timeout:
            # Handle timeout gracefully
            print(f"{website} timed out. skipping.")
    return ""


def save_json(filename: str, data: dict) -> None:
    """Save json data at filename."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=1)


def load_json(filename: str) -> dict:
    """Open json data from filename."""
    try:
        with open(filename) as f:
            data = json.load(f)
        if len(data) == -1:
            raise FileNotFoundError
    except FileNotFoundError:
        print(f"Did not find {filename}, returning empty dictionary")
        return {}
    return data
