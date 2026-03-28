from pathlib import Path

import responses

from board_aggregator.scrapers.cryptocurrencyjobs import CryptocurrencyJobsScraper


# Load real HTML fixture
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cryptocurrencyjobs_html.html"
SAMPLE_HTML = FIXTURE_PATH.read_text()


@responses.activate
def test_cryptocurrencyjobs_parses_li_cards():
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/operations/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/remote/",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = CryptocurrencyJobsScraper()
    jobs = scraper.scrape(["operations"])

    # Deduped across 3 pages (same fixture)
    assert len(jobs) == 4
    assert jobs[0].title == "Financial Associate"
    assert jobs[0].company == "Ethena Labs"
    assert jobs[0].source == "cryptocurrencyjobs"


@responses.activate
def test_cryptocurrencyjobs_extracts_url_from_h2_a():
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/operations/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/remote/",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = CryptocurrencyJobsScraper()
    jobs = scraper.scrape(["any"])

    assert jobs[0].job_url == "https://cryptocurrencyjobs.co/operations/ethena-labs-financial-associate/"


@responses.activate
def test_cryptocurrencyjobs_parses_salary_from_span():
    """Salary is in a bare <span> matching currency pattern. ~30-40% of listings."""
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/operations/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/remote/",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = CryptocurrencyJobsScraper()
    jobs = scraper.scrape(["any"])

    # Job 0 (Ethena Labs): has "\u20ac50K \u2013 \u20ac75K"
    ethena = jobs[0]
    assert ethena.salary_min is not None
    # Job 1 (Legacy): no salary span
    legacy = jobs[1]
    assert legacy.salary_min is None
    # Job 3 (Paradigm): has "$100K \u2013 $180K"
    paradigm = jobs[3]
    assert paradigm.salary_min == 100000
    assert paradigm.salary_max == 180000


@responses.activate
def test_cryptocurrencyjobs_handles_company_without_link():
    """Some companies have no profile, so h3 has no <a> tag."""
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/operations/",
        body=SAMPLE_HTML,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://cryptocurrencyjobs.co/remote/",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = CryptocurrencyJobsScraper()
    jobs = scraper.scrape(["any"])

    # Job 1 (Legacy): h3 has no <a> tag
    legacy = [j for j in jobs if j.company == "Legacy"][0]
    assert legacy.company == "Legacy"
