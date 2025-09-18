# NYT Spelling Bee Automated Scraper

An automated system that scrapes the daily New York Times Spelling Bee answers and publishes them to this GitHub repository. The system runs daily via GitHub Actions and provides answers in JSON format.

## Features

- **Automated Daily Scraping**: Runs automatically every day at 06:00 UTC
- **Multiple Fallback Sources**: Uses 7 different sources with priority ordering for reliability
- **Deductive Analysis**: Automatically determines center letter, all puzzle letters, and pangrams
- **Anti-Bot Measures**: Implements user agent rotation and random delays
- **JSON Output**: Provides structured data with all puzzle information
- **Manual Trigger**: Supports manual workflow runs via GitHub Actions

## Output Format

The scraper generates an `answers.json` file with the following structure:

```json
{
  "date": "2024-01-15",
  "letters": "ABCDEFG",
  "centerLetter": "A",
  "wordCount": 42,
  "pangrams": ["PANGRAMONE", "PANGRAMTWO"],
  "answers": ["WORDONE", "WORDTWO", ...]
}
```

## Setup Instructions

Follow these steps to set up the automated scraper in your own GitHub repository:

### 1. Create a New Repository

1. Create a new **public** GitHub repository (private repos have limited GitHub Actions minutes)
2. Clone the repository to your local machine

### 2. Copy the Files

Copy these files to your repository root:

- `scraper.py` - The main Python scraper script
- `requirements.txt` - Python dependencies
- `.github/workflows/run_scraper.yml` - GitHub Actions workflow
- `README.md` - This documentation (optional)

### 3. Configure Repository Settings

1. Go to your repository settings on GitHub
2. Navigate to **Actions** → **General**
3. Under "Workflow permissions", ensure "Read and write permissions" is selected
4. This allows the workflow to commit back to the repository

### 4. Test Manual Run

1. Go to the **Actions** tab in your GitHub repository
2. Select the "NYT Spelling Bee Scraper" workflow
3. Click "Run workflow" to trigger a manual run
4. Monitor the workflow execution to ensure it completes successfully

### 5. Verify Automation

- The workflow will run automatically daily at 06:00 UTC
- Check that `answers.json` gets updated with new puzzle data
- View commit history to see automated updates

## How It Works

### Sources (in priority order)
1. **SpellingBeeTimes** - Primary source with reliable structured data
2. **Techwiser** - Secondary source with good parsing
3. **SBHints** - Backup source with consistent formatting
4. **PuzzlePrime** - Additional fallback option
5. **SBSolver** - Live solver interface
6. **NYT Official Yesterday** - Official NYT archive
7. **Reddit** - Community discussion threads

### Scraping Process

1. **Source Iteration**: Tries each source in priority order until valid data is found
2. **Anti-Bot Measures**: Random user agents, delays, and proper HTTP headers
3. **Dual Parsing**: Uses both structured HTML parsing and regex pattern matching
4. **Validation**: Ensures at least 15 words found before accepting results
5. **Deductive Analysis**:
   - **Center Letter**: Finds the letter present in every word
   - **All Letters**: Uses frequency analysis to identify the 7 puzzle letters
   - **Pangrams**: Identifies words using all 7 letters

### Error Handling

- Network failures trigger fallback to next source
- Parsing failures attempt alternative parsing methods
- Complete failures are logged with detailed error messages
- Manual trigger available for re-runs if needed

## Customization

### Change Schedule
Edit `.github/workflows/run_scraper.yml` and modify the cron schedule:
```yaml
schedule:
  - cron: '0 6 * * *'  # 06:00 UTC daily
```

### Add Sources
Modify the `_build_sources()` method in `scraper.py` to add new sources:
```python
{
    'name': 'New Source',
    'url': f'https://example.com/bee-answers-{date_formatted}/'
}
```

### Adjust Validation
Change the minimum word count in `_validate_result()`:
```python
len(result['answers']) >= 15  # Modify this threshold
```

## Troubleshooting

### Workflow Fails
- Check repository permissions allow Actions to write
- Verify all source websites are accessible
- Review workflow logs for specific error messages

### No Data Found
- Sources may have changed their URL patterns
- Websites might be temporarily unavailable
- Try manual workflow trigger during different times

### Parse Failures
- Website HTML structure may have changed
- Add debug logging to see what content is being parsed
- Consider updating parsing patterns

## Dependencies

- `requests>=2.31.0` - HTTP client for web scraping
- `beautifulsoup4>=4.12.0` - HTML parsing and extraction

## Architecture

The system follows these design principles from the original Google Apps Script:

- **Resiliency**: Focus on getting the answer list above all else
- **Prioritization**: Most reliable sources are tried first
- **Deductive Analysis**: Programmatically determines puzzle properties
- **Graceful Fallback**: Seamless transition between sources on failure

## License

This project is open source and available under the [MIT License](LICENSE).