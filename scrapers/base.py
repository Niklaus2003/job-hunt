"""
Abstract base class for all job scrapers.
Provides common helpers so each platform scraper only needs to implement scrape().
"""

import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class BaseScraper(ABC):
    """Base class that every platform scraper must extend."""

    def __init__(self, job_title: str, pages: int = 2, location: str | None = None, experience: str | None = None):
        self.job_title = job_title
        self.pages = pages
        self.location = location
        self.experience = experience

    # ------------------------------------------------------------------
    # Abstract — each subclass must implement this
    # ------------------------------------------------------------------
    @abstractmethod
    def scrape(self) -> list[dict]:
        """Scrape the platform and return a list of job-record dicts."""
        ...

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_job_record(
        title: str,
        company: str,
        location: str,
        salary: str,
        url: str,
        source: str,
    ) -> dict:
        """Create a standardised job-record dict with a scraped_at timestamp."""
        return {
            "title": (title or "").strip(),
            "company": (company or "").strip(),
            "location": (location or "").strip(),
            "salary": (salary or "").strip(),
            "url": (url or "").strip(),
            "source": source,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _slugify(text: str) -> str:
        """
        Convert a human-readable job title into a URL-friendly slug.
        Example: 'Software Engineer' → 'software-engineer'
        """
        text = text.strip().lower()
        text = re.sub(r"[^a-z0-9\s-]", "", text)
        text = re.sub(r"[\s]+", "-", text)
        return text
