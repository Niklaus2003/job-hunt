"""
RemoteOK scraper — fetches jobs from the public JSON API.
No browser or API key required.
"""

import time
import random

import httpx

from scrapers.base import BaseScraper
from utils.config import USER_AGENT, REQUEST_DELAY_MIN, REQUEST_DELAY_MAX


class RemoteOKScraper(BaseScraper):
    """Scrape remote job listings from remoteok.com via its public API."""

    API_URL = "https://remoteok.com/api"
    SOURCE = "remoteok"

    def scrape(self) -> list[dict]:
        """
        Hit the RemoteOK JSON API, filter by job title keyword,
        and return a list of job-record dicts.
        """
        keyword = self._slugify(self.job_title)
        url = f"{self.API_URL}?q={keyword}"
        jobs: list[dict] = []

        loc_str = f" in '{self.location}'" if self.location else ""
        print(f"  🔍 RemoteOK: searching for '{self.job_title}'{loc_str} ...")

        try:
            headers = {"User-Agent": USER_AGENT}
            response = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"  ✗ RemoteOK HTTP error: {e.response.status_code}")
            return jobs
        except httpx.RequestError as e:
            print(f"  ✗ RemoteOK request failed: {e}")
            return jobs
        except Exception as e:
            print(f"  ✗ RemoteOK unexpected error: {e}")
            return jobs

        # First element is a legal/attribution notice — skip it
        listings = data[1:] if len(data) > 1 else []

        for item in listings:
            try:
                position = item.get("position", "")
                company = item.get("company", "")
                location = item.get("location", "Remote")
                
                # Build salary string from min/max if available
                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                if salary_min and salary_max:
                    salary = f"${salary_min:,} – ${salary_max:,}"
                elif salary_min:
                    salary = f"${salary_min:,}+"
                else:
                    salary = ""

                job_id = item.get("id")
                if job_id:
                    job_url = f"https://remoteok.com/remote-jobs/{job_id}"
                else:
                    job_slug = item.get("slug", "")
                    job_url = item.get("apply_url") or item.get("url") or f"https://remoteok.com/remote-jobs/{job_slug}"
                    if job_url:
                        job_url = job_url.replace("remoteOK.com", "remoteok.com")

                record = self._build_job_record(
                    title=position,
                    company=company,
                    location=location or "Remote",
                    salary=salary,
                    url=job_url,
                    source=self.SOURCE,
                )
                jobs.append(record)

            except Exception as e:
                print(f"  ⚠ RemoteOK: skipping one listing — {e}")
                continue

        if self.location:
            loc_lower = self.location.lower()
            filtered_jobs = []
            for j in jobs:
                job_loc = j["location"].lower()
                if loc_lower in job_loc or "remote" in job_loc or "worldwide" in job_loc:
                    filtered_jobs.append(j)
            jobs = filtered_jobs

        print(f"  ✓ RemoteOK: found {len(jobs)} jobs")

        # Polite delay
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

        return jobs
