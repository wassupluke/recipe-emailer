#!/usr/bin/env python3

"""A program I wrote to save my wife time and headache.

This program grabs recipes from all her favorite sites
and sends her a few to make each week. Now she doesn't
have to spend her time looking up what to make, it's all
automagic!
"""

# IMPORT STANDARD MODULES
import argparse
import json
import logging
import os
import random
import re
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# IMPORT THIRD-PARTY MODULES
import requests
from dotenv import load_dotenv
from recipe_scrapers import scrape_html
from tqdm import tqdm

# IMPORT LOCAL MODULES
from lists import veggies, websites
from tools import bcc_mailer

# VERSION TAG
version = 17.0

if __name__ == "__main__":
    try:
        ...
    except Exception as e:
        with open("error.log", "w+") as f:
            # clear existing logs
            f.write("")
            logging.exception("Code failed, see below: %s", e)
            error_content = "<br />".join(list(f.readlines()))
            bcc_mailer(error_content, True)
        raise
