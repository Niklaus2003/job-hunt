"""
Naukri.com scraper — HTML scraping with Playwright (Stealth Mode) + BeautifulSoup.
Uses headless Chromium with advanced stealth settings to bypass Akamai Bot Manager and render job cards,
then parses the fully-rendered HTML using BeautifulSoup selectors.
"""

import time
import random

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from scrapers.base import BaseScraper
from utils.config import REQUEST_DELAY_MIN, REQUEST_DELAY_MAX


class NaukriScraper(BaseScraper):
    """Scrape job listings from Naukri.com via client-rendered HTML parsing under Stealth."""

    BASE_URL = "https://www.naukri.com"
    SOURCE = "naukri"

    def _build_search_url(self, keyword: str, page: int) -> str:
        """
        Build the Naukri search URL for a given keyword, location, and page number.
        Without location:
            Page 1: /python-developer-jobs
            Page 2: /python-developer-jobs-2
        With location:
            Page 1: /python-developer-jobs-in-bangalore
            Page 2: /python-developer-jobs-in-bangalore-2
        """
        slug = keyword
        url = ""
        if self.location:
            loc_slug = self._slugify(self.location)
            if page == 1:
                url = f"{self.BASE_URL}/{slug}-jobs-in-{loc_slug}"
            else:
                url = f"{self.BASE_URL}/{slug}-jobs-in-{loc_slug}-{page}"
        else:
            if page == 1:
                url = f"{self.BASE_URL}/{slug}-jobs"
            else:
                url = f"{self.BASE_URL}/{slug}-jobs-{page}"
        
        if self.experience:
            url += f"?experience={self.experience}"
            
        return url

    def _parse_page(self, html: str) -> list[dict]:
        """Parse a single page of Naukri HTML and extract job records."""
        soup = BeautifulSoup(html, "html.parser")
        jobs: list[dict] = []

        # Each job card is inside a div with class 'srp-jobtuple-wrapper'
        cards = soup.select("div.srp-jobtuple-wrapper")

        for card in cards:
            try:
                # Job title & URL
                title_tag = card.select_one("a.title")
                title = title_tag.get_text(strip=True) if title_tag else ""
                url = title_tag.get("href", "") if title_tag else ""

                # Company name
                company_tag = card.select_one("a.comp-name")
                company = company_tag.get_text(strip=True) if company_tag else ""

                # Location
                loc_tag = card.select_one("span.loc-wrap")
                location = loc_tag.get_text(strip=True) if loc_tag else ""

                # Salary (may not exist)
                sal_tag = card.select_one("span.sal-wrap")
                salary = sal_tag.get_text(strip=True) if sal_tag else "Not disclosed"

                if not title:
                    continue

                record = self._build_job_record(
                    title=title,
                    company=company,
                    location=location,
                    salary=salary,
                    url=url,
                    source=self.SOURCE,
                )
                jobs.append(record)

            except Exception as e:
                print(f"  ⚠ Naukri: skipping one card — {e}")
                continue

        return jobs

    def scrape(self) -> list[dict]:
        """
        Scrape multiple pages of Naukri search results using a Stealth Playwright headless browser.
        Returns a combined list of job-record dicts.
        """
        keyword = self._slugify(self.job_title)
        all_jobs: list[dict] = []

        loc_str = f" in '{self.location}'" if self.location else ""
        print(f"  🔍 Naukri: searching for '{self.job_title}'{loc_str} ({self.pages} pages) ...")

        with sync_playwright() as p:
            # Launch Chromium with stealth arguments
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                ]
            )
            # Create a context with realistic headers and fingerprints
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone_id="Asia/Kolkata",
            )
            
            page_obj = context.new_page()
            
            # Inject stealth script to remove webdriver trace
            page_obj.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            for page in range(1, self.pages + 1):
                url = self._build_search_url(keyword, page)
                print(f"     Page {page}: {url}")

                try:
                    # Navigate to search page
                    page_obj.goto(url, wait_until="domcontentloaded", timeout=45000)
                    
                    # Wait for job wrapper cards to render in DOM
                    page_obj.wait_for_selector("div.srp-jobtuple-wrapper", timeout=20000)
                    
                    # Get fully rendered HTML
                    html = page_obj.content()
                except Exception as e:
                    print(f"  ✗ Naukri page {page} failed to load/render: {e}")
                    # Diagnostic dump on failure
                    try:
                        screenshot_path = f"naukri_page_{page}_fail.png"
                        page_obj.screenshot(path=screenshot_path)
                        print(f"     [DEBUG] Screenshot saved to: {screenshot_path}")
                        with open(f"naukri_page_{page}_fail.html", "w", encoding="utf-8") as f:
                            f.write(page_obj.content())
                        print(f"     [DEBUG] HTML source saved to: naukri_page_{page}_fail.html")
                    except Exception as debug_err:
                        print(f"     [DEBUG] Could not save diagnostic files: {debug_err}")
                    continue

                page_jobs = self._parse_page(html)
                all_jobs.extend(page_jobs)
                print(f"     → {len(page_jobs)} jobs found on page {page}")

                # Polite delay between pages
                if page < self.pages:
                    time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

            browser.close()

        print(f"  ✓ Naukri: found {len(all_jobs)} jobs total")
        return all_jobs
