"""
Job Agent — CLI entry point.

Scrapes job listings from Naukri, RemoteOK, and Wellfound,
then writes all results to a single CSV file.

Usage:
    python main.py --title "Software Engineer"
    python main.py --title "Data Analyst" --sources remoteok,naukri
    python main.py --title "Frontend Developer" --pages 3
"""

import argparse
import sys
import time

from scrapers.remoteok import RemoteOKScraper
from scrapers.naukri import NaukriScraper
from scrapers.wellfound import WellfoundScraper
from utils.csv_writer import write_jobs_to_csv


# Map of source names to their scraper classes
SCRAPERS = {
    "remoteok": RemoteOKScraper,
    "naukri": NaukriScraper,
    "wellfound": WellfoundScraper,
}


import re

def parse_natural_query(query: str) -> tuple[str, str | None]:
    """
    Parse a query like 'Find product manager roles in Bangalore' or 'software engineer in Pune'
    Returns a tuple of (job_title, location).
    """
    query = query.strip()
    
    # Patterns like: "Find <title> roles/jobs in <location>", "<title> in <location>", "<title> jobs in <location>"
    # Matches: (optional Find/Search for) <title> (optional roles/jobs/listings) in/at <location>
    pattern = re.compile(
        r'^(?:find|search\s+for|get)?\s*(.*?)\s*(?:roles|jobs|listings)?\s+(?:in|at)\s+(.+)$',
        re.IGNORECASE
    )
    
    match = pattern.match(query)
    if match:
        title = match.group(1).strip()
        location = match.group(2).strip()
        # Clean up potential leading/trailing articles or helper words
        title = re.sub(r'^(?:a|an|the)\s+', '', title, flags=re.IGNORECASE)
        return title, location
        
    return query, None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Job Agent — scrape jobs from Naukri, RemoteOK & Wellfound",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --query \"Find product manager roles in Bangalore\"\n"
            "  python main.py --title \"Software Engineer\" --location \"Pune\"\n"
            "  python main.py --title \"Data Analyst\" --sources remoteok,naukri\n"
            "  python main.py --title \"Frontend Developer\" --pages 3\n"
        ),
    )
    parser.add_argument(
        "--query",
        help="Natural language search query (e.g. 'Find product manager roles in Bangalore')",
    )
    parser.add_argument(
        "--title",
        help="Job title to search for (explicitly set or overrides query)",
    )
    parser.add_argument(
        "--location",
        help="Job location to search for (explicitly set or overrides query)",
    )
    parser.add_argument(
        "--experience",
        help="Years of experience to search for",
    )
    parser.add_argument(
        "--sources",
        default="naukri,remoteok,wellfound",
        help="Comma-separated list of sources to scrape (default: all three)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=2,
        help="Number of pages to scrape per source (default: 2)",
    )
    return parser.parse_args()


def main():
    """Main entry point — orchestrate scrapers and write CSV."""
    args = parse_args()

    title = args.title
    location = args.location

    experience = args.experience

    # Parse natural language query if provided
    if args.query:
        parsed_title, parsed_location = parse_natural_query(args.query)
        if not title:
            title = parsed_title
        if not location:
            location = parsed_location

    # Interactive prompt if no title is provided
    if not title and not args.query:
        print("Welcome to Job Agent! Please enter search details below:")
        title = input("Enter job role (e.g. Software Engineer): ").strip()
        if not title:
            print("  ✗ Error: Job role is required.")
            sys.exit(1)
        
        loc_input = input("Enter location (e.g. Bangalore, leave blank for Remote): ").strip()
        if loc_input and not location:
            location = loc_input
            
        exp_input = input("Enter years of experience (e.g. 2, leave blank if not applicable): ").strip()
        if exp_input and not experience:
            experience = exp_input

    sources = [s.strip().lower() for s in args.sources.split(",")]
    pages = args.pages

    print()
    print("=" * 60)
    print(f"  🤖 Job Agent — Searching for: {title}")
    if location:
        print(f"  📍 Location: {location}")
    if experience:
        print(f"  📈 Experience: {experience} years")
    print(f"  📋 Sources: {', '.join(sources)}")
    print(f"  📄 Pages per source: {pages}")
    print("=" * 60)
    print()

    all_jobs: list[dict] = []
    start_time = time.time()

    for source_name in sources:
        if source_name not in SCRAPERS:
            print(f"  ✗ Unknown source '{source_name}' — skipping.")
            print(f"    Valid sources: {', '.join(SCRAPERS.keys())}")
            print()
            continue

        scraper_class = SCRAPERS[source_name]

        try:
            scraper = scraper_class(job_title=title, pages=pages, location=location, experience=experience)
            jobs = scraper.scrape()
            all_jobs.extend(jobs)
        except ValueError as e:
            # e.g. missing API key for Wellfound
            print(f"  ✗ {source_name}: {e}")
        except Exception as e:
            print(f"  ✗ {source_name} failed: {e}")

        print()

    # Write results to CSV
    elapsed = round(time.time() - start_time, 1)

    if all_jobs:
        filepath = write_jobs_to_csv(all_jobs, title)
        print("=" * 60)
        print(f"  ✅ Done! Saved {len(all_jobs)} jobs to:")
        print(f"     {filepath}")
        print(f"  ⏱  Completed in {elapsed}s")
        print("=" * 60)
    else:
        filepath = write_jobs_to_csv([], title)
        print("=" * 60)
        print(f"  ⚠  No jobs found across any source.")
        print(f"     Empty CSV created at: {filepath}")
        print(f"  ⏱  Completed in {elapsed}s")
        print("=" * 60)


if __name__ == "__main__":
    main()
