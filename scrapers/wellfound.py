"""
Wellfound scraper — uses Firecrawl for structured extraction.
Firecrawl handles JS rendering and anti-bot measures so we don't need
a local browser.
"""

import time
import random

from firecrawl import FirecrawlApp

from scrapers.base import BaseScraper
from utils.config import (
    FIRECRAWL_API_KEY,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
)


class WellfoundScraper(BaseScraper):
    """Scrape job listings from Wellfound using Firecrawl's extract API."""

    BASE_URL = "https://wellfound.com"
    SOURCE = "wellfound"

    # Schema that tells Firecrawl what to extract from the page
    EXTRACT_SCHEMA = {
        "type": "object",
        "properties": {
            "jobs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Job title"},
                        "company": {"type": "string", "description": "Company name"},
                        "location": {"type": "string", "description": "Job location"},
                        "salary": {"type": "string", "description": "Salary or compensation range if available"},
                        "url": {"type": "string", "description": "Direct URL to the job posting"},
                    },
                },
            }
        },
    }

    EXTRACT_PROMPT = (
        "Extract all job listings from this page. "
        "For each job, get the title, company name, location, salary (if shown), "
        "and the direct URL to the job posting. "
        "If the URL is relative, prepend 'https://wellfound.com'."
    )

    def __init__(self, job_title: str, pages: int = 2, location: str | None = None, experience: str | None = None):
        super().__init__(job_title, pages, location, experience)
        
        self.extract_prompt = self.EXTRACT_PROMPT
        if self.experience:
            self.extract_prompt += f" Only include jobs suitable for someone with {self.experience} years of experience."

        if not FIRECRAWL_API_KEY:
            raise ValueError(
                "FIRECRAWL_API_KEY is not set. "
                "Get a free key at https://firecrawl.dev and add it to your .env file."
            )

        self.app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    def _build_search_url(self, role_slug: str, page: int) -> str:
        """Build the Wellfound role URL with optional pagination and location."""
        if self.location:
            loc_slug = self._slugify(self.location)
            url = f"{self.BASE_URL}/role/l/{role_slug}/{loc_slug}"
            if page > 1:
                url += f"?page={page}"
            return url
            
        url = f"{self.BASE_URL}/role/{role_slug}"
        if page > 1:
            url += f"?page={page}"
        return url

    def _extract_jobs_from_page(self, url: str) -> list[dict]:
        """Use Firecrawl to scrape a single Wellfound page and extract jobs."""
        jobs: list[dict] = []

        try:
            result = self.app.extract(
                urls=[url],
                prompt=self.extract_prompt,
                schema=self.EXTRACT_SCHEMA,
            )

            # Firecrawl v2 returns the extracted structure under .data or .extract
            extracted = None
            if hasattr(result, "data") and getattr(result, "data") is not None:
                extracted = result.data
            elif hasattr(result, "extract") and getattr(result, "extract") is not None:
                extracted = result.extract
            elif isinstance(result, dict):
                extracted = result.get("data") or result.get("extract", {})

            if not extracted:
                print(f"     ⚠ No data extracted from {url}")
                return jobs

            # Handle case where extracted is a string (some older versions returned raw JSON string)
            if isinstance(extracted, str):
                import json
                try:
                    extracted = json.loads(extracted)
                except Exception:
                    pass

            job_list = extracted.get("jobs", []) if isinstance(extracted, dict) else []

            for item in job_list:
                try:
                    job_url = item.get("url", "")
                    # Ensure absolute URL
                    if job_url and not job_url.startswith("http"):
                        job_url = f"{self.BASE_URL}{job_url}"

                    record = self._build_job_record(
                        title=item.get("title", ""),
                        company=item.get("company", ""),
                        location=item.get("location", ""),
                        salary=item.get("salary", ""),
                        url=job_url,
                        source=self.SOURCE,
                    )
                    jobs.append(record)
                except Exception as e:
                    print(f"     ⚠ Wellfound: skipping one listing — {e}")
                    continue

        except Exception as e:
            print(f"  ✗ Wellfound Firecrawl error for {url}: {e}")

        return jobs

    def scrape(self) -> list[dict]:
        """
        Scrape multiple pages of Wellfound role listings via Firecrawl.
        Returns a combined list of job-record dicts.
        """
        role_slug = self._slugify(self.job_title)
        all_jobs: list[dict] = []

        loc_str = f" in '{self.location}'" if self.location else ""
        print(f"  🔍 Wellfound: searching for '{self.job_title}'{loc_str} ({self.pages} pages) ...")

        for page in range(1, self.pages + 1):
            url = self._build_search_url(role_slug, page)
            print(f"     Page {page}: {url}")

            page_jobs = self._extract_jobs_from_page(url)
            all_jobs.extend(page_jobs)
            print(f"     → {len(page_jobs)} jobs found on page {page}")

            # Polite delay between pages
            if page < self.pages:
                time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

        print(f"  ✓ Wellfound: found {len(all_jobs)} jobs total")
        return all_jobs
