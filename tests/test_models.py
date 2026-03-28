from board_aggregator.models import JobPosting


def test_job_posting_minimal():
    job = JobPosting(
        title="AI Engineer",
        company="Acme Corp",
        source="himalayas",
        job_url="https://example.com/job/1",
    )
    assert job.title == "AI Engineer"
    assert job.company == "Acme Corp"
    assert job.source == "himalayas"
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.is_remote is True  # default


def test_job_posting_full():
    job = JobPosting(
        title="Operations Manager",
        company="Grafana Labs",
        source="indeed",
        job_url="https://indeed.com/viewjob?jk=abc123",
        location="Remote, US",
        is_remote=True,
        salary_min=150000,
        salary_max=200000,
        salary_currency="USD",
        salary_interval="yearly",
        date_posted="2026-03-27",
        job_type="fulltime",
        description="Lead AI operations...",
    )
    assert job.salary_min == 150000
    assert job.salary_currency == "USD"
    assert job.date_posted == "2026-03-27"


def test_job_posting_dedup_key():
    job = JobPosting(
        title="AI Engineer",
        company="Acme Corp",
        source="himalayas",
        job_url="https://example.com/job/1",
    )
    key = job.dedup_key
    assert key == ("ai engineer", "acme corp")


def test_job_posting_dedup_key_normalizes():
    job1 = JobPosting(title="AI Engineer ", company="  Acme Corp", source="a", job_url="https://x.com/1")
    job2 = JobPosting(title="ai engineer", company="acme corp", source="b", job_url="https://x.com/2")
    assert job1.dedup_key == job2.dedup_key


# --- Task 2: Base class tests ---

from board_aggregator.scrapers.base import BaseScraper


def test_base_scraper_is_abstract():
    import pytest

    with pytest.raises(TypeError):
        BaseScraper()


class DummyScraper(BaseScraper):
    name = "dummy"

    def scrape(self, queries, is_remote=True):
        return [
            JobPosting(
                title="Test Job",
                company="Test Co",
                source=self.name,
                job_url="https://example.com/1",
            )
        ]


def test_dummy_scraper_works():
    s = DummyScraper()
    results = s.scrape(["test query"])
    assert len(results) == 1
    assert results[0].source == "dummy"
