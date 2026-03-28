from pathlib import Path

import responses

from board_aggregator.scrapers.web3career import Web3CareerScraper


# Load real HTML fixture
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "web3career_jobs_html.html"
SAMPLE_HTML = FIXTURE_PATH.read_text()


def _mock_all_pages():
    """Register mock responses for all web3career page URLs."""
    for url in [
        "https://web3.career/remote-jobs",
        "https://web3.career/security+smart-contract-jobs",
        "https://web3.career/solidity-jobs",
        "https://web3.career/defi+security-jobs",
    ]:
        responses.add(responses.GET, url, body=SAMPLE_HTML, status=200)


@responses.activate
def test_web3career_parses_table_rows():
    _mock_all_pages()

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    # 4 unique jobs deduped across 4 pages (same fixture)
    assert len(jobs) == 4
    assert jobs[0].title == "Senior Product Manager Privacy"
    assert jobs[0].company == "Base"
    assert jobs[0].source == "web3career"


@responses.activate
def test_web3career_extracts_url_from_onclick():
    _mock_all_pages()

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    assert jobs[0].job_url == "https://web3.career/senior-product-manager-privacy-base/148070"


@responses.activate
def test_web3career_parses_real_salary_only():
    """Only salaries starting with $ are real; 'Estimated salary...' should be None."""
    _mock_all_pages()

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    # Job 0 (Base) has "Estimated salary..." -- should be None
    assert jobs[0].salary_min is None
    # Job 1 (Tether) has "$76k - $84k" -- should parse
    assert jobs[1].salary_min == 76000
    assert jobs[1].salary_max == 84000
    # Job 2 (Referment) has "$175k - $250k"
    assert jobs[2].salary_min == 175000
    assert jobs[2].salary_max == 250000


@responses.activate
def test_web3career_detects_remote_location():
    _mock_all_pages()

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    # Job 0 (Base): <a href="/remote-jobs">Remote</a>
    assert jobs[0].location == "Remote"
    assert jobs[0].is_remote is True
    # Job 1 (Tether): <a href="/web3-jobs-warsaw">Warsaw</a>
    assert jobs[1].location == "Warsaw"
