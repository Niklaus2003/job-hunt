"""
Streamlit frontend for the Job Agent project.

This app reuses the existing scraper classes and writes consolidated results to CSV.
"""

import csv
import io
from pathlib import Path
from typing import Any

import streamlit as st
from scrapers.naukri import NaukriScraper
from scrapers.remoteok import RemoteOKScraper
from scrapers.wellfound import WellfoundScraper
from utils.csv_writer import write_jobs_to_csv
from utils.config import CSV_COLUMNS

SCRAPERS = {
    "remoteok": RemoteOKScraper,
    "naukri": NaukriScraper,
    "wellfound": WellfoundScraper,
}


def build_csv_bytes(jobs: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore", quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(jobs)
    return buffer.getvalue().encode("utf-8")


def search_jobs(title: str, location: str | None, experience: str | None, sources: list[str], pages: int) -> None:
    all_jobs: list[dict[str, Any]] = []
    errors: list[str] = []

    for source_name in sources:
        if source_name not in SCRAPERS:
            errors.append(f"Unknown source: {source_name}")
            continue

        scraper_class = SCRAPERS[source_name]
        try:
            scraper = scraper_class(job_title=title, pages=pages, location=location, experience=experience)
            jobs = scraper.scrape()
            all_jobs.extend(jobs)
            st.write(f"Source: {source_name} — {len(jobs)} jobs found")
        except ValueError as exc:
            errors.append(f"{source_name}: {exc}")
        except Exception as exc:  # pragma: no cover
            errors.append(f"{source_name} failed: {exc}")

    if errors:
        for message in errors:
            st.error(message)

    if not all_jobs:
        st.warning("No jobs were found for the selected criteria.")
        write_jobs_to_csv([], title)
        return

    st.success(f"Found {len(all_jobs)} jobs across {len(sources)} source(s).")
    st.dataframe(all_jobs, use_container_width=True)

    csv_bytes = build_csv_bytes(all_jobs)
    path = write_jobs_to_csv(all_jobs, title)

    st.markdown(f"**Saved CSV file:** `{path}`")
    st.download_button(
        label="Download results as CSV",
        data=csv_bytes,
        file_name=Path(path).name,
        mime="text/csv",
    )


def main() -> None:
    st.set_page_config(page_title="Job Agent", page_icon="🤖", layout="wide")
    st.title("🤖 Job Agent — Streamlit Frontend")
    st.write(
        "Use this frontend to search jobs across Naukri, RemoteOK, and Wellfound, then export the consolidated results to CSV."
    )

    with st.sidebar:
        st.header("Search options")
        title = st.text_input("Job title", placeholder="Software Engineer")
        location = st.text_input("Location (optional)", placeholder="Bangalore")
        experience = st.text_input("Years of experience (optional)", placeholder="2")
        sources = st.multiselect(
            "Sources",
            options=list(SCRAPERS.keys()),
            default=list(SCRAPERS.keys()),
        )
        pages = st.slider("Pages per source", min_value=1, max_value=5, value=2)
        search_button = st.button("Search jobs")

    if search_button:
        if not title.strip():
            st.error("Job title is required.")
            return

        with st.spinner("Scraping jobs. This may take a few minutes..."):
            search_jobs(
                title=title.strip(),
                location=location.strip() or None,
                experience=experience.strip() or None,
                sources=sources,
                pages=pages,
            )

    st.markdown("---")
    st.markdown(
        "If you are using Naukri scraping, ensure the required Playwright dependencies are installed and `.env` contains any needed API keys for Wellfound."
    )


if __name__ == "__main__":
    main()
