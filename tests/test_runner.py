from unittest.mock import MagicMock, patch

from board_aggregator.models import JobPosting
from board_aggregator.runner import collect_from_boards, deduplicate


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


def test_collect_from_boards_returns_raw_jobs():
    mock_scraper = MagicMock()
    mock_scraper.name = "test_board"
    mock_scraper.scrape.return_value = [
        JobPosting(
            title="AI Eng", company="TestCo", source="test_board", job_url="http://a"
        ),
    ]

    with patch("board_aggregator.runner.get_all_scrapers", return_value=[mock_scraper]):
        jobs = collect_from_boards(["query"], is_remote=True)

    assert len(jobs) == 1
    assert jobs[0].title == "AI Eng"
