from hireboost_scraper.models import JobPosting
from hireboost_scraper.runner import deduplicate


def test_deduplicate_by_title_company():
    jobs = [
        JobPosting(title="AI Engineer", company="Acme", source="indeed", job_url="https://a.com/1"),
        JobPosting(title="AI Engineer", company="Acme", source="himalayas", job_url="https://b.com/2"),
        JobPosting(title="Rust Dev", company="NXLog", source="indeed", job_url="https://c.com/3"),
    ]

    result = deduplicate(jobs)

    assert len(result) == 2
    titles = {j.title for j in result}
    assert "AI Engineer" in titles
    assert "Rust Dev" in titles


def test_deduplicate_keeps_version_with_salary():
    jobs = [
        JobPosting(title="AI Engineer", company="Acme", source="indeed", job_url="https://a.com/1"),
        JobPosting(title="AI Engineer", company="Acme", source="himalayas", job_url="https://b.com/2", salary_min=150000, salary_max=200000),
    ]

    result = deduplicate(jobs)

    assert len(result) == 1
    assert result[0].salary_min == 150000  # kept the richer version


def test_deduplicate_keeps_version_with_description():
    jobs = [
        JobPosting(title="AI Engineer", company="Acme", source="a", job_url="https://a.com/1", description="Full description here..."),
        JobPosting(title="AI Engineer", company="Acme", source="b", job_url="https://b.com/2"),
    ]

    result = deduplicate(jobs)

    assert len(result) == 1
    assert result[0].description == "Full description here..."
