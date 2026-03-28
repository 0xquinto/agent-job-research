from unittest.mock import patch

import feedparser as real_feedparser

from board_aggregator.scrapers.weworkremotely import WeWorkRemotelyScraper


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:media="http://search.yahoo.com/mrss">
  <channel>
    <title>We Work Remotely: Remote jobs in design, programming, marketing and more</title>
    <item>
      <title><![CDATA[Company Name: AI Operations Lead]]></title>
      <link>https://weworkremotely.com/remote-jobs/company-ai-ops-lead</link>
      <guid>https://weworkremotely.com/remote-jobs/company-ai-ops-lead</guid>
      <pubDate>Mon, 25 Mar 2026 12:00:00 +0000</pubDate>
      <description><![CDATA[<p>We're looking for an AI Operations Lead...</p>]]></description>
      <region><![CDATA[Anywhere in the World]]></region>
      <type><![CDATA[Full-Time]]></type>
      <category><![CDATA[Programming]]></category>
    </item>
    <item>
      <title><![CDATA[OtherCo: DevRel Engineer]]></title>
      <link>https://weworkremotely.com/remote-jobs/otherco-devrel</link>
      <guid>https://weworkremotely.com/remote-jobs/otherco-devrel</guid>
      <pubDate>Tue, 26 Mar 2026 10:00:00 +0000</pubDate>
      <description><![CDATA[<p>Join our DevRel team...</p>]]></description>
      <region><![CDATA[USA Only]]></region>
      <type><![CDATA[Contract]]></type>
      <category><![CDATA[DevOps and Sysadmin]]></category>
      <skills><![CDATA[Python, TypeScript, Developer Relations]]></skills>
    </item>
  </channel>
</rss>"""

COLON_RSS = """<?xml version="1.0"?><rss version="2.0"><channel>
<item>
  <title><![CDATA[BigCorp: Senior Engineer: Payments Team]]></title>
  <link>https://weworkremotely.com/remote-jobs/bigcorp-payments</link>
  <guid>https://weworkremotely.com/remote-jobs/bigcorp-payments</guid>
  <pubDate>Wed, 27 Mar 2026 12:00:00 +0000</pubDate>
  <description><![CDATA[<p>Payments role</p>]]></description>
</item>
</channel></rss>"""

EMPTY_RSS = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'

# Parse RSS at module level BEFORE mocks are active
PARSED_FEED = real_feedparser.parse(SAMPLE_RSS)
PARSED_COLON_FEED = real_feedparser.parse(COLON_RSS)
PARSED_EMPTY_FEED = real_feedparser.parse(EMPTY_RSS)


@patch("board_aggregator.scrapers.weworkremotely.feedparser.parse")
def test_wwr_scraper_parses_rss(mock_parse):
    mock_parse.return_value = PARSED_FEED

    scraper = WeWorkRemotelyScraper()
    jobs = scraper.scrape(["AI Operations"])

    assert len(jobs) == 2
    assert jobs[0].company == "Company Name"
    assert jobs[0].title == "AI Operations Lead"
    assert jobs[0].source == "weworkremotely"
    assert jobs[0].is_remote is True
    assert "weworkremotely.com" in jobs[0].job_url


@patch("board_aggregator.scrapers.weworkremotely.feedparser.parse")
def test_wwr_scraper_splits_company_on_first_colon(mock_parse):
    """Company name must split on first colon only (job titles can contain colons)."""
    mock_parse.return_value = PARSED_COLON_FEED

    scraper = WeWorkRemotelyScraper()
    jobs = scraper.scrape(["Engineer"])

    assert jobs[0].company == "BigCorp"
    assert jobs[0].title == "Senior Engineer: Payments Team"


@patch("board_aggregator.scrapers.weworkremotely.feedparser.parse")
def test_wwr_scraper_handles_empty_feed(mock_parse):
    mock_parse.return_value = PARSED_EMPTY_FEED

    scraper = WeWorkRemotelyScraper()
    jobs = scraper.scrape(["anything"])

    assert jobs == []
