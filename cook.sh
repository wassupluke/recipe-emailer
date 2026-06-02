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

# --- Publish to GitHub Pages (delete this block to disable) ----------------- #
# main.py writes index.html each run. Publish it to the gh-pages branch via a
# detached worktree so the main working tree (and its uncommitted recipe JSONs)
# is never touched. Requires a one-time setup -- see "GitHub Pages" in README.
if [ -f index.html ]; then
    publish_gh_pages() {
        local wt=".gh-pages-worktree"
        # Check out gh-pages into a throwaway worktree (track remote if present).
        git worktree add --quiet -B gh-pages "$wt" origin/gh-pages 2>/dev/null \
            || git worktree add --quiet "$wt" gh-pages || return 1
        cp index.html "$wt/index.html"
        git -C "$wt" add index.html
        if git -C "$wt" diff --cached --quiet; then
            echo "gh-pages: no change to index.html"
        else
            git -C "$wt" commit --quiet -m "Update weekly meals $(date +%F)"
            git -C "$wt" push --quiet origin gh-pages
        fi
        git worktree remove --force "$wt"
    }
    publish_gh_pages >> cronjob.log 2>&1 || echo "gh-pages publish failed" >> cronjob.log
fi
# --------------------------------------------------------------------------- #

# Keep cronjob.log bounded: retain only the most recent ~2000 lines (dozens of
# weekly runs, well under a megabyte) so the log can't grow without limit.
tail -n 2000 cronjob.log > cronjob.log.tmp && mv cronjob.log.tmp cronjob.log

deactivate
