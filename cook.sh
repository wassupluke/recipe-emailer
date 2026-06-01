#!/bin/bash

# Run the recipe emailer from the directory this script lives in, so the repo
# can be cloned/checked out anywhere (cron invokes this script by full path).
cd "$(dirname "$(readlink -f "$0")")" || exit 1
source .venv/bin/activate
python main.py >> cronjob.log
deactivate
