# NYT Spelling Bee Answers Scraper (Python + GitHub Actions)

[![Daily Scraper](https://github.com/amcdonoughfisher001/BEE/actions/workflows/run_scraper.yml/badge.svg)](https://github.com/amcdonoughfisher001/BEE/actions/workflows/run_scraper.yml)

This repository automates scraping the daily NYT Spelling Bee answers and publishes them to `answers.json` at the repository root. It uses a resilient, multi-source approach with graceful fallbacks and deductive logic to determine the seven letters, center letter, and pangrams.

## What you get

- A Python scraper (`scraper.py`) using `requests` and `beautifulsoup4`
- Automated daily runs via GitHub Actions at 06:00 UTC
- Manual run capability via `workflow_dispatch`
- Automatic commit of `answers.json` with a dated commit message

---

## Quick Start

1. Create a new public GitHub repository (or use an existing one).

2. Add these files to your repository:
   - `scraper.py`
   - `requirements.txt`
   - `.github/workflows/run_scraper.yml`

3. Commit and push the files to your default branch (e.g., `main`).

4. Enable GitHub Actions in your repository if prompted. For public repos, scheduled workflows run automatically.

5. The workflow will:
   - Install dependencies
   - Run the scraper daily at 06:00 UTC
   - Save output to `answers.json`
   - Commit changes using a standard auto-commit action

You can also trigger it manually via the Actions tab (look for “Run NYT Spelling Bee Scraper”).

---

## Local Development

If you want to test locally:

```bash
# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the scraper (uses today's UTC date by default)
python scraper.py > answers.json

# Optionally, run for a specific date:
python scraper.py --date 2025-09-18 > answers.json
```

The output JSON structure:

```json
{
  "date": "YYYY-MM-DD",
  "letters": "ABCDEFG",
  "centerLetter": "A",
  "wordCount": 42,
  "pangrams": ["PANGRAMONE", "PANGRAMTWO"],
  "answers": ["WORDONE", "WORDTWO", "..."]
}
```

Notes:
- If no valid answers are found, the script still outputs a valid JSON object with empty fields (e.g., `wordCount: 0` and `answers: []`) for resiliency.

---

## How it works

- Multiple prioritized sources are queried. Each source attempts:
  - A structured parse (list items) using BeautifulSoup
  - A regex-based fallback parse
- A result is accepted if at least 15 valid words are found.
- Deductive logic:
  - Center letter: a letter present in every answer
  - Letters: top 7 most frequent letters across all answers (sorted alphabetically)
  - Pangrams: answers that use all seven letters
- Anti-bot measures:
  - Realistic headers with random User-Agent
  - Referrer set to Google
  - Randomized sleeps between requests

---

## GitHub Actions details

- Workflow file: `.github/workflows/run_scraper.yml`
- Triggers:
  - Scheduled: daily at 06:00 UTC
  - Manual: via `workflow_dispatch`
- Permissions:
  - `contents: write` to push `answers.json`
- Commit message:
  - “Update Spelling Bee answers for YYYY-MM-DD”
- Only `answers.json` is considered for commit (`file_pattern`).

If there are no changes to `answers.json`, the commit step will no-op.

---

## Customization

- Change Python version in `run_scraper.yml` if preferred.
- Adjust the cron schedule under `on.schedule`.
- Add or remove sources by editing the `sources_config()` function in `scraper.py`.
- Tweak parser logic if your preferred source structure changes.

---

## Troubleshooting

- Workflow didn’t run:
  - Ensure Actions are enabled in the repo.
  - For private repos, schedules may require additional configuration.
- Empty `answers.json`:
  - Sites may have changed structure or blocked automated access.
  - Try running locally and inspect stderr logs.
  - Consider adding additional sources or custom parsers.
- Commit not pushed:
  - Ensure `permissions: contents: write` is present in the workflow.
  - Confirm your default branch is not protected in a way that blocks the bot.

---

## Monitoring

- **Workflow Status**: The badge at the top of this README shows the status of the last automated run.
- **Manual Execution**: You can manually trigger the scraper by going to the Actions tab and clicking "Run workflow" on the "Run NYT Spelling Bee Scraper" workflow.
- **View Results**: Check the `answers.json` file in the repository root for the latest results.
- **Workflow History**: Visit the [Actions tab](../../actions/workflows/run_scraper.yml) to see all previous runs and their logs.

---

## Ethical and Legal Considerations

- Respect robots.txt and site terms.
- This scraper uses minimal, randomized delays and standard headers. Increase the delay or reduce frequency if needed.
- Content belongs to the respective publishers. Use responsibly.

---