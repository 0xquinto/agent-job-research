import csv
import tempfile
from pathlib import Path

from board_aggregator.models import JobPosting
from board_aggregator.output import write_csv, write_markdown


SAMPLE_JOBS = [
    JobPosting(
        title="AI Engineer",
        company="Grafana Labs",
        source="indeed",
        job_url="https://indeed.com/viewjob?jk=abc",
        location="Remote, US",
        salary_min=154000,
        salary_max=185000,
        date_posted="2026-03-27",
        job_type="fulltime",
        description="Build AI/ML ops tooling...",
    ),
    JobPosting(
        title="Rust Developer",
        company="NXLog",
        source="himalayas",
        job_url="https://himalayas.app/jobs/rust-dev",
        location="Remote",
    ),
]


def test_write_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = Path(f.name)

    write_csv(SAMPLE_JOBS, path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["title"] == "AI Engineer"
    assert rows[0]["company"] == "Grafana Labs"
    assert rows[0]["salary_min"] == "154000"
    assert rows[1]["salary_min"] == ""
    path.unlink()


def test_write_markdown():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = Path(f.name)

    write_markdown(SAMPLE_JOBS, path)

    content = path.read_text()
    assert "# Phase 1: Job Board Scrape Results" in content
    assert "## AI Engineer" in content
    assert "Grafana Labs" in content
    assert "$154,000 - $185,000" in content or "154000" in content
    assert "## Rust Developer" in content
    path.unlink()
