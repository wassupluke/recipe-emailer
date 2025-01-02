#!/usr/bin/env python3

"""A program I wrote to save my wife time and headache.

This program grabs recipes from all her favorite sites
and sends her a few to make each week. Now she doesn't
have to spend her time looking up what to make, it's all
automagic!

## General workflow:
    1. Open data table
    2. From each website
        - Get recipes
        - Add recipes to data table with used == False
    3. Select random recipes from data table and changed used == True
    4. Build pretty HTML with selected recipes
    5. Email recipes
    6. Save data table
"""

# IMPORT STANDARD MODULES
import argparse
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
from pandas import DataFrame, read_json
from recipe_scrapers import scrape_html
from tqdm import tqdm

# IMPORT LOCAL MODULES
from lists import veggies
from tools import bcc_mailer, get_html, load_toml

# VERSION TAG
version = 17.0

# DEFINE FILENAME CONSTANTS
master_filename = "mmaster_data.json"
websites = load_toml("websites.toml")
debug_mode = False

if __name__ == "__main__":
    try:
        df = read_json(master_filename)

        urls = df["canonical_url"]
        for website in websites:
            html = get_html(website, debug_mode)

        json_str = df.to_json(orient="records")
        with open(master_filename, "w") as f:
            f.write(json_str)

    except Exception as e:
        with open("error.log", "w+") as f:
            # clear existing logs
            f.write("")
            logging.exception("Code failed, see below: %s", e)
            error_content = "<br />".join(list(f.readlines()))
        #            bcc_mailer(error_content, True)
        raise
