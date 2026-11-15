#!/bin/bash

# Run the recipe emailer from the directory this script lives in, so the repo
# can be cloned/checked out anywhere (cron invokes this script by full path).
cd "$(dirname "$(readlink -f "$0")")" || exit 1

# cron runs with a minimal PATH; the uv installer puts uv in ~/.local/bin.
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
    echo "cook.sh: uv not found. Install it: https://docs.astral.sh/uv/" >&2
    exit 1
fi

# uv run syncs .venv to uv.lock before running, so dependencies added by a
# git pull are installed automatically.
uv run main.py >> cronjob.log

# --- Publish to GitHub Pages (delete this block to disable) ----------------- #
# main.py writes index.html each run. Publish it to the gh-pages branch via a
# detached worktree so the main working tree (and its uncommitted recipe JSONs)
# is never touched. Requires a one-time setup -- see "GitHub Pages" in README.
if [ -f index.html ]; then
    publish_gh_pages() {
        local wt=".gh-pages-worktree"
        # Clean up any leftover worktree from a previously interrupted run.
        git worktree remove --force "$wt" 2>/dev/null
        rm -rf "$wt"
        # Make sure we have the remote gh-pages branch (a fresh clone / the Pi
        # may never have fetched it). Without this, origin/gh-pages won't exist.
        git fetch --quiet origin gh-pages || return 1
        # Check out gh-pages into a throwaway worktree at the remote tip.
        git worktree add --quiet -B gh-pages "$wt" origin/gh-pages || return 1
        cp index.html "$wt/index.html"
        git -C "$wt" add index.html
        if git -C "$wt" diff --cached --quiet; then
            echo "gh-pages: no change to index.html"
        else
            git -C "$wt" commit --quiet -m "Update weekly meals $(date +%F)"
            git -C "$wt" push --quiet origin gh-pages
            echo "gh-pages: pushed update"
        fi
        git worktree remove --force "$wt"
    }
    publish_gh_pages >> cronjob.log 2>&1 || echo "gh-pages publish failed" >> cronjob.log
else
    echo "gh-pages: no index.html written (debug run or earlier failure?)" >> cronjob.log
fi
# --------------------------------------------------------------------------- #

# Keep cronjob.log bounded: retain only the most recent ~2000 lines (dozens of
# weekly runs, well under a megabyte) so the log can't grow without limit.
tail -n 2000 cronjob.log > cronjob.log.tmp && mv cronjob.log.tmp cronjob.log
