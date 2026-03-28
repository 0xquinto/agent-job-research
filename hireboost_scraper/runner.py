from pathlib import Path

from hireboost_scraper.models import JobPosting
from hireboost_scraper.output import write_csv, write_markdown
from hireboost_scraper.scrapers import get_all_scrapers


def deduplicate(jobs: list[JobPosting]) -> list[JobPosting]:
    """Deduplicate by (title, company), keeping the version with most data."""
    seen: dict[tuple[str, str], JobPosting] = {}

    for job in jobs:
        key = job.dedup_key
        if key not in seen:
            seen[key] = job
        else:
            existing = seen[key]
            if _richness(job) > _richness(existing):
                seen[key] = job

    return list(seen.values())


def _richness(job: JobPosting) -> int:
    """Score how much data a posting has. Higher = more complete."""
    score = 0
    if job.salary_min is not None:
        score += 3
    if job.salary_max is not None:
        score += 3
    if job.description:
        score += 2
    if job.date_posted:
        score += 1
    if job.job_type:
        score += 1
    return score


def run_all(
    queries: list[str],
    output_dir: Path,
    is_remote: bool = True,
    scrapers: list[str] | None = None,
) -> list[JobPosting]:
    """Run all registered scrapers, deduplicate, and write output."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_jobs: list[JobPosting] = []
    available = get_all_scrapers()

    for scraper in available:
        if scrapers and scraper.name not in scrapers:
            continue

        print(f"[runner] Scraping {scraper.name}...")
        try:
            jobs = scraper.scrape(queries, is_remote=is_remote)
            print(f"[runner] {scraper.name}: {len(jobs)} results")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[runner] {scraper.name} failed: {e}")

    print(f"[runner] Total before dedup: {len(all_jobs)}")
    unique_jobs = deduplicate(all_jobs)
    print(f"[runner] Total after dedup: {len(unique_jobs)}")

    write_csv(unique_jobs, output_dir / "all-postings.csv")
    write_markdown(unique_jobs, output_dir / "all-postings.md")

    return unique_jobs
