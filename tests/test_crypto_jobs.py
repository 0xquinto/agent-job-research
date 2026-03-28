from unittest.mock import patch

import feedparser as real_feedparser

from board_aggregator.scrapers.crypto_jobs import CryptoJobsScraper


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CryptoJobs - Latest Web3 Jobs</title>
    <link>https://crypto.jobs</link>
    <item>
      <title>Co-founder &amp; CEO at Niubi Bank</title>
      <link>https://crypto.jobs/jobs/co-founder-ceo-at-niubi-bank?utm_source=rss&amp;utm_medium=feed</link>
      <guid isPermaLink="true">https://crypto.jobs/jobs/co-founder-ceo-at-niubi-bank</guid>
      <description><![CDATA[
        <p><strong>Company:</strong> Niubi Bank</p>
        <p><strong>Location:</strong> Remote</p>
        <p><strong>Salary:</strong> 180-280K USD a year</p>
        <p><strong>Type:</strong> Full Time</p>
        <p><strong>Skills:</strong> Fundraising, strategy, payments, DeFi</p>
        <p>Leadership responsibilities include seed through Series A fundraising</p>
      ]]></description>
      <category>Other</category>
      <pubDate>Tue, 24 Mar 2026 00:00:06 +0000</pubDate>
    </item>
    <item>
      <title>Junior Crypto Trader (Remote, Spot Trading) at Token town</title>
      <link>https://crypto.jobs/jobs/junior-crypto-trader?utm_source=rss</link>
      <guid isPermaLink="true">https://crypto.jobs/jobs/junior-crypto-trader</guid>
      <description><![CDATA[
        <p><strong>Company:</strong> Token town</p>
        <p><strong>Location:</strong> Remote</p>
        <p><strong>Salary:</strong> 5000</p>
        <p><strong>Type:</strong> Part Time</p>
        <p><strong>Skills:</strong> binance trust</p>
        <p>"Token Town ecosystem"</p>
      ]]></description>
      <category>Sales</category>
      <pubDate>Thu, 12 Mar 2026 00:00:07 +0000</pubDate>
    </item>
  </channel>
</rss>"""

EMPTY_RSS = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'

# Parse RSS at module level BEFORE mocks are active
PARSED_FEED = real_feedparser.parse(SAMPLE_RSS)
PARSED_EMPTY_FEED = real_feedparser.parse(EMPTY_RSS)


@patch("board_aggregator.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_extracts_company_from_description(mock_parse):
    mock_parse.return_value = PARSED_FEED

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["CEO"])

    assert len(jobs) == 2
    # Company extracted from description HTML, not title
    assert jobs[0].company == "Niubi Bank"
    assert jobs[0].source == "crypto_jobs"
    assert jobs[0].location == "Remote"
    assert jobs[0].is_remote is True


@patch("board_aggregator.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_uses_guid_not_link(mock_parse):
    """<guid> has clean URL without UTM params."""
    mock_parse.return_value = PARSED_FEED

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["any"])

    assert "utm_source" not in jobs[0].job_url
    assert jobs[0].job_url == "https://crypto.jobs/jobs/co-founder-ceo-at-niubi-bank"


@patch("board_aggregator.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_parses_title_at_pattern(mock_parse):
    mock_parse.return_value = PARSED_FEED

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["any"])

    # Title should strip the "at Company" suffix
    assert jobs[0].title == "Co-founder & CEO"


@patch("board_aggregator.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_handles_empty_feed(mock_parse):
    mock_parse.return_value = PARSED_EMPTY_FEED

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["anything"])
    assert jobs == []
