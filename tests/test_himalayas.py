import responses

from board_aggregator.scrapers.himalayas import HimalayasScraper
from tests.conftest import HIMALAYAS_API_RESPONSE


@responses.activate
def test_himalayas_scraper_parses_jobs():
    responses.add(
        responses.GET,
        "https://himalayas.app/jobs/api",
        json=HIMALAYAS_API_RESPONSE,
        status=200,
    )

    scraper = HimalayasScraper()
    jobs = scraper.scrape(["AI Operations"])

    assert len(jobs) == 2
    assert jobs[0].title == "AI Operations Manager"
    assert jobs[0].company == "Acme AI"
    assert jobs[0].source == "himalayas"
    assert jobs[0].salary_min == 150000
    assert jobs[0].salary_max == 200000
    assert jobs[0].salary_currency == "USD"
    assert jobs[0].job_url == "https://himalayas.app/companies/acme-ai/jobs/ai-operations-manager"


@responses.activate
def test_himalayas_scraper_handles_no_salary():
    responses.add(
        responses.GET,
        "https://himalayas.app/jobs/api",
        json=HIMALAYAS_API_RESPONSE,
        status=200,
    )

    scraper = HimalayasScraper()
    jobs = scraper.scrape(["DevRel"])

    devrel_job = [j for j in jobs if j.title == "DevRel Engineer"][0]
    assert devrel_job.salary_min is None
    assert devrel_job.salary_max is None


@responses.activate
def test_himalayas_scraper_converts_unix_timestamp():
    responses.add(
        responses.GET,
        "https://himalayas.app/jobs/api",
        json=HIMALAYAS_API_RESPONSE,
        status=200,
    )

    scraper = HimalayasScraper()
    jobs = scraper.scrape(["AI"])

    # pubDate 1774692720 = 2026-03-26 (approx)
    assert jobs[0].date_posted is not None
    assert jobs[0].date_posted.startswith("2026-")


@responses.activate
def test_himalayas_scraper_handles_api_error():
    responses.add(
        responses.GET,
        "https://himalayas.app/jobs/api",
        json={"error": "rate limited"},
        status=429,
    )

    scraper = HimalayasScraper()
    jobs = scraper.scrape(["AI"])

    assert jobs == []
