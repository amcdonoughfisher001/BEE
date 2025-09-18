#!/usr/bin/env python3
"""
NYT Spelling Bee Answers Scraper
=================================
Python implementation of the Google Apps Script logic for scraping
daily NYT Spelling Bee answers with fallback sources and deductive analysis.
"""

import json
import random
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class SpellingBeeScraper:
    """Main scraper class for NYT Spelling Bee answers."""
    
    # Common blocklist words to filter out
    COMMON_BLOCKLIST = {
        'HTML', 'HTTP', 'HTTPS', 'HEAD', 'BODY', 'SCRIPT', 'STYLE', 'META', 'JSON', 'AJAX', 
        'TYPE', 'NAME', 'CLASS', 'HREF', 'LINK', 'SPAN', 'DOCTYPE', 'CDATA', 'AICP',
        'TODAY', 'TODAYS', 'SPELLING', 'PUZZLE', 'ANSWERS', 'WORDS', 'GAME', 'LETTER', 
        'LETTERS', 'CENTER', 'PANGRAM', 'GENIUS', 'QUEEN', 'BEE',
        'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER', 'JANUARY', 'FEBRUARY', 'MARCH', 
        'APRIL', 'JUNE', 'JULY', 'AUGUST', 'MONDAY', 'TUESDAY',
        'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY', 'TIMES', 'NEWS', 'YORK', 'SOLUTION',
        'COMMENTS', 'REPLY', 'EMAIL', 'WEBSITE', 'SUBSCRIBE', 'LOGIN', 'LOGOUT', 'REGISTER', 
        'SEARCH', 'POST', 'EDIT', 'DELETE', 'UPDATE', 'VIEW', 'SHARE',
        'USER', 'ADMIN', 'FORUM', 'BLOG', 'ARCHIVE', 'SOLVER', 'HINT', 'PRIME', 'FINDER', 
        'SBHINTS', 'SBANSWERS', 'SBARCHIVE', 'TECHWISER', 'GUIDE',
        'COPYRIGHT', 'POLICY', 'CONTACT', 'ABOUT', 'PRIVACY', 'TERMS', 'SERVICE', 'FOLLOW'
    }
    
    # User agents for anti-bot measures
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
        })
    
    def _build_sources(self, date: datetime) -> List[Dict]:
        """Build list of sources with URLs for the given date."""
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                 'july', 'august', 'september', 'october', 'november', 'december']
        
        month_str = str(date.month).zfill(2)
        day_str = str(date.day).zfill(2)
        day_int = date.day
        year = date.year
        month_name = months[date.month - 1]
        date_formatted = date.strftime('%Y-%m-%d')
        
        return [
            {
                'name': 'SpellingBeeTimes',
                'url': f'https://spellingbeetimes.com/{year}/{month_str}/{day_str}/new-york-times-nyt-spelling-bee-answers-and-solution-for-{month_name}-{day_int}-{year}/'
            },
            {
                'name': 'Techwiser',
                'url': f'https://techwiser.com/todays-nyt-spelling-bee-answers-for-{month_name}-{day_int}-{year}/'
            },
            {
                'name': 'SBHints',
                'url': f'https://www.sbhints.com/nyt-spelling-bee-answers-{date_formatted}/'
            },
            {
                'name': 'PuzzlePrime',
                'url': f'https://www.puzzleprime.com/nyt-spelling-bee-answers-{date_formatted}/'
            },
            {
                'name': 'SBSolver',
                'url': 'https://www.sbsolver.com/answers'
            },
            {
                'name': 'NYT Official Yesterday',
                'url': 'https://www.nytimes.com/spotlight/spelling-bee-answers'
            },
            {
                'name': 'Reddit',
                'url': f'https://www.reddit.com/r/NYTSpellingBee/search/?q=Official%20{date_formatted}&restrict_sr=1&sort=new'
            }
        ]
    
    def _random_sleep(self, min_ms: int = 1000, max_ms: int = 2500) -> None:
        """Sleep for a random duration to avoid being blocked."""
        sleep_time = random.randint(min_ms, max_ms) / 1000.0
        time.sleep(sleep_time)
    
    def _fetch_with_anti_bot(self, url: str) -> Optional[str]:
        """Fetch URL with anti-bot measures."""
        try:
            # Random user agent
            user_agent = random.choice(self.USER_AGENTS)
            self.session.headers.update({'User-Agent': user_agent})
            
            # Random delay before request
            self._random_sleep(1000, 2500)
            
            response = self.session.get(url, timeout=30, allow_redirects=True)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"[HTTP-FAIL] {response.status_code} from {url}")
                return None
                
        except Exception as e:
            print(f"[NET-ERR] {str(e)} from {url}")
            return None
    
    def _is_spelling_bee_word(self, word: str) -> bool:
        """Check if a word is a valid Spelling Bee word."""
        if not word or not isinstance(word, str):
            return False
        
        w = word.strip().upper()
        
        # Check length (4-15 characters)
        if len(w) < 4 or len(w) > 15:
            return False
        
        # Check if only alphabetic
        if not w.isalpha():
            return False
        
        # Check against blocklist
        if w in self.COMMON_BLOCKLIST:
            return False
        
        return True
    
    def _generic_structured_parser(self, html: str) -> Dict:
        """Parse HTML looking for structured list items."""
        answers = set()
        
        try:
            # Look for list items with words
            pattern = r'<li>([A-Z]{4,})</li>'
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                word = match.upper()
                if self._is_spelling_bee_word(word):
                    answers.add(word)
                    
            # Also try BeautifulSoup parsing
            soup = BeautifulSoup(html, 'html.parser')
            list_items = soup.find_all('li')
            for item in list_items:
                text = item.get_text(strip=True).upper()
                if self._is_spelling_bee_word(text):
                    answers.add(text)
                    
        except Exception:
            pass
        
        return {'answers': list(answers)}
    
    def _generic_regex_parser(self, html: str) -> Dict:
        """Parse HTML using regex to find potential words."""
        answers = set()
        
        try:
            # Find all-caps words 4-15 characters long
            pattern = r'\b[A-Z]{4,15}\b'
            matches = re.findall(pattern, html)
            for match in matches:
                if self._is_spelling_bee_word(match):
                    answers.add(match)
                    
        except Exception:
            pass
        
        return {'answers': list(answers)}
    
    def _validate_result(self, result: Dict) -> bool:
        """Validate that a result has enough answers."""
        return (result and 
                'answers' in result and 
                result['answers'] and 
                len(result['answers']) >= 15)
    
    def _find_center_letter(self, answers: List[str]) -> Optional[str]:
        """Find the center letter (present in every word)."""
        if not answers:
            return None
        
        # Get unique letters from the first word
        first_word_letters = set(answers[0])
        
        # Check each letter to see if it's in every word
        for letter in first_word_letters:
            if all(letter in word for word in answers):
                return letter
                
        return None
    
    def _find_all_letters(self, answers: List[str]) -> Optional[str]:
        """Find all 7 puzzle letters using frequency analysis."""
        if not answers or len(answers) < 10:
            return None
        
        # Count frequency of each letter
        letter_counts = {}
        for word in answers:
            for letter in word:
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
        
        # Sort by frequency (descending)
        sorted_letters = sorted(letter_counts.keys(), 
                              key=lambda x: letter_counts[x], 
                              reverse=True)
        
        # Take top 7 letters
        if len(sorted_letters) >= 7:
            puzzle_letters = sorted(sorted_letters[:7])
            return ''.join(puzzle_letters)
        
        return None
    
    def _find_pangrams(self, answers: List[str], letters: str) -> List[str]:
        """Find pangrams (words using all 7 letters)."""
        if not answers or not letters or len(letters) != 7:
            return []
        
        letter_set = set(letters)
        pangrams = []
        
        for word in answers:
            word_letters = set(word)
            # Must have at least 7 unique letters and contain all puzzle letters
            if len(word_letters) >= 7 and letter_set.issubset(word_letters):
                pangrams.append(word)
        
        return pangrams
    
    def scrape(self, target_date: Optional[datetime] = None) -> Dict:
        """Main scraping function."""
        if target_date is None:
            target_date = datetime.now(timezone.utc)
        
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"[START] Scraper for {date_str}")
        
        sources = self._build_sources(target_date)
        best_result = None
        best_source = None
        log_summary = []
        
        for source in sources:
            try:
                url = source['url']
                print(f"[TRY] {source['name']} | {url}")
                
                html = self._fetch_with_anti_bot(url)
                if not html:
                    log_summary.append(f"{source['name']}: HTTP FAIL")
                    continue
                
                # Try both parsers
                result = None
                for parser_func in [self._generic_structured_parser, self._generic_regex_parser]:
                    result = parser_func(html)
                    if self._validate_result(result):
                        break
                
                if self._validate_result(result):
                    print(f"[FOUND] {len(result['answers'])} answers from {source['name']}")
                    best_result = result
                    best_source = source['name']
                    break
                else:
                    word_count = len(result['answers']) if result else 0
                    log_summary.append(f"{source['name']}: PARSE/VALIDATION FAIL (Found {word_count} words)")
                    
            except Exception as e:
                print(f"[ERROR] Unhandled exception in source {source['name']}: {str(e)}")
                log_summary.append(f"{source['name']}: SCRIPT ERROR")
            
            # Sleep between sources
            self._random_sleep(1500, 3000)
        
        if best_result:
            # Perform deductive analysis
            best_result['centerLetter'] = self._find_center_letter(best_result['answers'])
            best_result['letters'] = self._find_all_letters(best_result['answers'])
            best_result['pangrams'] = self._find_pangrams(best_result['answers'], best_result['letters'] or '')
            
            print(f"[ANALYSIS] Center: {best_result['centerLetter']}, Letters: {best_result['letters']}")
            print(f"[DONE] Saved {len(best_result['answers'])} words from {best_source}")
            
            # Build final result
            result = {
                'date': date_str,
                'letters': best_result['letters'] or '',
                'centerLetter': best_result['centerLetter'] or '',
                'wordCount': len(best_result['answers']),
                'pangrams': best_result['pangrams'] or [],
                'answers': sorted(best_result['answers'])
            }
            
            return result
        else:
            error_msg = f"[FAIL] No valid answers found. Details: {'; '.join(log_summary)}"
            print(error_msg)
            raise Exception(error_msg)


def main():
    """Main entry point."""
    scraper = SpellingBeeScraper()
    
    try:
        result = scraper.scrape()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {str(e)}", file=__import__('sys').stderr)
        exit(1)


if __name__ == '__main__':
    main()