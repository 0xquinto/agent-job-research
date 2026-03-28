import csv
from collections import Counter
from datetime import date
from pathlib import Path

from hireboost_scraper.models import JobPosting

CSV_FIELDS = [
    "title", "company", "source", "job_url", "location", "is_remote",
    "salary_min", "salary_max", "salary_currency", "salary_interval",
    "date_posted", "job_type", "description",
]


def _csv_value(val):
    """Convert value for CSV: None -> '', float whole numbers -> int string."""
    if val is None:
        return ""
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return val


def write_csv(jobs: list[JobPosting], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for job in jobs:
            row = job.model_dump()
            writer.writerow({k: _csv_value(row.get(k)) for k in CSV_FIELDS})


def write_markdown(jobs: list[JobPosting], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    source_counts = Counter(j.source for j in jobs)
    source_summary = ", ".join(f"{src}: {cnt}" for src, cnt in source_counts.most_common())

    lines: list[str] = []
    lines.append("# Phase 1: Job Board Scrape Results")
    lines.append(f"**Date:** {date.today().isoformat()}")
    lines.append(f"**Total Postings (unique after dedup):** {len(jobs)}")
    lines.append(f"**By Board:** {source_summary}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for job in jobs:
        lines.append(f"## {job.title} -- {job.company}")
        lines.append(f"- **Source:** {job.source}")
        lines.append(f"- **Location:** {job.location or 'Remote'}")
        lines.append(f"- **Is Remote:** {job.is_remote}")

        if job.salary_min and job.salary_max:
            lines.append(
                f"- **Salary:** ${job.salary_min:,.0f} - ${job.salary_max:,.0f} {job.salary_currency} ({job.salary_interval})"
            )
        elif job.salary_min:
            lines.append(f"- **Salary:** ${job.salary_min:,.0f}+ {job.salary_currency}")
        else:
            lines.append("- **Salary:** Not listed")

        lines.append(f"- **URL:** {job.job_url}")
        if job.date_posted:
            lines.append(f"- **Date Posted:** {job.date_posted}")
        if job.job_type:
            lines.append(f"- **Job Type:** {job.job_type}")
        if job.description:
            lines.append(f"- **Description:** {job.description[:300]}")
        lines.append("---")
        lines.append("")

    path.write_text("\n".join(lines))
