# Recipe Emailer v17.0

> Automatically scrapes recipes from ~20 cooking websites each week and emails a
> curated, balanced dinner menu to your household.

**What it does:** once a week (typically via cron), Recipe Emailer scrapes fresh
recipes from a list of cooking sites, picks a balanced set of meals — by default
two land-protein mains, one seafood main, plus vegetable sides where a meal needs
one — and emails the menu (with images, ingredients, and instructions) to your
recipients. It remembers what it has already sent so meals don't repeat, and it
nudges each week's picks toward **seasonally-appropriate** recipes (light/no-cook
dishes in summer, hearty/oven dishes in winter) using a small local model that
needs no network or API keys at run time. It's built to run unattended on
low-powered hardware like a Raspberry Pi: failures are logged and skipped rather
than crashing the weekly run.

## 🎯 What's New in v17.0

- 🌱 **Seasonal AI selection** — each recipe is scored for seasonal fit by a
  distilled, **pure-numpy model** that ships in the repo (`seasonal_model.json`).
  Inference is instant with **no Ollama, network, or GPU at run time**; picks are
  biased toward in-season recipes and toward oven use in winter / oven-light in
  summer. Applies to both mains **and** sides. (Replaces an earlier ~60s/recipe
  runtime-LLM approach.)
- 🩺 **Site-health monitoring** — when a site's scraper regex silently breaks or a
  site is unreachable, the maintainer gets an email instead of a quietly
  shrinking menu. Tracks an 8-run rolling window in `site_health.json`.
- 💧 **Streaming scrape** — recipes are scraped one page at a time instead of
  buffering every page in memory, fixing out-of-memory crashes on the Pi.
- 🔤 **Encoding fix** — scraped pages are decoded by their declared/sniffed
  charset, eliminating UTF-8 mojibake (e.g. `5â€"6` now renders as `5–6`).
- 🧰 **Operational hardening** — location-independent, venv-aware `cook.sh`;
  self-capping logs (`cronjob.log` trimmed, `recipe_emailer.log` rotated to the
  last 8 runs); `numpy` pinned as a runtime dependency.

### Foundation (from the v16.0 refactor)

- ✅ **Type-hinted throughout** - mypy type-checked in CI
- ✅ **Production logging** - structured, leveled logging throughout
- ✅ **Custom exceptions** - no `sys.exit()` in business logic
- ✅ **Comprehensive testing** - 159 tests, ~77% coverage
- ✅ **Modern tooling** - black, ruff, mypy, pytest configured

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/wassupluke/recipe-emailer.git
cd recipe-emailer

# Install dependencies
pip install -r requirements.txt

# Or install in development mode with dev tools
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file with your credentials:

```env
SENDER=your-email@gmail.com
PASSWD=your-google-app-password
BCC=recipient1@example.com,recipient2@example.com
```

**Note:** For Gmail, you need an [App Password](https://myaccount.google.com/apppasswords), not your regular password.

### Usage

```bash
# Normal mode - sends emails to configured recipients
python main.py

# Debug mode - sends only to sender, selects single website
python main.py -d
# or
python main.py --debug
```

### Scheduling with cron

`cook.sh` activates the virtualenv and runs the emailer, appending output to
`cronjob.log`. It resolves its own location, so it works no matter where you
cloned the repo. Make it executable, then add a crontab entry:

```bash
chmod +x cook.sh
crontab -e
```

```cron
# Run the Recipe Emailer at 8a on Fridays
0 8 * * Fri /home/wassu/code/recipe-emailer/cook.sh
```

Adjust the path to wherever you cloned the repo.

### Publishing to GitHub Pages (optional)

Each run writes a self-contained `index.html` (the same content as the email).
`cook.sh` commits + pushes it to a **`gh-pages` branch** of this repo, so your
weekly menu is served at `https://<user>.github.io/<repo>/` — without ever adding
generated pages to your `main` history.

One-time setup:

```bash
# Create an empty gh-pages branch with a first index.html
git switch --orphan gh-pages
git commit --allow-empty -m "init gh-pages"
git push -u origin gh-pages
git switch main
```

Then enable Pages in the repo settings (**Settings → Pages → Build from branch →
`gh-pages` / root**). After that, every `cook.sh` run publishes automatically.

`index.html` is gitignored on `main` and pushed via a throwaway git worktree, so
the publish step never touches your working tree or the recipe JSON files. **To
disable publishing, delete the marked block in `cook.sh`** — the rest of the run
(scrape, email) is unaffected.

## 📋 Features

### Core Functionality

- **Multi-site scraping**: Scrapes 20 recipe websites automatically
- **Smart selection**: Balances protein types (seafood vs. land-based)
- **Veggie checking**: Ensures meals have adequate vegetables, adds sides if needed
- **Seasonal bias**: A distilled local model nudges picks toward in-season recipes
- **Site-health monitoring**: Emails the maintainer when a scraper's regex breaks
- **Deduplication**: Tracks used recipes, avoids repeats
- **Error resilience**: Continues on failures, tracks problematic URLs

### Quality Features

- **Type safety**: Type hints throughout, mypy type-checked in CI
- **Error handling**: Custom exceptions, detailed error messages
- **Logging**: Structured, self-capping file logs + console output
- **Testing**: Comprehensive test suite (159 tests)
- **Documentation**: Docstring coverage enforced at ≥95% (interrogate)

## 🏗️ Architecture

### Module Structure

Flat layout — every module is a top-level file at the repo root:

```
main.py                  Entry point and pipeline orchestration
config.py                Configuration and constants
file_utils.py            JSON load/save (the recipe "database")
websites.py              Per-site scrape configs (regex + index URLs)
web_scraper.py           HTTP fetch + HTML -> recipe parsing
recipe_processor.py      Streaming batch scrape across sites
recipe_selector.py       Protein selection + veggie/side checking
seasonal_tagging.py      Per-recipe oven-use + seasonality tags
seasonal_model.py        Pure-numpy seasonal "student" inference
seasonal_selection.py    Season/heat-weighted recipe selection
seasonal_label.py        Teacher labeling for training (desktop/GPU)
train_seasonal_model.py  Train + export seasonal_model.json (desktop)
backfill_seasonality.py  One-off tagger for the existing backlog
site_health.py           Scraper regex-failure / reachability monitoring
html_generator.py        Email HTML generation
email_sender.py          SMTP email delivery
website_publisher.py     Write the standalone index.html page for publishing
debug_utils.py           Debug-mode utilities
pyproject.toml           Project + tooling configuration
tests/                   Test suite
```

### Data Flow

1. **Load config** (`config.py`) — env vars + constants.
2. **Load state** (`file_utils.py`) — read the tracking JSON files; check debug mode.
3. **Scrape** (`recipe_processor.py` → `web_scraper.py`) — stream recipes from each
   site one page at a time; record regex/reachability problems (`site_health.py`).
4. **Tag** (`seasonal_tagging.py` / `seasonal_model.py`) — add oven-use + seasonality
   scores to any untagged recipes (instant, pure-numpy).
5. **Select** (`recipe_selector.py` + `seasonal_selection.py`) — balance proteins,
   ensure veggies/sides, bias toward in-season picks.
6. **Render** (`html_generator.py`) — build the email HTML.
7. **Send** (`email_sender.py`) — SMTP delivery.
8. **Write page** (`website_publisher.py`) — write the standalone `index.html`;
   `cook.sh` then commits + pushes it to the `gh-pages` branch.
9. **Persist** (`file_utils.py`) — move sent recipes to used, save tracking JSON.

## 🧪 Testing

### Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_file_utils.py -v

# Run with detailed coverage report
pytest --cov --cov-report=html
```

### Coverage Report

```bash
# View HTML coverage report
open htmlcov/index.html
```

Current coverage: **~77%** across 159 tests.

Target: **95%+** (all modules)

## 🛠️ Development

### Code Quality Tools

```bash
# Type checking
mypy .

# Formatting
black .

# Linting
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Run all checks
mypy . && ruff check . && black --check .
```

### Pre-commit Checklist

- [ ] All tests passing: `pytest`
- [ ] Type checks clean: `mypy .`
- [ ] Linting clean: `ruff check .`
- [ ] Formatted: `black .`
- [ ] Documentation updated
- [ ] Changelog updated

## 📊 Performance

### Benchmarks (Typical Run)

| Operation | Time | Notes |
|-|-|-|
| Startup | ~0.09s | Load config, imports |
| URL extraction | ~8s | ~20 sites |
| Recipe parsing | ~142s | network I/O dominated |
| Seasonal tagging | <1s | pure-numpy, cached model load |
| Email generation | ~0.03s | HTML formatting |
| **Total** | **~150s** | Average full run (scrape-bound) |

Subsequent runs within `FILE_AGE_THRESHOLD` reuse the cached recipe pool and skip
scraping entirely, completing in a few seconds.

## 🔧 Configuration

### Environment Variables

Set in `.env` (loaded via `python-dotenv`):

| Variable | Required | Description |
|-|-|-|
| `SENDER` | ✅ | Gmail address for sending |
| `PASSWD` | ✅ | Gmail app password |
| `BCC` | ✅ | Comma-separated recipients |

### Configurable Constants

All in `config.py`. Defaults shown.

**Scraping**
- `FILE_AGE_THRESHOLD` (12): hours before the recipe pool is re-scraped.
- `NORMAL_TIMEOUT` / `DEBUG_TIMEOUT` (9 / 20): per-request HTTP timeout, seconds.
- `SCRAPE_FLUSH_INTERVAL` (100): how often (in URLs) the streaming scrape flushes
  progress to disk.

**Meal selection**
- `LANDFOOD_COUNT_WITH_SEAFOOD` (2): land mains to send when seafood is available.
- `SEAFOOD_COUNT` (1): seafood mains to send when available.
- `LANDFOOD_COUNT_NO_SEAFOOD` (3): total land mains when no seafood is available.
- `SEAFOOD_PROTEINS` / `LANDFOOD_PROTEINS`: ingredient keywords that classify a
  recipe's protein type.
- `VEGGIES`: vegetable keywords; a main without one gets a side dish added.

**Seasonal scoring** (see [Seasonal AI Selection](#seasonal-ai-selection))
- `HEAT_WEIGHT` (0.5): how strongly winter-oven / summer-no-oven tilts the score.
- `SELECTION_SHARPNESS` (3.0): exponent on selection weights; higher = stronger
  bias toward in-season recipes (a 0.8 recipe becomes ~50× likelier than a 0.2).
- `MIN_SCORE` (0.01): floor so weighted-random never sees a zero weight.
- `SPRING/SUMMER/FALL/WINTER_CENTER`: day-of-year season centers used to blend
  today's date into per-season weights.
- `SEASONAL_MODEL_FILENAME` / `SEASONAL_LABELS_FILENAME`: the committed student
  model artifact and the teacher labels used to train it.
- `OLLAMA_HOST` / `SEASONAL_MODEL` / `OLLAMA_TIMEOUT`: **teacher/training only** —
  the Ollama endpoint, teacher model, and request timeout used by
  `seasonal_label.py`. Unused on the host at run time.

**Email**
- `SUBJECT` ("Weekly Meals") / `HEALTH_SUBJECT`: email subject lines.
- `SMTP_SERVER` / `SMTP_PORT`: Gmail SMTP (SSL) defaults.

### Supported Websites

Currently scrapes 20 recipe websites, including:
- Recipe Runner
- Paleo Running Momma
- Skinny Taste
- Two Peas and Their Pod
- Well Plated
- The Spruce Eats
- Eating Bird Food
- Budget Bytes
- Minimalist Baker
- Pinch of Yum
- Love and Lemons
- *(and more - see `websites.py`)*

### Seasonal AI Selection

Meal selection is biased toward seasonally-appropriate recipes and toward oven
use in winter / grilling in summer. Each recipe gets four per-season scores from
a small **distilled "student" model** — a TF-IDF + ridge regression trained
offline and shipped in the repo as `seasonal_model.json`. Inference is pure
numpy: no network, no Ollama, and no GPU at runtime. (numpy is the only added
runtime dependency and is installed by `pip install -r requirements.txt`.)

There is **no setup** on the host (e.g. the Raspberry Pi) — the model file is
committed, so a normal `python main.py` run scores any newly-scraped recipes
inline and instantly. If the model file is missing or a recipe has no usable
text, scoring falls back to a neutral 0.5 per season and nothing breaks.

#### Retraining the model (optional, desktop/GPU only)

The student is distilled from a local "teacher" LLM via [Ollama](https://ollama.com).
You only need this to refresh the model on newly-scraped recipes; the Pi never
runs the teacher. Do it on a machine with a GPU + Ollama, with the dev extras
installed (`pip install -e ".[dev]"`, which brings in scikit-learn):

    ollama pull llama3.1:8b

    # 1. label the recipe corpus with the teacher (resumable):
    SEASONAL_MODEL=llama3.1:8b python seasonal_label.py   # -> seasonal_labels.json

    # 2. train + export the numpy student, then commit it:
    python train_seasonal_model.py                        # -> seasonal_model.json
    git add seasonal_model.json seasonal_labels.json && git commit

Teacher-only env vars: `OLLAMA_HOST` (default `http://localhost:11434`) and
`SEASONAL_MODEL` (the teacher model, e.g. `llama3.1:8b`). These affect labeling
only and have no effect on the Pi at runtime.

## 🐛 Troubleshooting

### Common Issues

**Problem:** `ModuleNotFoundError: No module named 'recipe_scrapers'`

**Solution:**
```bash
pip install -r requirements.txt
```

---

**Problem:** `ValueError: EMAIL_SENDER not configured`

**Solution:** Create `.env` file with required variables (see Configuration above)

---

**Problem:** Gmail authentication fails

**Solution:** Use an [App Password](https://myaccount.google.com/apppasswords), not your regular Gmail password

---

**Problem:** No recipes found

**Solution:** Check that recipe files aren't too old (>12 hours). Delete JSON files to force refresh.

---

**Problem:** Meals don't look seasonal / `Seasonal student prediction failed` in the log

**Solution:** The seasonal model needs `numpy`, which a bare `git pull` won't
install. Run `pip install -r requirements.txt`. Confirm the model loads:
```bash
python -c "import numpy, json; print('vocab', len(json.load(open('seasonal_model.json'))['idf']))"
```
If the model is missing or numpy isn't installed, scoring falls back to neutral
(no seasonal bias) rather than crashing.

---

### Debug Mode

For troubleshooting, use debug mode:

```bash
python main.py -d
```

This will:
- Prompt you to select a single website
- Send emails only to the sender (not BCC list)
- Use longer timeouts for requests
- Skip saving updated recipe files

## 📝 Logging

Two log files, both self-capping so they can't grow without bound (all `*.log`
files are gitignored):

- **`recipe_emailer.log`** — structured logger output (timestamps + levels),
  written on every run whether launched by hand or by cron. Rotated **per run**,
  retaining the last 8 runs (the same window the site-health email reports), so
  it's easy to inspect "what did the last few runs do."
- **`cronjob.log`** — full stdout capture from cron via `cook.sh` (the logger
  lines **plus** scraping-progress prints), trimmed to the last ~2000 lines.

Console output (stdout) mirrors the logger at INFO and above.

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages (recoverable issues)
- `ERROR`: Error messages (serious issues)

### Example Log Output

```
2026-06-01 18:08:10 - __main__ - INFO - Recipe Emailer started at 2026-06-01 18:08:10
2026-06-01 18:08:10 - __main__ - INFO - Loading existing recipe data
2026-06-01 18:08:10 - __main__ - INFO - Seasonal tagging: tagged 0 new recipe(s)
2026-06-01 18:08:10 - recipe_selector - INFO - Selected 3 recipes: 1 seafood, 2 landfood
2026-06-01 18:08:10 - __main__ - INFO - selected https://.../tzatziki-chicken-salad/ [single_main]: season_fit=0.873 final_score=0.676
2026-06-01 18:08:11 - __main__ - INFO - Sending email
2026-06-01 18:08:12 - __main__ - INFO - ✓ Process completed successfully in 2.63s
```

The `selected ... season_fit=... final_score=...` lines record why each meal was
picked — useful since chosen recipes are removed from the pool after a run.

## 📄 License

MIT License - see LICENSE file

## 👤 Author

**wassupluke**

## 🙏 Acknowledgments

- [hhursev/recipe-scrapers](https://github.com/hhursev/recipe-scrapers) - Recipe parsing library
- [theskumar/python-dotenv](https://github.com/theskumar/python-dotenv) - Environment management
- [tqdm/tqdm](https://github.com/tqdm/tqdm) - Progress bars

## 🔄 Version History

### v17.0.0 (2026) - Feature additions
- **Seasonal AI selection**: distilled pure-numpy model biases picks toward in-season recipes (no runtime LLM)
- **Site-health monitoring**: alerts the maintainer when a scraper's regex breaks
- **Streaming scrape**: fixes Raspberry Pi out-of-memory on large scrapes
- **Encoding fix**: scraped pages decode by declared/sniffed charset (no more UTF-8 mojibake)

### v16.0.0 (2024-02-13) - Major Refactor
- Complete codebase refactor
- 100% type coverage
- Comprehensive testing
- Production logging
- Zero technical debt

### v15.5 (Previous)
- Original functional version

---

**Made with ❤️ for easier meal planning**
