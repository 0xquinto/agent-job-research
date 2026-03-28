import responses

from board_aggregator.scrapers.cryptojobslist import CryptoJobsListScraper


NEXT_DATA_HTML = '''<html><body>
<script id="__NEXT_DATA__" type="application/json">
{"props":{"pageProps":{"jobs":[
  {
    "_id":{"$oid":"69bd0a8d86d7913525d656c8"},
    "id":"69bd0a8d86d7913525d656c8",
    "jobTitle":"Smart Contract Auditor",
    "companyName":"DeFi Corp",
    "companySlug":"defi-corp",
    "jobLocation":"",
    "remote":true,
    "salary":{"unitText":"YEAR","currency":"USD","minValue":150000,"maxValue":250000},
    "salaryString":"$150k-250k/year",
    "seoSlug":"smart-contract-auditor-at-defi-corp",
    "publishedAt":"2026-03-25T10:00:00.000Z",
    "tags":["full-time","defi","senior","remote"],
    "filled":false,
    "isActive":true
  },
  {
    "_id":{"$oid":"69bd0b1286d7913525d656c9"},
    "id":"69bd0b1286d7913525d656c9",
    "jobTitle":"Rust Engineer",
    "companyName":"Chain Labs",
    "companySlug":"chain-labs",
    "jobLocation":"Remote, US",
    "remote":true,
    "salary":null,
    "salaryString":null,
    "seoSlug":"rust-engineer-at-chain-labs",
    "publishedAt":"2026-03-26T12:00:00.000Z",
    "tags":["full-time","developer","remote"],
    "filled":false,
    "isActive":true
  }
]}}}
</script>
</body></html>'''


@responses.activate
def test_cryptojobslist_parses_next_data():
    responses.add(
        responses.GET,
        "https://cryptojobslist.com/",
        body=NEXT_DATA_HTML,
        status=200,
    )

    scraper = CryptoJobsListScraper()
    jobs = scraper.scrape(["auditor"])

    assert len(jobs) == 2
    assert jobs[0].title == "Smart Contract Auditor"
    assert jobs[0].company == "DeFi Corp"
    assert jobs[0].salary_min == 150000
    assert jobs[0].salary_max == 250000
    assert jobs[0].salary_currency == "USD"
    assert jobs[0].source == "cryptojobslist"
    assert jobs[0].job_url == "https://cryptojobslist.com/smart-contract-auditor-at-defi-corp-69bd0a8d86d7913525d656c8"


@responses.activate
def test_cryptojobslist_handles_null_salary():
    responses.add(
        responses.GET,
        "https://cryptojobslist.com/",
        body=NEXT_DATA_HTML,
        status=200,
    )

    scraper = CryptoJobsListScraper()
    jobs = scraper.scrape(["rust"])

    rust_job = [j for j in jobs if j.title == "Rust Engineer"][0]
    assert rust_job.salary_min is None
    assert rust_job.salary_max is None


@responses.activate
def test_cryptojobslist_uses_remote_boolean():
    responses.add(
        responses.GET,
        "https://cryptojobslist.com/",
        body=NEXT_DATA_HTML,
        status=200,
    )

    scraper = CryptoJobsListScraper()
    jobs = scraper.scrape(["any"])

    assert all(j.is_remote for j in jobs)
