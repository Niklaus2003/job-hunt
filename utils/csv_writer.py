"""
CSV writer utility for the Job Agent.
Writes a list of job records to a timestamped CSV file.
"""

import csv
from datetime import datetime
from pathlib import Path

from utils.config import OUTPUT_DIR, CSV_COLUMNS


def write_jobs_to_csv(jobs: list[dict], title: str) -> str:
    """
    Write job records to a CSV file in the output/ directory.

    Args:
        jobs:  List of job dicts (keys must match CSV_COLUMNS).
        title: The job title that was searched (used in the filename).

    Returns:
        The absolute path to the created CSV file.
    """
    # Build a filename-safe slug from the job title
    slug = title.strip().lower().replace(" ", "_")
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"jobs_{slug}_{date_str}.csv"
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()

        if not jobs:
            print("  ⚠  No jobs to write — CSV created with headers only.")
        else:
            writer.writerows(jobs)

    return str(filepath)
