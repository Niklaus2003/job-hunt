# Job Agent — Project Context

## Problem Statement

Job seekers spend hours manually browsing multiple job platforms to find relevant openings. Each platform has its own UI, filters, and listing format, making it tedious to compile a unified view of available opportunities. This project automates that process.

## Goal

Build a **Python-based Job Agent** that:

1. Accepts a **job title** (e.g. "Software Engineer", "Data Analyst") as input.
2. Scrapes / fetches job listings from **three platforms**:
   - **Naukri.com** — India's largest job board → **HTML scraping** (requests + BeautifulSoup).
   - **RemoteOK** — Remote-first job board → **Public JSON API** (httpx).
   - **Wellfound** (formerly AngelList) — Startup-focused job board → **Firecrawl** (structured extraction).
3. Extracts structured data for each listing:
   - Job Title
   - Company Name
   - Location
   - Salary (if available)
   - Job URL
   - Source Platform
   - Date Scraped
4. Stores all results in a single **CSV file** for easy review, filtering, and sharing.

## Architecture Overview

```
┌─────────────────────────────────────┐
│           main.py (CLI)             │
│  - Accept job title from user       │
│  - Orchestrate scraper calls        │
│  - Merge results → CSV              │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┐
    │   scrapers/  │
    ├──────────────┤
    │ naukri.py    │  ← HTML scraping (requests + BeautifulSoup)
    │ remoteok.py  │  ← HTTP GET → JSON API
    │ wellfound.py │  ← Firecrawl (structured extraction)
    └──────────────┘
           │
    ┌──────┴──────┐
    │   utils/     │
    ├──────────────┤
    │ csv_writer.py│  ← Write/append results to CSV
    │ config.py    │  ← Shared constants & settings
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │  output/     │
    │  jobs.csv    │  ← Final consolidated output
    └──────────────┘
```

## Tech Stack

| Layer              | Tool / Library                                        |
| ------------------ | ----------------------------------------------------- |
| Language           | Python 3.12                                           |
| HTML Scraping      | `requests` + `beautifulsoup4` (for Naukri)            |
| HTTP / API Client  | `httpx` (for RemoteOK JSON API)                       |
| Web Extraction     | `firecrawl-py` (for Wellfound — handles JS rendering) |
| Data Handling      | Python `csv` module (stdlib)                          |
| CLI                | `argparse` (stdlib)                                   |

## Platform-Specific Strategy

### 1. Naukri.com — HTML Scraping
- **URL pattern:** `https://www.naukri.com/{keyword}-jobs` (e.g. `python-developer-jobs`)
- **Method:** `requests` + `BeautifulSoup` — fetch raw HTML and parse job cards.
- **Pagination:** URL query param `&page=N`.
- **Key challenge:** Frequent DOM/class-name changes; use resilient selectors. Naukri may also return partial server-rendered HTML that's enough for extraction without JS execution.

### 2. RemoteOK — Public JSON API
- **Web URL pattern:** `https://remoteok.com/remote-{keyword}-jobs` (e.g. `https://remoteok.com/remote-software-jobs`)
- **API URL pattern:** `https://remoteok.com/api?q={keyword}` (e.g. `https://remoteok.com/api?q=software`)
- **Method:** Simple HTTP GET via `httpx` — no browser needed.
- **API response:** Returns a JSON array. First element is a legal/attribution notice; remaining elements are job objects with fields like `company`, `position`, `apply_url`, `tags`, `salary_min`, `salary_max`, etc.
- **Key challenge:** Rate limiting; add polite delays.

### 3. Wellfound — Firecrawl
- **Base URL:** `https://wellfound.com/`
- **Search URL pattern:** `https://wellfound.com/role/{role-slug}` (e.g. `https://wellfound.com/role/software-engineer`)
- **Pagination:** `https://wellfound.com/role/{role-slug}?page=N` (e.g. `?page=2`)
- **Method:** `firecrawl-py` SDK — Firecrawl renders JS, bypasses anti-bot protections, and returns clean structured data (Markdown or JSON). We use `app.scrape_url()` with a schema to extract job fields directly.
- **Why Firecrawl:** Wellfound is a heavy JS SPA with aggressive anti-bot measures. Firecrawl handles rendering & extraction in one step, so we don't need to manage a local browser.
- **Requires:** A Firecrawl API key (free tier available at [firecrawl.dev](https://firecrawl.dev)).

## Output Format (CSV)

| Column         | Description                        |
| -------------- | ---------------------------------- |
| `title`        | Job title as listed                |
| `company`      | Company name                       |
| `location`     | Job location or "Remote"           |
| `salary`       | Salary range (if available)        |
| `url`          | Direct link to the job posting     |
| `source`       | Platform name (naukri / remoteok / wellfound) |
| `scraped_at`   | ISO timestamp of when it was scraped |

## Project Structure

```
job_agent/
├── context.md              # This file — project context
├── docs/                   # Additional documentation
├── main.py                 # Entry point — CLI + orchestration
├── scrapers/
│   ├── __init__.py
│   ├── base.py             # Abstract base scraper class
│   ├── naukri.py            # Naukri.com scraper
│   ├── remoteok.py          # RemoteOK scraper
│   └── wellfound.py         # Wellfound scraper
├── utils/
│   ├── __init__.py
│   ├── csv_writer.py        # CSV output helper
│   └── config.py            # Shared settings
├── output/                  # Generated CSV files land here
├── requirements.txt         # Python dependencies
└── .gitignore
```

## Key Dependencies

```
requests
beautifulsoup4
httpx
firecrawl-py
```

## Usage (Planned)

```bash
# Install dependencies
pip install -r requirements.txt

# Set Firecrawl API key (needed for Wellfound scraper)
set FIRECRAWL_API_KEY=fc-your-key-here   # Windows
# export FIRECRAWL_API_KEY=fc-your-key-here  # macOS/Linux

# Run the agent
python main.py --title "Software Engineer"

# Output
# → output/jobs_software_engineer_2026-05-17.csv
```

## Constraints & Considerations

- **Rate Limiting:** Add random delays (2–5 s) between requests to avoid IP bans.
- **Firecrawl API Key:** Required for the Wellfound scraper; store in `.env` or environment variable — never commit to git.
- **Robustness:** Wrap all extraction in try/except — if one field fails, skip it gracefully.
- **Respect robots.txt:** This tool is for personal/educational use only.
- **No PII collection:** We only scrape publicly visible job metadata, not user/recruiter data.
