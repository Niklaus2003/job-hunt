# 🤖 Job Hunt Agent

A resilient and modern Python-based job aggregator that collects, standardizes, and consolidates job listings from **Naukri**, **RemoteOK**, and **Wellfound** into a unified, formatted CSV report.

Designed with advanced scraping strategies to bypass modern anti-bot systems (like Akamai Bot Manager) and handle complex client-side rendered Single Page Applications (SPAs).

---

## 🎯 Features

- **Interactive Mode:** Run the script without arguments and it will intuitively ask for Job Role, Location, and Years of Experience.
- **Experience Filtering:** Automatically injects your experience requirements into platform-specific filters (e.g. Naukri URL parameters, Wellfound AI extraction instructions).
- **Multi-Source Aggregation:** Pulls postings simultaneously from:
  - **RemoteOK:** Native, high-performance JSON API.
  - **Naukri.com:** Bypasses advanced Akamai Bot Manager security and Next.js skeleton loaders using a stealth-configured local desktop browser (Playwright) parsed with BeautifulSoup.
  - **Wellfound:** AI-powered structured JSON extraction using Firecrawl to bypass heavy JS rendering and anti-bot measures.
- **Unified Schema:** Automatically normalizes diverse fields into a clean consolidated CSV:
  `[title, company, location, salary, url, source, scraped_at]`
- **Robust Orchestration:** Features per-scraper isolation, delay-politeness, custom paging, and error handling (so one platform failing won't crash the entire run).

---

## 🏗 Project Structure

```text
job_agent/
├── scrapers/              # Platform-specific scraper implementations
│   ├── __init__.py        # Exposes scraper classes
│   ├── base.py            # Abstract Base Scraper class
│   ├── naukri.py          # Playwright + BeautifulSoup parser
│   ├── remoteok.py        # HTTPX API consumer
│   └── wellfound.py       # Firecrawl extractor
├── utils/                 # Utility helpers
│   ├── config.py          # Project config loader
│   └── csv_writer.py      # Output CSV formatting & creation
├── output/                # Generated CSV job reports (auto-created)
├── main.py                # Command Line entry point
├── requirements.txt       # Python dependency definitions
└── .env.example           # Environment template file
```

---

## 🚀 Installation & Setup

### 1. Clone & Set Up Environment

Ensure Python 3.10+ is installed on your system.

```powershell
# Clone the repository
git clone https://github.com/Niklaus2003/job-hunt.git
cd job-hunt

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install Playwright Chromium dependencies (required for Naukri)
python -m playwright install chromium
```

### 2. Configure Environment Variables

Duplicate the template and rename to `.env`:

```powershell
copy .env.example .env
```

Open `.env` and configure your API keys:

```ini
# Required if you want to run Wellfound scraping
FIRECRAWL_API_KEY=fc-your-key-here
```

---

## 💻 Usage

Run the agent from the command line using `main.py`:

### 1. Interactive Mode (Recommended)

Simply run the script without any arguments to trigger the interactive prompts:

```powershell
python main.py
```
*You will be prompted to enter:*
- Job Role (e.g. Software Engineer)
- Location (e.g. Bangalore)
- Years of Experience (e.g. 2)

### 2. Natural Language Search (Auto-extracts Job Title and Location)

```powershell
python main.py --query "Find product manager roles in Bangalore"
```
This parses the query automatically to extract:
* **Job Title:** `product manager`
* **Location:** `Bangalore`

### 3. Explicit Search with Arguments

```powershell
python main.py --title "Data Analyst" --location "Pune" --experience "3" --sources naukri,remoteok --pages 1
```

### 4. View Command Line Options

```powershell
python main.py --help
```

---

## 📊 Output File Example

Consolidated job results are written directly to `output/jobs_[job_title]_[date].csv`.

| title | company | location | salary | url | source | scraped_at |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Python Developer | Persistent | Pune | Not disclosed | "https://naukri.com/..." | naukri | 2026-05-17T10:51:06 |
| IT Support | Avalere Health | Remote | | "https://remoteok.com/..." | remoteok | 2026-05-17T10:24:44 |

---

## 🛡 Scraping Strategies Explained

1. **RemoteOK:** Uses standard REST API requesting utilizing custom user agents and clean HTTP response handlers.
2. **Naukri:** Launches Playwright in non-headless mode to completely simulate human presence. This is necessary because Akamai Bot Manager automatically blocks standard HTTP request client libraries and headless browsers with a `403/406 Access Denied` response. Playwright handles client-side React rendering, and results are scraped using BeautifulSoup. Experience filters are injected dynamically into the URL payload.
3. **Wellfound:** Employs Firecrawl's advanced extraction endpoints to bypass aggressive cloudflare protections and utilizes AI schemas to extract beautifully structured job arrays, dynamically adapting to requested experience levels.
