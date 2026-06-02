#!/bin/bash

# Run the recipe emailer from the directory this script lives in, so the repo
# can be cloned/checked out anywhere (cron invokes this script by full path).
cd "$(dirname "$(readlink -f "$0")")" || exit 1

# Activate the virtualenv. Prefer .venv (the documented convention) and fall
# back to venv. If you have both, .venv wins -- delete whichever you don't use.
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
elif [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    echo "cook.sh: no virtualenv found (expected .venv/ or venv/)." >&2
    echo "Create one: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

python main.py >> cronjob.log

# Keep cronjob.log bounded: retain only the most recent ~2000 lines (dozens of
# weekly runs, well under a megabyte) so the log can't grow without limit.
tail -n 2000 cronjob.log > cronjob.log.tmp && mv cronjob.log.tmp cronjob.log

deactivate
