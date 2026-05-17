"""
Shared configuration for the Job Agent.
Loads environment variables and defines constants used across all scrapers.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Request settings
# ---------------------------------------------------------------------------
REQUEST_DELAY_MIN = 2   # seconds
REQUEST_DELAY_MAX = 5   # seconds

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# ---------------------------------------------------------------------------
# Scraper defaults
# ---------------------------------------------------------------------------
DEFAULT_PAGES = 2  # number of pages to scrape per source

# CSV column order
CSV_COLUMNS = ["title", "company", "location", "salary", "url", "source", "scraped_at"]
