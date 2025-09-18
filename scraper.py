#!/usr/bin/env python3
"""
NYT Spelling Bee Answers Scraper (Python)

- Iterates through prioritized sources, using anti-bot headers and randomized delays.
- Parses HTML using BeautifulSoup and a regex fallback.
- Validates a result by requiring >= 15 words.
- Deductive analysis:
  - findCenterLetter: letter present in every word
  - findAllLetters: frequency analysis across all answers -> top 7 letters, sorted
  - findPangrams: words that include all seven letters
- Prints a JSON object to stdout:

{
  "date": "YYYY-MM-DD",
  "letters": "ABCDEFG",
  "centerLetter": "A",
  "wordCount": 42,
  "pangrams": ["PANGRAMONE", "PANGRAMTWO"],
  "answers": ["WORDONE", "WORDTWO", ...]
}

Notes:
- Requires: requests, beautifulsoup4
"""

import sys
import re
import json
import time
import random
import string
import traceback
from datetime import datetime, timezone, date as date_cls
from typing import Callable, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# -----------------------------
# Configuration
# -----------------------------

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

COMMON_BLOCKLIST = {
    'HTML', 'HTTP', 'HTTPS', 'HEAD', 'BODY', 'SCRIPT', 'STYLE', 'META', 'JSON', 'AJAX', 'TYPE', 'NAME', 'CLASS', 'HREF', 'LINK', 'SPAN', 'DOCTYPE', 'CDATA', 'AICP',
    'TODAY', 'TODAYS', 'SPELLING', 'PUZZLE', 'ANSWERS', 'WORDS', 'GAME', 'LETTER', 'LETTERS', 'CENTER', 'PANGRAM', 'GENIUS', 'QUEEN', 'BEE',
    'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'JUNE', 'JULY', 'AUGUST', 'MONDAY', 'TUESDAY',
    'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', 'TIMES', 'NEWS', 'YORK', 'SOLUTION',
    'COMMENTS', 'REPLY', 'EMAIL', 'WEBSITE', 'SUBSCRIBE', 'LOGIN', 'LOGOUT', 'REGISTER', 'SEARCH', 'POST', 'EDIT', 'DELETE', 'UPDATE', 'VIEW', 'SHARE',
    'USER', 'ADMIN', 'FORUM', 'BLOG', 'ARCHIVE', 'SOLVER', 'HINT', 'PRIME', 'FINDER', 'SBHINTS', 'SBANSWERS', 'SBARCHIVE', 'TECHWISER', 'GUIDE',
    'COPYRIGHT', 'POLICY', 'CONTACT', 'ABOUT', 'PRIVACY', 'TERMS', 'SERVICE', 'FOLLOW'
}

# -----------------------------
# Utilities
# -----------------------------

def log(msg: str) -> None:
    print(msg, file=sys.stderr)

def rand_sleep(min_ms: int, max_ms: int) -> None:
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)

def today_utc() -> date_cls:
    return datetime.now(timezone.utc).date()

def format_date(dt: date_cls) -> str:
    return dt.strftime("%Y-%m-%d")

def unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out

# -----------------------------
# Fetch with anti-bot
# -----------------------------

def fetch_html(url: str, timeout: int = 20) -> Optional[str]:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }
    try:
        rand_sleep(1000, 2500)
        with requests.Session() as s:
            resp = s.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200 and resp.text:
                return resp.text
            log(f"[HTTP-FAIL] {resp.status_code} from {url}")
            return None
    except Exception as e:
        log(f"[NET-ERR] {e} from {url}")
        return None

# -----------------------------
# Parsers and Validators
# -----------------------------

def is_spelling_bee_word(word: str) -> bool:
    if not word or not isinstance(word, str):
        return False
    w = word.strip().upper()
    if len(w) < 4 or len(w) > 15:
        return False
    if not re.fullmatch(r"[A-Z]+", w):
        return False
    if w in COMMON_BLOCKLIST:
        return False
    return True

def generic_structured_parser(html: str) -> Dict[str, List[str]]:
    answers: List[str] = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for li in soup.find_all("li"):
            text = li.get_text(separator=" ", strip=True)
            if not text:
                continue
            w = text.strip().upper()
            # keep only pure A-Z tokens in a list item (split in case of multiple words)
            tokens = [t for t in re.findall(r"\b[A-Z]{4,15}\b", w)]
            for t in tokens:
                if is_spelling_bee_word(t):
                    answers.append(t)
    except Exception:
        # ignore parsing errors
        pass
    return {"answers": unique_preserve_order(answers)}

def generic_regex_parser(html: str) -> Dict[str, List[str]]:
    answers: List[str] = []
    try:
        # Pull text for more signal, then scan for uppercase words
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ").upper()
        words = re.findall(r"\b[A-Z]{4,15}\b", text)
        for w in words:
            if is_spelling_bee_word(w):
                answers.append(w)
    except Exception:
        pass
    return {"answers": unique_preserve_order(answers)}

def validate_result(result: Optional[Dict[str, List[str]]]) -> bool:
    return bool(result and isinstance(result.get("answers"), list) and len(result["answers"]) >= 15)

# -----------------------------
# Deductive logic
# -----------------------------

def find_center_letter(answers: List[str]) -> Optional[str]:
    if not answers:
        return None
    first = answers[0]
    # preserve order of appearance in first word but unique
    seen = set()
    first_letters = []
    for ch in first:
        if ch not in seen:
            seen.add(ch)
            first_letters.append(ch)
    for letter in first_letters:
        if all(letter in w for w in answers):
            return letter
    return None

def find_all_letters(answers: List[str]) -> Optional[str]:
    if not answers or len(answers) < 10:
        return None
    counts: Dict[str, int] = {}
    for word in answers:
        for ch in word:
            if ch in string.ascii_uppercase:
                counts[ch] = counts.get(ch, 0) + 1
    if not counts:
        return None
    # Sort by frequency desc, then alphabetically to stabilize ties
    sorted_letters = sorted(counts.keys(), key=lambda c: (-counts[c], c))
    if len(sorted_letters) >= 7:
        top7 = sorted(sorted_letters[:7])
        return "".join(top7)
    return None

def find_pangrams(answers: List[str], letters: Optional[str]) -> List[str]:
    if not answers or not letters or len(letters) != 7:
        return []
    req = set(letters)
    pangrams = []
    for w in answers:
        wl = set(w)
        if len(wl) >= 7 and req.issubset(wl):
            pangrams.append(w)
    return pangrams

# -----------------------------
# Sources
# -----------------------------

class Source:
    def __init__(self, name: str, build_url: Callable[[date_cls], str], parsers: List[Callable[[str], Dict[str, List[str]]]]):
        self.name = name
        self.build_url = build_url
        self.parsers = parsers

def sources_config() -> List[Source]:
    def spelling_bee_times(d: date_cls) -> str:
        m_idx = d.month - 1
        day = f"{d.day:02d}"
        y = d.year
        month_str = f"{d.month:02d}"
        return f"https://spellingbeetimes.com/{y}/{month_str}/{day}/new-york-times-nyt-spelling-bee-answers-and-solution-for-{MONTHS[m_idx]}-{int(day)}-{y}/"

    def techwiser(d: date_cls) -> str:
        return f"https://techwiser.com/todays-nyt-spelling-bee-answers-for-{MONTHS[d.month - 1]}-{d.day}-{d.year}/"

    def sbhints(d: date_cls) -> str:
        return f"https://www.sbhints.com/nyt-spelling-bee-answers-{d.strftime('%Y-%m-%d')}/"

    def puzzleprime(d: date_cls) -> str:
        return f"https://www.puzzleprime.com/nyt-spelling-bee-answers-{d.strftime('%Y-%m-%d')}/"

    def sbsolver(_: date_cls) -> str:
        return "https://www.sbsolver.com/answers"

    def nyt_official_yesterday(_: date_cls) -> str:
        return "https://www.nytimes.com/spotlight/spelling-bee-answers"

    def reddit(d: date_cls) -> str:
        return f"https://www.reddit.com/r/NYTSpellingBee/search/?q=Official%20{d.strftime('%Y-%m-%d')}&restrict_sr=1&sort=new"

    parsers = [generic_structured_parser, generic_regex_parser]
    return [
        Source("SpellingBeeTimes", spelling_bee_times, parsers),
        Source("Techwiser", techwiser, parsers),
        Source("SBHints", sbhints, parsers),
        Source("PuzzlePrime", puzzleprime, parsers),
        Source("SBSolver", sbsolver, parsers),
        Source("NYT Official Yesterday", nyt_official_yesterday, parsers),
        Source("Reddit", reddit, parsers),
    ]

# -----------------------------
# Main scraping flow
# -----------------------------

def scrape_for_date(d: date_cls) -> Tuple[Optional[Dict], List[str]]:
    log_summary: List[str] = []
    best_result: Optional[Dict[str, List[str]]] = None
    best_source: Optional[str] = None

    for src in sources_config():
        try:
            url = src.build_url(d)
            log(f"[TRY] {src.name} | {url}")
            html = fetch_html(url)
            if not html:
                log_summary.append(f"{src.name}: HTTP FAIL")
                rand_sleep(1500, 3000)
                continue

            result: Optional[Dict[str, List[str]]] = None
            for parser in src.parsers:
                result = parser(html)
                if validate_result(result):
                    break

            if validate_result(result):
                answers = result["answers"]
                log(f"[FOUND] {len(answers)} answers from {src.name}")
                best_result = {"answers": answers}
                best_source = src.name
                break
            else:
                wc = len(result["answers"]) if result and "answers" in result else 0
                log_summary.append(f"{src.name}: PARSE/VALIDATION FAIL (Found {wc} words)")
        except Exception as e:
            log(f"[ERROR] Unhandled exception in source {src.name}: {e}")
            traceback.print_exc(file=sys.stderr)
            log_summary.append(f"{src.name}: SCRIPT ERROR")
        finally:
            rand_sleep(1500, 3000)

    if best_result:
        answers = [w.upper() for w in best_result["answers"]]
        center = find_center_letter(answers) or ""
        letters = find_all_letters(answers) or ""
        pangrams = find_pangrams(answers, letters)
        # Deduplicate and sort for stable output
        answers = sorted(unique_preserve_order(answers))
        pangrams = sorted(unique_preserve_order(pangrams))

        result_json = {
            "date": format_date(d),
            "letters": letters,
            "centerLetter": center,
            "wordCount": len(answers),
            "pangrams": pangrams,
            "answers": answers,
        }
        return result_json, log_summary

    # If no valid result was found, return empty structure to remain resilient
    error_details = "; ".join(log_summary) if log_summary else "No sources attempted"
    log(f"[FAIL] No valid answers found. Details: {error_details}")
    result_json = {
        "date": format_date(d),
        "letters": "",
        "centerLetter": "",
        "wordCount": 0,
        "pangrams": [],
        "answers": [],
    }
    return result_json, log_summary

def parse_cli_date() -> Optional[date_cls]:
    # Optional CLI argument: --date YYYY-MM-DD
    # If provided, use that date; otherwise use today UTC
    argv = sys.argv[1:]
    if not argv:
        return None
    for i, a in enumerate(argv):
        if a == "--date" and i + 1 < len(argv):
            try:
                return datetime.strptime(argv[i + 1], "%Y-%m-%d").date()
            except ValueError:
                log(f"[WARN] Invalid date format for --date: {argv[i + 1]} (expected YYYY-MM-DD)")
    return None

def main() -> None:
    target_date = parse_cli_date() or today_utc()
    log(f"[START] Scraper for {format_date(target_date)}")

    result_json, _log = scrape_for_date(target_date)
    print(json.dumps(result_json, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()