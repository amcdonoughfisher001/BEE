#!/usr/bin/env python3
"""
NYT Spelling Bee Answers Scraper

A resilient, multi-source scraper that fetches daily NYT Spelling Bee answers
and publishes them to answers.json. Uses fallbacks and deductive logic to
determine the seven letters, center letter, and pangrams.
"""

import requests
import json
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
import time


class SpellingBeeScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.answers_file = 'answers.json'
        
    def get_nyt_official_data(self) -> Optional[Dict]:
        """
        Attempt to get data from NYT's official API/website.
        This is the primary source.
        """
        try:
            # NYT Spelling Bee game data endpoint (may require authentication)
            url = "https://www.nytimes.com/puzzles/spelling-bee"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Look for game data in the HTML
                game_data_match = re.search(r'window\.gameData\s*=\s*({.*?});', response.text)
                if game_data_match:
                    game_data = json.loads(game_data_match.group(1))
                    return self.extract_bee_data(game_data)
                    
        except Exception as e:
            print(f"NYT official source failed: {e}")
            
        return None
    
    def get_sbsolver_data(self) -> Optional[Dict]:
        """
        Fallback source: SB Solver or similar community sites.
        """
        try:
            # Example fallback API (replace with actual working endpoint)
            url = "https://api.example-bee-solver.com/today"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'letters': data.get('letters', []),
                    'center_letter': data.get('center', ''),
                    'pangrams': data.get('pangrams', []),
                    'answers': data.get('answers', [])
                }
                
        except Exception as e:
            print(f"SB Solver fallback failed: {e}")
            
        return None
    
    def get_reddit_data(self) -> Optional[Dict]:
        """
        Third fallback: Parse Reddit discussions for hints.
        """
        try:
            # Reddit API for spelling bee discussions
            url = "https://www.reddit.com/r/NYTSpellingBee/new.json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Parse recent posts for today's puzzle info
                return self.parse_reddit_posts(data)
                
        except Exception as e:
            print(f"Reddit fallback failed: {e}")
            
        return None
    
    def extract_bee_data(self, game_data: Dict) -> Optional[Dict]:
        """Extract spelling bee data from NYT game data."""
        try:
            today_data = game_data.get('today', {})
            if not today_data:
                return None
                
            return {
                'letters': today_data.get('outerLetters', []) + [today_data.get('centerLetter', '')],
                'center_letter': today_data.get('centerLetter', ''),
                'pangrams': today_data.get('pangrams', []),
                'answers': today_data.get('answers', [])
            }
        except Exception as e:
            print(f"Error extracting bee data: {e}")
            return None
    
    def parse_reddit_posts(self, reddit_data: Dict) -> Optional[Dict]:
        """Parse Reddit posts to extract spelling bee information."""
        try:
            posts = reddit_data.get('data', {}).get('children', [])
            today_str = datetime.now().strftime("%B %d")  # e.g., "January 15"
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '').lower()
                
                if today_str.lower() in title and 'spelling bee' in title:
                    # Try to extract letters from post content
                    selftext = post_data.get('selftext', '')
                    return self.extract_letters_from_text(selftext)
                    
        except Exception as e:
            print(f"Error parsing Reddit data: {e}")
            
        return None
    
    def extract_letters_from_text(self, text: str) -> Optional[Dict]:
        """Extract spelling bee letters from text using regex patterns."""
        try:
            # Look for patterns like "Letters: A B C D E F G" or similar
            letter_match = re.search(r'letters?:?\s*([a-zA-Z\s,]+)', text, re.IGNORECASE)
            if letter_match:
                letters = re.findall(r'[a-zA-Z]', letter_match.group(1))
                if len(letters) == 7:
                    # Assume first letter is center (common convention)
                    return {
                        'letters': letters,
                        'center_letter': letters[0],
                        'pangrams': [],  # Would need additional parsing
                        'answers': []    # Would need additional parsing
                    }
        except Exception as e:
            print(f"Error extracting letters from text: {e}")
            
        return None
    
    def deduce_missing_data(self, partial_data: Dict) -> Dict:
        """
        Use deductive logic to fill in missing information.
        """
        letters = partial_data.get('letters', [])
        center_letter = partial_data.get('center_letter', '')
        
        # If we have letters but no center letter, try to deduce it
        if letters and not center_letter and len(letters) == 7:
            # Common heuristics: center letter often appears frequently in English
            letter_frequency = {'E': 10, 'T': 9, 'A': 8, 'O': 7, 'I': 6, 'N': 6, 'S': 6, 'H': 6, 'R': 6}
            center_letter = max(letters, key=lambda x: letter_frequency.get(x.upper(), 0))
            partial_data['center_letter'] = center_letter
        
        return partial_data
    
    def scrape_daily_answers(self) -> Dict:
        """
        Main scraping method that tries multiple sources with fallbacks.
        """
        print(f"Scraping Spelling Bee answers for {datetime.now().strftime('%Y-%m-%d')}")
        
        # Try primary source
        data = self.get_nyt_official_data()
        if data:
            print("Successfully retrieved data from NYT official source")
            return data
        
        # Try fallback sources
        print("Primary source failed, trying fallbacks...")
        
        data = self.get_sbsolver_data()
        if data:
            print("Successfully retrieved data from SB Solver")
            return self.deduce_missing_data(data)
        
        data = self.get_reddit_data()
        if data:
            print("Successfully retrieved data from Reddit")
            return self.deduce_missing_data(data)
        
        # If all sources fail, return empty structure
        print("All sources failed, returning empty structure")
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'letters': [],
            'center_letter': '',
            'pangrams': [],
            'answers': [],
            'error': 'Unable to retrieve data from any source'
        }
    
    def save_answers(self, data: Dict):
        """Save the scraped data to answers.json"""
        # Add metadata
        data['date'] = datetime.now().strftime('%Y-%m-%d')
        data['scraped_at'] = datetime.now().isoformat()
        data['version'] = '1.0'
        
        # Load existing data if available
        existing_data = {}
        if os.path.exists(self.answers_file):
            try:
                with open(self.answers_file, 'r') as f:
                    existing_data = json.load(f)
            except Exception as e:
                print(f"Error loading existing data: {e}")
                existing_data = {}
        
        # Update with today's data
        today_key = data['date']
        existing_data[today_key] = data
        
        # Save updated data
        try:
            with open(self.answers_file, 'w') as f:
                json.dump(existing_data, f, indent=2, sort_keys=True)
            print(f"Successfully saved answers to {self.answers_file}")
        except Exception as e:
            print(f"Error saving answers: {e}")
    
    def run(self):
        """Main execution method"""
        try:
            data = self.scrape_daily_answers()
            self.save_answers(data)
            
            # Print summary
            print("\n=== Scraping Summary ===")
            print(f"Date: {data.get('date', 'Unknown')}")
            print(f"Letters: {', '.join(data.get('letters', []))}")
            print(f"Center Letter: {data.get('center_letter', 'Unknown')}")
            print(f"Pangrams: {len(data.get('pangrams', []))}")
            print(f"Total Answers: {len(data.get('answers', []))}")
            
            if data.get('error'):
                print(f"Error: {data['error']}")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Unexpected error during scraping: {e}")
            return 1


if __name__ == "__main__":
    scraper = SpellingBeeScraper()
    exit_code = scraper.run()
    exit(exit_code)