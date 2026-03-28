from unittest.mock import patch
import pandas as pd

from hireboost_scraper.scrapers.jobspy_boards import JobSpyScraper


@patch("hireboost_scraper.scrapers.jobspy_boards.scrape_jobs")
def test_jobspy_scraper_wraps_library(mock_scrape):
    mock_scrape.return_value = pd.DataFrame([
        {
            "title": "AI Ops Manager",
            "company": "TechCo",
            "location": "Remote, US",
            "is_remote": True,
            "min_amount": 150000,
            "max_amount": 200000,
            "currency": "USD",
            "interval": "yearly",
            "job_url": "https://indeed.com/viewjob?jk=abc",
            "date_posted": "2026-03-27",
            "job_type": "fulltime",
            "site": "indeed",
            "description": "Lead AI operations...",
        },
    ])

    scraper = JobSpyScraper()
    jobs = scraper.scrape(["AI Operations Manager"])

    assert len(jobs) == 1
    assert jobs[0].title == "AI Ops Manager"
    assert jobs[0].source == "indeed"
    assert jobs[0].salary_min == 150000


@patch("hireboost_scraper.scrapers.jobspy_boards.scrape_jobs")
def test_jobspy_scraper_handles_exception(mock_scrape):
    mock_scrape.side_effect = Exception("Rate limited")

    scraper = JobSpyScraper()
    jobs = scraper.scrape(["anything"])

    assert jobs == []
