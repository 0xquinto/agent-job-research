# HireBoost Scraper CLI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool (`hireboost-scraper`) that scrapes 10+ job boards (APIs, RSS, BeautifulSoup, Playwright) and outputs unified CSV/markdown compatible with the existing scout-1 pipeline.

**Architecture:** Each board gets its own scraper module implementing a common `Scraper` interface (`scrape(queries, filters) -> list[JobPosting]`). A CLI entrypoint orchestrates all scrapers, deduplicates results, and writes output. python-jobspy remains a dependency for Indeed + LinkedIn. New scrapers are pure Python (requests/feedparser/bs4) for easy boards and optional Playwright for SPA boards.

**Tech Stack:** Python 3.13, click (CLI), requests, feedparser, beautifulsoup4, pydantic (models), playwright (optional), python-jobspy (existing), pytest

**Real data fixtures:** All test fixtures in this plan are derived from live API responses and HTML captured on 2026-03-28 and saved to `tests/fixtures/`. Field names, HTML structures, and URL patterns are verified against production data.

---

## File Structure

```
hireboost_scraper/
  __init__.py               # Package init, version
  cli.py                    # Click CLI entrypoint
  models.py                 # JobPosting pydantic model
  runner.py                 # Orchestrator: run scrapers, dedup, output
  output.py                 # Writers: CSV, markdown (scout-1 format)
  scrapers/
    __init__.py              # Registry of all scrapers
    base.py                  # Abstract Scraper base class
    jobspy_boards.py         # Wraps python-jobspy (Indeed + LinkedIn)
    himalayas.py             # Public API scraper
    weworkremotely.py        # RSS feed scraper
    hn_hiring.py             # Algolia API scraper
    cryptojobslist.py        # __NEXT_DATA__ extraction scraper
    crypto_jobs.py           # RSS feed scraper
    web3career.py            # BeautifulSoup scraper
    cryptocurrencyjobs.py    # BeautifulSoup scraper
tests/
  __init__.py
  conftest.py                # Shared fixtures (sample HTML, mock responses)
  fixtures/                  # Real API/HTML samples captured 2026-03-28
  test_models.py             # JobPosting model tests
  test_output.py             # CSV/markdown writer tests
  test_runner.py             # Orchestrator + dedup tests
  test_himalayas.py          # Himalayas API scraper tests
  test_weworkremotely.py     # WWR RSS scraper tests
  test_hn_hiring.py          # HN Algolia scraper tests
  test_cryptojobslist.py     # CryptoJobsList scraper tests
  test_crypto_jobs.py        # crypto.jobs RSS scraper tests
  test_web3career.py         # Web3.career BS4 scraper tests
  test_cryptocurrencyjobs.py # CryptocurrencyJobs BS4 scraper tests
  test_jobspy_boards.py      # JobSpy wrapper tests
pyproject.toml               # Project config, deps, CLI entrypoint
```

---

### Task 1: Project Scaffold + JobPosting Model

**Files:**
- Create: `pyproject.toml`
- Create: `hireboost_scraper/__init__.py`
- Create: `hireboost_scraper/models.py`
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
from hireboost_scraper.models import JobPosting


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/diego/Dev/non-toxic/job-applications/hireboost-ops-ai-manager && python3 -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'hireboost_scraper'`

- [ ] **Step 3: Create pyproject.toml**

```toml
# pyproject.toml
[project]
name = "hireboost-scraper"
version = "0.1.0"
description = "Multi-board job scraper CLI for the HireBoost pipeline"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1",
    "requests>=2.31",
    "feedparser>=6.0",
    "beautifulsoup4>=4.12",
    "pydantic>=2.0",
    "python-jobspy>=1.1",
]

[project.optional-dependencies]
browser = ["playwright>=1.40"]
dev = ["pytest>=8.0", "pytest-mock>=3.12", "responses>=0.25"]

[project.scripts]
hireboost-scraper = "hireboost_scraper.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends._legacy:_Backend"
```

- [ ] **Step 4: Create package init**

```python
# hireboost_scraper/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 5: Write minimal JobPosting model**

```python
# hireboost_scraper/models.py
from pydantic import BaseModel


class JobPosting(BaseModel):
    title: str
    company: str
    source: str
    job_url: str
    location: str | None = None
    is_remote: bool = True
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "USD"
    salary_interval: str = "yearly"
    date_posted: str | None = None
    job_type: str | None = None
    description: str | None = None

    @property
    def dedup_key(self) -> tuple[str, str]:
        return (self.title.strip().lower(), self.company.strip().lower())
```

- [ ] **Step 6: Create tests/__init__.py**

```python
# tests/__init__.py
```

- [ ] **Step 7: Install dev deps and run tests**

Run:
```bash
cd /Users/diego/Dev/non-toxic/job-applications/hireboost-ops-ai-manager
pip install -e ".[dev]"
python3 -m pytest tests/test_models.py -v
```
Expected: 4 PASSED

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml hireboost_scraper/ tests/
git commit -m "feat: project scaffold with JobPosting pydantic model"
```

---

### Task 2: Scraper Base Class + Registry

**Files:**
- Create: `hireboost_scraper/scrapers/__init__.py`
- Create: `hireboost_scraper/scrapers/base.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py (append to existing file)
from hireboost_scraper.scrapers.base import BaseScraper
from hireboost_scraper.models import JobPosting


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_models.py::test_base_scraper_is_abstract -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'hireboost_scraper.scrapers'`

- [ ] **Step 3: Write the base class**

```python
# hireboost_scraper/scrapers/base.py
from abc import ABC, abstractmethod

from hireboost_scraper.models import JobPosting


class BaseScraper(ABC):
    name: str = "base"

    @abstractmethod
    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        """Scrape job postings for the given queries. Returns list of JobPosting."""
        ...
```

```python
# hireboost_scraper/scrapers/__init__.py
from hireboost_scraper.scrapers.base import BaseScraper

SCRAPER_REGISTRY: dict[str, type[BaseScraper]] = {}


def register(cls: type[BaseScraper]) -> type[BaseScraper]:
    """Decorator to register a scraper class."""
    SCRAPER_REGISTRY[cls.name] = cls
    return cls


def get_all_scrapers() -> list[BaseScraper]:
    """Instantiate and return all registered scrapers."""
    return [cls() for cls in SCRAPER_REGISTRY.values()]
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_models.py -v`
Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/
git commit -m "feat: add BaseScraper ABC and scraper registry"
```

---

### Task 3: Himalayas API Scraper

**Real API data source:** `tests/fixtures/himalayas_api_response.json` + `tests/fixtures/himalayas_field_mapping.md`

Key findings from real API:
- Endpoint is `/jobs/api` (NOT `/api/jobs`)
- Max `limit` per request is 20
- `currency` field (NOT `salaryCurrency`)
- `pubDate` is Unix timestamp in seconds (NOT ISO date string)
- `applicationLink` has full absolute URL
- `seniority` is always an array of strings

**Files:**
- Create: `hireboost_scraper/scrapers/himalayas.py`
- Create: `tests/conftest.py`
- Create: `tests/test_himalayas.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/conftest.py
import pytest


HIMALAYAS_API_RESPONSE = {
    "comments": "13/03/2026: The API has been updated.",
    "updatedAt": 1774692720,
    "offset": 0,
    "limit": 20,
    "totalCount": 95423,
    "jobs": [
        {
            "title": "AI Operations Manager",
            "excerpt": "Lead AI operations for a fast-growing startup...",
            "companyName": "Acme AI",
            "companySlug": "acme-ai",
            "companyLogo": "https://cdn-images.himalayas.app/logo123",
            "employmentType": "Full Time",
            "minSalary": 150000,
            "maxSalary": 200000,
            "seniority": ["Senior"],
            "currency": "USD",
            "locationRestrictions": ["United States", "Canada"],
            "timezoneRestrictions": [-8, -7, -6, -5],
            "categories": ["Operations-Manager", "AI-Operations"],
            "parentCategories": ["Operations"],
            "description": "<p>Lead AI operations...</p>",
            "pubDate": 1774692720,
            "expiryDate": 1779876720,
            "applicationLink": "https://himalayas.app/companies/acme-ai/jobs/ai-operations-manager",
            "guid": "https://himalayas.app/companies/acme-ai/jobs/ai-operations-manager",
        },
        {
            "title": "DevRel Engineer",
            "excerpt": "Build developer community...",
            "companyName": "ToolCo",
            "companySlug": "toolco",
            "companyLogo": "https://cdn-images.himalayas.app/logo456",
            "employmentType": "Full Time",
            "minSalary": None,
            "maxSalary": None,
            "seniority": ["Mid-level"],
            "currency": "USD",
            "locationRestrictions": [],
            "timezoneRestrictions": [],
            "categories": ["Developer-Relations"],
            "parentCategories": [],
            "description": "<p>Build developer community...</p>",
            "pubDate": 1774692665,
            "expiryDate": 1779876664,
            "applicationLink": "https://himalayas.app/companies/toolco/jobs/devrel-engineer",
            "guid": "https://himalayas.app/companies/toolco/jobs/devrel-engineer",
        },
    ],
}
```

```python
# tests/test_himalayas.py
import responses

from hireboost_scraper.scrapers.himalayas import HimalayasScraper
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_himalayas.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'hireboost_scraper.scrapers.himalayas'`

- [ ] **Step 3: Write the Himalayas scraper**

```python
# hireboost_scraper/scrapers/himalayas.py
from datetime import datetime, timezone

import requests as http_requests

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

BASE_URL = "https://himalayas.app"
API_URL = f"{BASE_URL}/jobs/api"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
MAX_LIMIT = 20  # API enforces max 20 per request


@register
class HimalayasScraper(BaseScraper):
    name = "himalayas"

    def scrape(
        self, queries: list[str], is_remote: bool = True, max_pages: int = 5
    ) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        offset = 0

        for _ in range(max_pages):
            try:
                resp = http_requests.get(
                    API_URL,
                    params={"limit": MAX_LIMIT, "offset": offset},
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                if resp.status_code != 200:
                    print(f"[himalayas] API returned {resp.status_code}, skipping")
                    return jobs

                data = resp.json()
                page_jobs = data.get("jobs", [])
                if not page_jobs:
                    break

                for item in page_jobs:
                    jobs.append(
                        JobPosting(
                            title=item.get("title", ""),
                            company=item.get("companyName", ""),
                            source=self.name,
                            job_url=item.get("applicationLink", ""),
                            location=", ".join(item.get("locationRestrictions", [])) or "Worldwide",
                            is_remote=len(item.get("locationRestrictions", [])) == 0
                            or is_remote,
                            salary_min=item.get("minSalary"),
                            salary_max=item.get("maxSalary"),
                            salary_currency=item.get("currency") or "USD",
                            date_posted=self._unix_to_date(item.get("pubDate")),
                            job_type=item.get("employmentType"),
                            description=item.get("excerpt"),
                        )
                    )

                total = data.get("totalCount", 0)
                offset += MAX_LIMIT
                if offset >= total:
                    break

            except Exception as e:
                print(f"[himalayas] Error: {e}")
                break

        return jobs

    @staticmethod
    def _unix_to_date(ts: int | None) -> str | None:
        """Convert Unix timestamp (seconds) to ISO date string."""
        if ts is None:
            return None
        try:
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return None
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_himalayas.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/himalayas.py tests/conftest.py tests/test_himalayas.py
git commit -m "feat: add Himalayas API scraper (verified /jobs/api endpoint)"
```

---

### Task 4: We Work Remotely RSS Scraper

**Real data source:** `tests/fixtures/wwr_rss_sample.xml` + `tests/fixtures/wwr_field_mapping.md`

Key findings from real RSS:
- No `wwr:` namespace — custom tags are bare (`<region>`, `<type>`, `<skills>`, `<expires_at>`)
- Company name in `<title>` as `"Company: Job Title"` (split on first `:`)
- `<link>` and `<guid>` are identical canonical URLs
- Date is RFC 2822: `Fri, 27 Mar 2026 20:20:27 +0000`
- `dc:` and `media:` namespaces present (Dublin Core, Yahoo Media RSS)

**Files:**
- Create: `hireboost_scraper/scrapers/weworkremotely.py`
- Create: `tests/test_weworkremotely.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_weworkremotely.py
from unittest.mock import patch, MagicMock

from hireboost_scraper.scrapers.weworkremotely import WeWorkRemotelyScraper


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


@patch("hireboost_scraper.scrapers.weworkremotely.feedparser.parse")
def test_wwr_scraper_parses_rss(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(SAMPLE_RSS)

    scraper = WeWorkRemotelyScraper()
    jobs = scraper.scrape(["AI Operations"])

    assert len(jobs) == 2
    assert jobs[0].company == "Company Name"
    assert jobs[0].title == "AI Operations Lead"
    assert jobs[0].source == "weworkremotely"
    assert jobs[0].is_remote is True
    assert "weworkremotely.com" in jobs[0].job_url


@patch("hireboost_scraper.scrapers.weworkremotely.feedparser.parse")
def test_wwr_scraper_splits_company_on_first_colon():
    """Company name must split on first colon only (job titles can contain colons)."""
    import feedparser
    rss = """<?xml version="1.0"?><rss version="2.0"><channel>
    <item>
      <title><![CDATA[BigCorp: Senior Engineer: Payments Team]]></title>
      <link>https://weworkremotely.com/remote-jobs/bigcorp-payments</link>
      <guid>https://weworkremotely.com/remote-jobs/bigcorp-payments</guid>
      <pubDate>Wed, 27 Mar 2026 12:00:00 +0000</pubDate>
      <description><![CDATA[<p>Payments role</p>]]></description>
    </item>
    </channel></rss>"""
    mock_parse.return_value = feedparser.parse(rss)

    scraper = WeWorkRemotelyScraper()
    jobs = scraper.scrape(["Engineer"])

    assert jobs[0].company == "BigCorp"
    assert jobs[0].title == "Senior Engineer: Payments Team"


@patch("hireboost_scraper.scrapers.weworkremotely.feedparser.parse")
def test_wwr_scraper_handles_empty_feed(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(
        '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
    )

    scraper = WeWorkRemotelyScraper()
    jobs = scraper.scrape(["anything"])

    assert jobs == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_weworkremotely.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the WWR scraper**

```python
# hireboost_scraper/scrapers/weworkremotely.py
import feedparser

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

FEED_URLS = [
    "https://weworkremotely.com/remote-jobs.rss",
    "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]


@register
class WeWorkRemotelyScraper(BaseScraper):
    name = "weworkremotely"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        seen_urls: set[str] = set()

        for feed_url in FEED_URLS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    url = entry.get("link", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    raw_title = entry.get("title", "")
                    company, title = self._parse_title(raw_title)

                    # Region and type are bare custom tags (no namespace)
                    region = entry.get("region", "")
                    job_type = entry.get("type", "")

                    jobs.append(
                        JobPosting(
                            title=title,
                            company=company,
                            source=self.name,
                            job_url=url,
                            location=region or "Remote",
                            is_remote=True,
                            date_posted=entry.get("published", ""),
                            job_type=job_type,
                            description=entry.get("summary", ""),
                        )
                    )
            except Exception as e:
                print(f"[weworkremotely] Error fetching {feed_url}: {e}")

        return jobs

    @staticmethod
    def _parse_title(raw: str) -> tuple[str, str]:
        """WWR titles are 'Company Name: Job Title'. Split on FIRST colon only."""
        if ": " in raw:
            company, title = raw.split(": ", 1)
            return company.strip(), title.strip()
        return "", raw.strip()
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_weworkremotely.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/weworkremotely.py tests/test_weworkremotely.py
git commit -m "feat: add We Work Remotely RSS scraper"
```

---

### Task 5: HN Who's Hiring Algolia Scraper

**Real data source:** `tests/fixtures/hn_algolia_response.json` + `tests/fixtures/hn_field_mapping.md`

Key findings from real API:
- Field is `comment_text` (raw HTML with `<p>` tags, HTML entities like `&#x2F;`, `&#x27;`)
- Top-level job posts: `parent_id == story_id` (both are ints)
- Replies: `parent_id != story_id` — filter these out
- Thread discovery: search for `author_whoishiring` stories via `search_by_date`
- March 2026 thread objectID: `47219668`, 483 comments

**Files:**
- Create: `hireboost_scraper/scrapers/hn_hiring.py`
- Create: `tests/test_hn_hiring.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hn_hiring.py
import responses

from hireboost_scraper.scrapers.hn_hiring import HNHiringScraper


ALGOLIA_THREAD_RESPONSE = {
    "hits": [
        {
            "objectID": "47219668",
            "title": "Ask HN: Who is hiring? (March 2026)",
            "created_at": "2026-03-02T17:00:00Z",
            "author": "whoishiring",
        },
    ],
    "nbHits": 1,
}

ALGOLIA_COMMENTS_RESPONSE = {
    "hits": [
        {
            "objectID": "47398997",
            "parent_id": 47219668,
            "story_id": 47219668,
            "author": "founder_jane",
            "created_at": "2026-03-16T13:48:17Z",
            "comment_text": "Acme AI (https://acme.ai) | AI Operations Lead | REMOTE | $160K-$200K<p>We're building autonomous AI agents. Looking for someone to lead ops.<p>Tech: Python, Claude, multi-agent systems<p>Apply: jobs@acme.ai",
            "story_title": "Ask HN: Who is hiring? (March 2026)",
        },
        {
            "objectID": "47399001",
            "parent_id": 47219668,
            "story_id": 47219668,
            "author": "cto_bob",
            "created_at": "2026-03-16T14:00:00Z",
            "comment_text": "ToolCo | MCP Developer | San Francisco (ONSITE)<p>Building MCP tooling for enterprises.",
            "story_title": "Ask HN: Who is hiring? (March 2026)",
        },
        {
            "objectID": "47513830",
            "parent_id": 47398997,
            "story_id": 47219668,
            "author": "random_reply",
            "created_at": "2026-03-20T10:00:00Z",
            "comment_text": "This sounds great, applied!",
            "story_title": "Ask HN: Who is hiring? (March 2026)",
        },
    ],
    "nbHits": 3,
    "nbPages": 1,
}


@responses.activate
def test_hn_scraper_filters_top_level_only():
    responses.add(
        responses.GET,
        "https://hn.algolia.com/api/v1/search_by_date",
        json=ALGOLIA_THREAD_RESPONSE,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://hn.algolia.com/api/v1/search",
        json=ALGOLIA_COMMENTS_RESPONSE,
        status=200,
    )

    scraper = HNHiringScraper()
    jobs = scraper.scrape(["AI Operations", "MCP"])

    # Should only return top-level comments (parent_id == story_id), not replies
    assert len(jobs) == 2
    assert jobs[0].source == "hn_hiring"


@responses.activate
def test_hn_scraper_parses_pipe_separated_format():
    responses.add(
        responses.GET,
        "https://hn.algolia.com/api/v1/search_by_date",
        json=ALGOLIA_THREAD_RESPONSE,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://hn.algolia.com/api/v1/search",
        json=ALGOLIA_COMMENTS_RESPONSE,
        status=200,
    )

    scraper = HNHiringScraper()
    jobs = scraper.scrape(["AI"])

    acme = [j for j in jobs if "Acme" in j.company][0]
    assert acme.company == "Acme AI (https://acme.ai)"
    assert acme.title == "AI Operations Lead"
    assert acme.is_remote is True
    assert acme.salary_min == 160000
    assert acme.salary_max == 200000


@responses.activate
def test_hn_scraper_handles_no_thread():
    responses.add(
        responses.GET,
        "https://hn.algolia.com/api/v1/search_by_date",
        json={"hits": [], "nbHits": 0},
        status=200,
    )

    scraper = HNHiringScraper()
    jobs = scraper.scrape(["anything"])

    assert jobs == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_hn_hiring.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the HN scraper**

```python
# hireboost_scraper/scrapers/hn_hiring.py
import re

import requests as http_requests

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
ALGOLIA_DATE_URL = "https://hn.algolia.com/api/v1/search_by_date"


@register
class HNHiringScraper(BaseScraper):
    name = "hn_hiring"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        thread_id = self._find_latest_thread()
        if not thread_id:
            print("[hn_hiring] No 'Who is hiring?' thread found")
            return []

        comments = self._fetch_comments(thread_id)
        # Only top-level comments are job posts: parent_id == story_id
        job_comments = [c for c in comments if c.get("parent_id") == c.get("story_id")]

        jobs: list[JobPosting] = []
        for comment in job_comments:
            text = comment.get("comment_text", "")
            parsed = self._parse_comment(text, comment)
            if parsed:
                jobs.append(parsed)

        return jobs

    def _find_latest_thread(self) -> int | None:
        """Find the most recent 'Who is hiring?' thread using search_by_date."""
        try:
            resp = http_requests.get(
                ALGOLIA_DATE_URL,
                params={
                    "tags": "story,author_whoishiring",
                    "hitsPerPage": 1,
                },
                timeout=15,
            )
            hits = resp.json().get("hits", [])
            if hits:
                return int(hits[0]["objectID"])
        except Exception as e:
            print(f"[hn_hiring] Error finding thread: {e}")
        return None

    def _fetch_comments(self, thread_id: int) -> list[dict]:
        all_comments: list[dict] = []
        page = 0
        while True:
            try:
                resp = http_requests.get(
                    ALGOLIA_URL,
                    params={
                        "tags": f"comment,story_{thread_id}",
                        "hitsPerPage": 1000,
                        "page": page,
                    },
                    timeout=30,
                )
                data = resp.json()
                hits = data.get("hits", [])
                if not hits:
                    break
                all_comments.extend(hits)
                if page >= data.get("nbPages", 1) - 1:
                    break
                page += 1
            except Exception as e:
                print(f"[hn_hiring] Error fetching comments page {page}: {e}")
                break
        return all_comments

    def _parse_comment(self, text: str, comment: dict) -> JobPosting | None:
        if not text or len(text) < 20:
            return None

        # Strip HTML: replace <p> with newlines, remove tags, decode entities
        clean = self._strip_html(text)

        # HN job posts typically start with "Company | Role | Location | ..."
        first_line = clean.split("\n")[0]
        parts = [p.strip() for p in first_line.split("|")]

        company = parts[0] if len(parts) >= 1 else "Unknown"
        title = parts[1] if len(parts) >= 2 else first_line[:100]
        location = parts[2] if len(parts) >= 3 else ""

        # Extract company URL if present
        url_match = re.search(r"https?://[^\s<>)]+", text)
        job_url = url_match.group(0) if url_match else f"https://news.ycombinator.com/item?id={comment.get('objectID', '')}"

        is_remote = bool(re.search(r"\bREMOTE\b", clean, re.IGNORECASE))

        # Try to extract salary ($160K-$200K pattern)
        salary_match = re.search(r"\$(\d{2,3})[Kk]\s*[-–]\s*\$?(\d{2,3})[Kk]", clean)
        salary_min = int(salary_match.group(1)) * 1000 if salary_match else None
        salary_max = int(salary_match.group(2)) * 1000 if salary_match else None

        return JobPosting(
            title=title,
            company=company,
            source=self.name,
            job_url=job_url,
            location=location,
            is_remote=is_remote,
            salary_min=salary_min,
            salary_max=salary_max,
            date_posted=comment.get("created_at", "")[:10],
            description=clean[:500],
        )

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags and decode common entities from HN comment_text."""
        text = html.replace("<p>", "\n").replace("</p>", "")
        text = re.sub(r"<[^>]+>", "", text)
        text = (
            text.replace("&#x2F;", "/")
            .replace("&#x27;", "'")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )
        return text.strip()
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_hn_hiring.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/hn_hiring.py tests/test_hn_hiring.py
git commit -m "feat: add HN Who's Hiring Algolia API scraper"
```

---

### Task 6: CryptoJobsList NEXT_DATA Scraper

**Real data source:** `tests/fixtures/cryptojobslist_next_data_jobs.json` + `tests/fixtures/cryptojobslist_field_mapping.md`

Key findings from real __NEXT_DATA__:
- `salary` is a nested object: `salary.minValue`, `salary.maxValue`, `salary.currency`, `salary.unitText`
- URL pattern: `https://cryptojobslist.com/{seoSlug}-{id}` (NOT `/jobs/{slug}`)
- Has flat `id` field alongside `_id.$oid`
- `remote` boolean field for remote detection
- `publishedAt` is ISO8601 string
- `jobLocation` is empty string when remote (not null)

**Files:**
- Create: `hireboost_scraper/scrapers/cryptojobslist.py`
- Create: `tests/test_cryptojobslist.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cryptojobslist.py
import responses

from hireboost_scraper.scrapers.cryptojobslist import CryptoJobsListScraper


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cryptojobslist.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the scraper**

```python
# hireboost_scraper/scrapers/cryptojobslist.py
import json
import re

import requests as http_requests

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

BASE_URL = "https://cryptojobslist.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

CATEGORY_PAGES = [
    f"{BASE_URL}/",
    f"{BASE_URL}/operations",
    f"{BASE_URL}/remote",
    f"{BASE_URL}/smart-contract",
]


@register
class CryptoJobsListScraper(BaseScraper):
    name = "cryptojobslist"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        seen_ids: set[str] = set()

        for page_url in CATEGORY_PAGES:
            try:
                resp = http_requests.get(
                    page_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                if resp.status_code != 200:
                    continue

                match = re.search(
                    r'id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    resp.text,
                    re.DOTALL,
                )
                if not match:
                    continue

                data = json.loads(match.group(1))
                page_jobs = data.get("props", {}).get("pageProps", {}).get("jobs", [])

                for item in page_jobs:
                    job_id = item.get("id", "")
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    # Salary is a nested object with minValue/maxValue/currency/unitText
                    salary = item.get("salary")
                    salary_min = None
                    salary_max = None
                    salary_currency = "USD"
                    if isinstance(salary, dict):
                        salary_min = salary.get("minValue")
                        salary_max = salary.get("maxValue")
                        salary_currency = salary.get("currency", "USD")

                    # URL pattern: {seoSlug}-{id}
                    seo_slug = item.get("seoSlug", "")
                    job_url = f"{BASE_URL}/{seo_slug}-{job_id}" if seo_slug else ""

                    # Remote detection uses the boolean `remote` field
                    is_job_remote = item.get("remote", False)

                    # Date from publishedAt ISO8601
                    published_at = item.get("publishedAt", "")
                    date_posted = published_at[:10] if published_at else None

                    jobs.append(
                        JobPosting(
                            title=item.get("jobTitle", ""),
                            company=item.get("companyName", ""),
                            source=self.name,
                            job_url=job_url,
                            location=item.get("jobLocation", "") or "Remote",
                            is_remote=is_job_remote,
                            salary_min=salary_min,
                            salary_max=salary_max,
                            salary_currency=salary_currency,
                            date_posted=date_posted,
                        )
                    )
            except Exception as e:
                print(f"[cryptojobslist] Error on {page_url}: {e}")

        return jobs
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_cryptojobslist.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/cryptojobslist.py tests/test_cryptojobslist.py
git commit -m "feat: add CryptoJobsList NEXT_DATA scraper (verified salary.minValue/maxValue)"
```

---

### Task 7: crypto.jobs RSS Scraper

**Real data source:** `tests/fixtures/cryptojobs_rss_sample.xml` + `tests/fixtures/cryptojobs_field_mapping.md`

Key findings from real RSS:
- Company, location, salary, type, skills are ALL embedded as HTML inside `<description>` CDATA
- Description format: `<p><strong>Company:</strong> value</p>` for each field
- `<title>` has varying patterns: `"Company — Role at Company"` or `"Role at Company"`
- `<guid>` has clean URL (no UTM params) — use this, not `<link>`
- Only `atom:` namespace (no custom job fields)
- Salary is free-form text: `"180-280K USD a year"`, `"5000"`, token grants

**Files:**
- Create: `hireboost_scraper/scrapers/crypto_jobs.py`
- Create: `tests/test_crypto_jobs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_crypto_jobs.py
from unittest.mock import patch

from hireboost_scraper.scrapers.crypto_jobs import CryptoJobsScraper


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


@patch("hireboost_scraper.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_extracts_company_from_description(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(SAMPLE_RSS)

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["CEO"])

    assert len(jobs) == 2
    # Company extracted from description HTML, not title
    assert jobs[0].company == "Niubi Bank"
    assert jobs[0].source == "crypto_jobs"
    assert jobs[0].location == "Remote"
    assert jobs[0].is_remote is True


@patch("hireboost_scraper.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_uses_guid_not_link(mock_parse):
    """<guid> has clean URL without UTM params."""
    import feedparser
    mock_parse.return_value = feedparser.parse(SAMPLE_RSS)

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["any"])

    assert "utm_source" not in jobs[0].job_url
    assert jobs[0].job_url == "https://crypto.jobs/jobs/co-founder-ceo-at-niubi-bank"


@patch("hireboost_scraper.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_parses_title_at_pattern(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(SAMPLE_RSS)

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["any"])

    # Title should strip the "at Company" suffix
    assert jobs[0].title == "Co-founder & CEO"


@patch("hireboost_scraper.scrapers.crypto_jobs.feedparser.parse")
def test_crypto_jobs_handles_empty_feed(mock_parse):
    import feedparser
    mock_parse.return_value = feedparser.parse(
        '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
    )

    scraper = CryptoJobsScraper()
    jobs = scraper.scrape(["anything"])
    assert jobs == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_crypto_jobs.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the scraper**

```python
# hireboost_scraper/scrapers/crypto_jobs.py
import re

import feedparser
from bs4 import BeautifulSoup

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

FEED_URL = "https://crypto.jobs/feed/rss"


@register
class CryptoJobsScraper(BaseScraper):
    name = "crypto_jobs"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        try:
            feed = feedparser.parse(FEED_URL)
            for entry in feed.entries:
                # Extract structured fields from HTML description
                desc_html = entry.get("summary", "")
                fields = self._parse_description(desc_html)

                # Company from description (more reliable than title)
                company = fields.get("Company", "")

                # Title: strip "at Company" suffix from RSS title
                raw_title = entry.get("title", "")
                title = self._parse_title(raw_title, company)

                # Use <guid> for clean URL (no UTM params), fall back to <link>
                job_url = entry.get("id", "") or entry.get("link", "")

                location = fields.get("Location", "")
                job_type = fields.get("Type", "")

                jobs.append(
                    JobPosting(
                        title=title,
                        company=company,
                        source=self.name,
                        job_url=job_url,
                        location=location,
                        is_remote="remote" in location.lower(),
                        date_posted=entry.get("published", ""),
                        job_type=job_type,
                        description=desc_html[:500],
                    )
                )
        except Exception as e:
            print(f"[crypto_jobs] Error: {e}")

        return jobs

    @staticmethod
    def _parse_description(html: str) -> dict[str, str]:
        """Extract structured fields from description CDATA HTML.

        Format: <p><strong>Key:</strong> Value</p>
        Returns dict with keys: Company, Location, Salary, Type, Skills
        """
        soup = BeautifulSoup(html, "html.parser")
        fields: dict[str, str] = {}
        for p in soup.find_all("p"):
            strong = p.find("strong")
            if strong:
                key = strong.get_text(strip=True).rstrip(":")
                # Value is the text after the strong tag
                value = p.get_text(strip=True)[len(key) + 1:].strip()
                fields[key] = value
        return fields

    @staticmethod
    def _parse_title(raw: str, company: str) -> str:
        """Strip 'at Company' suffix and company prefix patterns from title."""
        title = raw
        # Remove "at Company" suffix
        if company and f" at {company}" in title:
            title = title.rsplit(f" at {company}", 1)[0]
        # Remove "Company — " prefix (some entries use em dash prefix)
        if company and title.startswith(f"{company} — "):
            title = title[len(f"{company} — "):]
            # If still has "at Company", strip it
            if f" at {company}" in title:
                title = title.rsplit(f" at {company}", 1)[0]
        return title.strip()
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_crypto_jobs.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/crypto_jobs.py tests/test_crypto_jobs.py
git commit -m "feat: add crypto.jobs RSS scraper (parses description CDATA HTML)"
```

---

### Task 8: Web3.career BeautifulSoup Scraper

**Real data source:** `tests/fixtures/web3career_jobs_html.html` + `tests/fixtures/web3career_field_mapping.md`

Key findings from real HTML:
- Jobs are in a `<table>` with `<tr onclick>` rows (NOT divs)
- URL extracted from `onclick` attribute via regex: `tableTurboRowClick(event, '/slug/id')`
- Title in `tds[0]` inside `<h2 class="job-title-mobile mb-auto">`
- Company in `tds[1]` inside `<h3>`
- Salary in `tds[4]` inside `<p>` — only valid if starts with `$` (otherwise "Estimated salary...")
- Location: `<a href="/remote-jobs">Remote</a>` or `<a href="/web3-jobs-*">City</a>`
- Skip rows where `tds[0]` has no `<h2>` (ad rows like Metana bootcamp banners)

**Files:**
- Create: `hireboost_scraper/scrapers/web3career.py`
- Create: `tests/test_web3career.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_web3career.py
from pathlib import Path

import responses

from hireboost_scraper.scrapers.web3career import Web3CareerScraper


# Load real HTML fixture
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "web3career_jobs_html.html"
SAMPLE_HTML = FIXTURE_PATH.read_text()


@responses.activate
def test_web3career_parses_table_rows():
    responses.add(
        responses.GET,
        "https://web3.career/remote-jobs",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    assert len(jobs) == 4
    assert jobs[0].title == "Senior Product Manager Privacy"
    assert jobs[0].company == "Base"
    assert jobs[0].source == "web3career"


@responses.activate
def test_web3career_extracts_url_from_onclick():
    responses.add(
        responses.GET,
        "https://web3.career/remote-jobs",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    assert jobs[0].job_url == "https://web3.career/senior-product-manager-privacy-base/148070"


@responses.activate
def test_web3career_parses_real_salary_only():
    """Only salaries starting with $ are real; 'Estimated salary...' should be None."""
    responses.add(
        responses.GET,
        "https://web3.career/remote-jobs",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    # Job 0 (Base) has "Estimated salary..." — should be None
    assert jobs[0].salary_min is None
    # Job 1 (Tether) has "$76k - $84k" — should parse
    assert jobs[1].salary_min == 76000
    assert jobs[1].salary_max == 84000
    # Job 2 (Referment) has "$175k - $250k"
    assert jobs[2].salary_min == 175000
    assert jobs[2].salary_max == 250000


@responses.activate
def test_web3career_detects_remote_location():
    responses.add(
        responses.GET,
        "https://web3.career/remote-jobs",
        body=SAMPLE_HTML,
        status=200,
    )

    scraper = Web3CareerScraper()
    jobs = scraper.scrape(["any"])

    # Job 0 (Base): <a href="/remote-jobs">Remote</a>
    assert jobs[0].location == "Remote"
    assert jobs[0].is_remote is True
    # Job 1 (Tether): <a href="/web3-jobs-warsaw">Warsaw</a>
    assert jobs[1].location == "Warsaw"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_web3career.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the scraper**

```python
# hireboost_scraper/scrapers/web3career.py
import re

import requests as http_requests
from bs4 import BeautifulSoup

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

BASE_URL = "https://web3.career"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

PAGES = [
    f"{BASE_URL}/remote-jobs",
    f"{BASE_URL}/security+smart-contract-jobs",
    f"{BASE_URL}/solidity-jobs",
    f"{BASE_URL}/defi+security-jobs",
]


@register
class Web3CareerScraper(BaseScraper):
    name = "web3career"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        seen_urls: set[str] = set()

        for page_url in PAGES:
            try:
                resp = http_requests.get(
                    page_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                for row in soup.select("tr[onclick]"):
                    tds = row.find_all("td")
                    if len(tds) < 2:
                        continue

                    # Skip ad rows (no h2 in first td)
                    h2 = tds[0].find("h2")
                    if not h2:
                        continue

                    title = h2.get_text(strip=True)

                    # Company from h3 in second td
                    h3 = tds[1].find("h3")
                    company = h3.get_text(strip=True) if h3 else ""

                    # URL from onclick attribute
                    onclick = row.get("onclick", "")
                    url_match = re.search(r"'(/[^']+)'", onclick)
                    job_url = f"{BASE_URL}{url_match.group(1)}" if url_match else ""

                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    # Location: check for /remote-jobs or /web3-jobs-* links
                    location = ""
                    is_job_remote = False
                    if row.find("a", href="/remote-jobs"):
                        location = "Remote"
                        is_job_remote = True
                    else:
                        for td in tds[2:]:
                            loc_link = td.find("a", href=lambda h: h and "/web3-jobs-" in h)
                            if loc_link:
                                location = loc_link.get_text(strip=True)
                                break

                    # Salary from tds[4] <p> — only if starts with $
                    salary_min, salary_max = None, None
                    if len(tds) > 4:
                        p = tds[4].find("p")
                        if p:
                            raw = p.get_text(strip=True)
                            if raw.startswith("$"):
                                salary_min, salary_max = self._parse_salary(raw)

                    jobs.append(
                        JobPosting(
                            title=title,
                            company=company,
                            source=self.name,
                            job_url=job_url,
                            location=location,
                            is_remote=is_job_remote,
                            salary_min=salary_min,
                            salary_max=salary_max,
                        )
                    )
            except Exception as e:
                print(f"[web3career] Error on {page_url}: {e}")

        return jobs

    @staticmethod
    def _parse_salary(text: str) -> tuple[float | None, float | None]:
        """Parse salary like '$76k - $84k' or '$175k - $250k'."""
        if not text:
            return None, None
        match = re.search(r"\$(\d+)[Kk]\s*[-–]\s*\$?(\d+)[Kk]", text)
        if match:
            return int(match.group(1)) * 1000, int(match.group(2)) * 1000
        return None, None
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_web3career.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/web3career.py tests/test_web3career.py
git commit -m "feat: add Web3.career BeautifulSoup scraper (table tr[onclick] structure)"
```

---

### Task 9: CryptocurrencyJobs BeautifulSoup Scraper

**Real data source:** `tests/fixtures/cryptocurrencyjobs_html.html` + `tests/fixtures/cryptocurrencyjobs_field_mapping.md`

Key findings from real HTML:
- Jobs are `<li>` items inside a `<ul>` (NOT divs with CSS classes)
- Title: `li > h2 > a` (href is the job URL)
- Company: `li > h3` (may or may not contain `<a>`)
- Location: first `<ul>` inside `<li>`, each location in `<li><h4><a>`
- Employment type: second `<ul>` inside `<li>`
- Salary: `<span>` with `$`/`€` pattern, directly inside `<li>` (~30-40% of listings)
- Date: `<span>` with relative strings: "Today", "1d", "3d", "9w"
- Featured: optional `<span>Featured</span>` at end
- NO semantic CSS classes — Tailwind only. Must use tag structure selectors.

**Files:**
- Create: `hireboost_scraper/scrapers/cryptocurrencyjobs.py`
- Create: `tests/test_cryptocurrencyjobs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cryptocurrencyjobs.py
from pathlib import Path

import responses

from hireboost_scraper.scrapers.cryptocurrencyjobs import CryptocurrencyJobsScraper


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

    # Job 0 (Ethena Labs): has "€50K – €75K"
    ethena = jobs[0]
    assert ethena.salary_min is not None
    # Job 1 (Legacy): no salary span
    legacy = jobs[1]
    assert legacy.salary_min is None
    # Job 3 (Paradigm): has "$100K – $180K"
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cryptocurrencyjobs.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the scraper**

```python
# hireboost_scraper/scrapers/cryptocurrencyjobs.py
import re

import requests as http_requests
from bs4 import BeautifulSoup

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper

BASE_URL = "https://cryptocurrencyjobs.co"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

CATEGORY_PAGES = [
    f"{BASE_URL}/",
    f"{BASE_URL}/operations/",
    f"{BASE_URL}/remote/",
]

SALARY_PATTERN = re.compile(r"[\$€£][\d,.]+[Kk]?\s*[–\-]\s*[\$€£]?[\d,.]+[Kk]?|[\$€£][\d,.]+[Kk]")


@register
class CryptocurrencyJobsScraper(BaseScraper):
    name = "cryptocurrencyjobs"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        seen_urls: set[str] = set()

        for page_url in CATEGORY_PAGES:
            try:
                resp = http_requests.get(
                    page_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=30,
                )
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                # Find the first <ul> that contains job <li> cards
                # Job cards have h2 > a for title
                for li in soup.find_all("li"):
                    title_tag = li.select_one("h2 a")
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    href = title_tag.get("href", "")
                    job_url = f"{BASE_URL}{href}" if href.startswith("/") else href

                    if job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    # Company: h3 with or without <a>
                    company_tag = li.find("h3")
                    if company_tag:
                        company_link = company_tag.find("a")
                        company = company_link.get_text(strip=True) if company_link else company_tag.get_text(strip=True)
                    else:
                        company = ""

                    # Location: first <ul> inside li, each location in li > h4 > a
                    location = ""
                    is_job_remote = False
                    inner_uls = li.find_all("ul", recursive=False)
                    if inner_uls:
                        loc_links = inner_uls[0].find_all("a")
                        locations = [a.get_text(strip=True) for a in loc_links]
                        location = ", ".join(locations)
                        is_job_remote = any("remote" in loc.lower() for loc in locations)

                    # Salary: bare <span> matching currency pattern
                    salary_min, salary_max = None, None
                    for span in li.find_all("span", recursive=False):
                        text = span.get_text(strip=True)
                        if SALARY_PATTERN.search(text):
                            salary_min, salary_max = self._parse_salary(text)
                            break

                    jobs.append(
                        JobPosting(
                            title=title,
                            company=company,
                            source=self.name,
                            job_url=job_url,
                            location=location,
                            is_remote=is_job_remote,
                            salary_min=salary_min,
                            salary_max=salary_max,
                        )
                    )
            except Exception as e:
                print(f"[cryptocurrencyjobs] Error on {page_url}: {e}")

        return jobs

    @staticmethod
    def _parse_salary(text: str) -> tuple[float | None, float | None]:
        """Parse salary like '$100K – $180K' or '€50K – €75K'."""
        if not text:
            return None, None
        # Match ranges: $100K – $180K, €50K – €75K
        match = re.search(r"[\$€£](\d+\.?\d*)[Kk]\s*[–\-]\s*[\$€£]?(\d+\.?\d*)[Kk]", text)
        if match:
            return float(match.group(1)) * 1000, float(match.group(2)) * 1000
        # Match single values: $120K
        single = re.search(r"[\$€£](\d+\.?\d*)[Kk]", text)
        if single:
            val = float(single.group(1)) * 1000
            return val, val
        return None, None
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_cryptocurrencyjobs.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/cryptocurrencyjobs.py tests/test_cryptocurrencyjobs.py
git commit -m "feat: add CryptocurrencyJobs BeautifulSoup scraper (ul>li structure, no CSS classes)"
```

---

### Task 10: JobSpy Wrapper (Indeed + LinkedIn)

**Files:**
- Create: `hireboost_scraper/scrapers/jobspy_boards.py`
- Create: `tests/test_jobspy_boards.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_jobspy_boards.py
from unittest.mock import patch, MagicMock
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_jobspy_boards.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the wrapper**

```python
# hireboost_scraper/scrapers/jobspy_boards.py
import math

from jobspy import scrape_jobs

from hireboost_scraper.models import JobPosting
from hireboost_scraper.scrapers import register
from hireboost_scraper.scrapers.base import BaseScraper


@register
class JobSpyScraper(BaseScraper):
    name = "jobspy"

    def scrape(
        self,
        queries: list[str],
        is_remote: bool = True,
        results_per_query: int = 50,
        hours_old: int = 168,
    ) -> list[JobPosting]:
        jobs: list[JobPosting] = []

        for query in queries:
            try:
                df = scrape_jobs(
                    site_name=["indeed", "linkedin"],
                    search_term=query,
                    google_search_term=f"{query} remote jobs",
                    location="Remote",
                    results_wanted=results_per_query,
                    hours_old=hours_old,
                    country_indeed="USA",
                    is_remote=is_remote,
                )

                for _, row in df.iterrows():
                    jobs.append(
                        JobPosting(
                            title=row.get("title", ""),
                            company=row.get("company", ""),
                            source=str(row.get("site", "jobspy")),
                            job_url=str(row.get("job_url", "")),
                            location=str(row.get("location", "")),
                            is_remote=bool(row.get("is_remote", True)),
                            salary_min=self._safe_float(row.get("min_amount")),
                            salary_max=self._safe_float(row.get("max_amount")),
                            salary_currency=str(row.get("currency", "USD")),
                            salary_interval=str(row.get("interval", "yearly")),
                            date_posted=str(row.get("date_posted", "")),
                            job_type=str(row.get("job_type", "")),
                            description=str(row.get("description", ""))[:500],
                        )
                    )
            except Exception as e:
                print(f"[jobspy] Error on query '{query}': {e}")

        return jobs

    @staticmethod
    def _safe_float(val) -> float | None:
        if val is None:
            return None
        try:
            f = float(val)
            return None if math.isnan(f) else f
        except (ValueError, TypeError):
            return None
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_jobspy_boards.py -v`
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/scrapers/jobspy_boards.py tests/test_jobspy_boards.py
git commit -m "feat: add JobSpy wrapper for Indeed + LinkedIn"
```

---

### Task 11: Output Writers (CSV + Markdown)

**Files:**
- Create: `hireboost_scraper/output.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_output.py
import csv
import tempfile
from pathlib import Path

from hireboost_scraper.models import JobPosting
from hireboost_scraper.output import write_csv, write_markdown


SAMPLE_JOBS = [
    JobPosting(
        title="AI Engineer",
        company="Grafana Labs",
        source="indeed",
        job_url="https://indeed.com/viewjob?jk=abc",
        location="Remote, US",
        salary_min=154000,
        salary_max=185000,
        date_posted="2026-03-27",
        job_type="fulltime",
        description="Build AI/ML ops tooling...",
    ),
    JobPosting(
        title="Rust Developer",
        company="NXLog",
        source="himalayas",
        job_url="https://himalayas.app/jobs/rust-dev",
        location="Remote",
    ),
]


def test_write_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = Path(f.name)

    write_csv(SAMPLE_JOBS, path)

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["title"] == "AI Engineer"
    assert rows[0]["company"] == "Grafana Labs"
    assert rows[0]["salary_min"] == "154000"
    assert rows[1]["salary_min"] == ""
    path.unlink()


def test_write_markdown():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        path = Path(f.name)

    write_markdown(SAMPLE_JOBS, path)

    content = path.read_text()
    assert "# Phase 1: Job Board Scrape Results" in content
    assert "## AI Engineer" in content
    assert "Grafana Labs" in content
    assert "$154,000 - $185,000" in content or "154000" in content
    assert "## Rust Developer" in content
    path.unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_output.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the output module**

```python
# hireboost_scraper/output.py
import csv
from collections import Counter
from datetime import date
from pathlib import Path

from hireboost_scraper.models import JobPosting

CSV_FIELDS = [
    "title", "company", "source", "job_url", "location", "is_remote",
    "salary_min", "salary_max", "salary_currency", "salary_interval",
    "date_posted", "job_type", "description",
]


def write_csv(jobs: list[JobPosting], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for job in jobs:
            row = job.model_dump()
            # Convert None to empty string for CSV
            writer.writerow({k: "" if row.get(k) is None else row.get(k, "") for k in CSV_FIELDS})


def write_markdown(jobs: list[JobPosting], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    source_counts = Counter(j.source for j in jobs)
    source_summary = ", ".join(f"{src}: {cnt}" for src, cnt in source_counts.most_common())

    lines: list[str] = []
    lines.append("# Phase 1: Job Board Scrape Results")
    lines.append(f"**Date:** {date.today().isoformat()}")
    lines.append(f"**Total Postings (unique after dedup):** {len(jobs)}")
    lines.append(f"**By Board:** {source_summary}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for job in jobs:
        lines.append(f"## {job.title} -- {job.company}")
        lines.append(f"- **Source:** {job.source}")
        lines.append(f"- **Location:** {job.location or 'Remote'}")
        lines.append(f"- **Is Remote:** {job.is_remote}")

        if job.salary_min and job.salary_max:
            lines.append(
                f"- **Salary:** ${job.salary_min:,.0f} - ${job.salary_max:,.0f} {job.salary_currency} ({job.salary_interval})"
            )
        elif job.salary_min:
            lines.append(f"- **Salary:** ${job.salary_min:,.0f}+ {job.salary_currency}")
        else:
            lines.append("- **Salary:** Not listed")

        lines.append(f"- **URL:** {job.job_url}")
        if job.date_posted:
            lines.append(f"- **Date Posted:** {job.date_posted}")
        if job.job_type:
            lines.append(f"- **Job Type:** {job.job_type}")
        if job.description:
            lines.append(f"- **Description:** {job.description[:300]}")
        lines.append("---")
        lines.append("")

    path.write_text("\n".join(lines))
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_output.py -v`
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/output.py tests/test_output.py
git commit -m "feat: add CSV and markdown output writers"
```

---

### Task 12: Runner (Orchestrator + Dedup)

**Files:**
- Create: `hireboost_scraper/runner.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runner.py
from hireboost_scraper.models import JobPosting
from hireboost_scraper.runner import deduplicate, run_all


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the runner**

```python
# hireboost_scraper/runner.py
from pathlib import Path

from hireboost_scraper.models import JobPosting
from hireboost_scraper.output import write_csv, write_markdown
from hireboost_scraper.scrapers import get_all_scrapers


def deduplicate(jobs: list[JobPosting]) -> list[JobPosting]:
    """Deduplicate by (title, company), keeping the version with most data."""
    seen: dict[tuple[str, str], JobPosting] = {}

    for job in jobs:
        key = job.dedup_key
        if key not in seen:
            seen[key] = job
        else:
            existing = seen[key]
            if _richness(job) > _richness(existing):
                seen[key] = job

    return list(seen.values())


def _richness(job: JobPosting) -> int:
    """Score how much data a posting has. Higher = more complete."""
    score = 0
    if job.salary_min is not None:
        score += 3
    if job.salary_max is not None:
        score += 3
    if job.description:
        score += 2
    if job.date_posted:
        score += 1
    if job.job_type:
        score += 1
    return score


def run_all(
    queries: list[str],
    output_dir: Path,
    is_remote: bool = True,
    scrapers: list[str] | None = None,
) -> list[JobPosting]:
    """Run all registered scrapers, deduplicate, and write output."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_jobs: list[JobPosting] = []
    available = get_all_scrapers()

    for scraper in available:
        if scrapers and scraper.name not in scrapers:
            continue

        print(f"[runner] Scraping {scraper.name}...")
        try:
            jobs = scraper.scrape(queries, is_remote=is_remote)
            print(f"[runner] {scraper.name}: {len(jobs)} results")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[runner] {scraper.name} failed: {e}")

    print(f"[runner] Total before dedup: {len(all_jobs)}")
    unique_jobs = deduplicate(all_jobs)
    print(f"[runner] Total after dedup: {len(unique_jobs)}")

    write_csv(unique_jobs, output_dir / "all-postings.csv")
    write_markdown(unique_jobs, output_dir / "all-postings.md")

    return unique_jobs
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_runner.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add hireboost_scraper/runner.py tests/test_runner.py
git commit -m "feat: add runner orchestrator with deduplication"
```

---

### Task 13: CLI Entrypoint

**Files:**
- Create: `hireboost_scraper/cli.py`

- [ ] **Step 1: Write the CLI**

```python
# hireboost_scraper/cli.py
from pathlib import Path

import click

from hireboost_scraper.runner import run_all

DEFAULT_QUERIES = [
    "Operations Manager AI",
    "AI Operations Lead",
    "Business Operations AI Integration",
    "AI Process Automation Manager",
    "Technical Operations Manager",
    "AI Agent Developer",
    "Developer Relations",
]

DEFAULT_OUTPUT = Path("research/phase-1-scrape")


@click.command()
@click.option(
    "-q", "--query",
    multiple=True,
    help="Search query (can specify multiple). Defaults to 7 built-in queries.",
)
@click.option(
    "-o", "--output-dir",
    type=click.Path(path_type=Path),
    default=DEFAULT_OUTPUT,
    help=f"Output directory. Default: {DEFAULT_OUTPUT}",
)
@click.option(
    "-s", "--scraper",
    multiple=True,
    help="Run only specific scrapers (e.g., -s himalayas -s hn_hiring). Default: all.",
)
@click.option(
    "--remote-only/--include-onsite",
    default=True,
    help="Only include remote jobs. Default: remote-only.",
)
@click.option(
    "--list-scrapers",
    is_flag=True,
    help="List all available scrapers and exit.",
)
def main(query, output_dir, scraper, remote_only, list_scrapers):
    """HireBoost Scraper -- Multi-board job scraper for the HireBoost pipeline."""
    # Import here to trigger registration via module imports
    import hireboost_scraper.scrapers.jobspy_boards  # noqa: F401
    import hireboost_scraper.scrapers.himalayas  # noqa: F401
    import hireboost_scraper.scrapers.weworkremotely  # noqa: F401
    import hireboost_scraper.scrapers.hn_hiring  # noqa: F401
    import hireboost_scraper.scrapers.cryptojobslist  # noqa: F401
    import hireboost_scraper.scrapers.crypto_jobs  # noqa: F401
    import hireboost_scraper.scrapers.web3career  # noqa: F401
    import hireboost_scraper.scrapers.cryptocurrencyjobs  # noqa: F401

    from hireboost_scraper.scrapers import SCRAPER_REGISTRY

    if list_scrapers:
        click.echo("Available scrapers:")
        for name in sorted(SCRAPER_REGISTRY.keys()):
            click.echo(f"  - {name}")
        return

    queries = list(query) if query else DEFAULT_QUERIES
    scraper_filter = list(scraper) if scraper else None

    click.echo(f"Running {len(queries)} queries across {'all' if not scraper_filter else len(scraper_filter)} scrapers")
    click.echo(f"Output: {output_dir}")
    click.echo(f"Remote only: {remote_only}")
    click.echo("---")

    jobs = run_all(
        queries=queries,
        output_dir=output_dir,
        is_remote=remote_only,
        scrapers=scraper_filter,
    )

    click.echo(f"\nDone! {len(jobs)} unique postings written to {output_dir}/")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the CLI manually**

Run:
```bash
cd /Users/diego/Dev/non-toxic/job-applications/hireboost-ops-ai-manager
python3 -m hireboost_scraper.cli --list-scrapers
```
Expected output:
```
Available scrapers:
  - crypto_jobs
  - cryptocurrencyjobs
  - cryptojobslist
  - himalayas
  - hn_hiring
  - jobspy
  - web3career
  - weworkremotely
```

- [ ] **Step 3: Test a single scraper end-to-end**

Run:
```bash
python3 -m hireboost_scraper.cli -s himalayas -q "AI Operations" -o /tmp/hireboost-test
```
Expected: Creates `/tmp/hireboost-test/all-postings.csv` and `/tmp/hireboost-test/all-postings.md`

- [ ] **Step 4: Commit**

```bash
git add hireboost_scraper/cli.py
git commit -m "feat: add Click CLI entrypoint with scraper selection"
```

---

### Task 14: Full Test Suite Run + Integration

- [ ] **Step 1: Run full test suite**

Run:
```bash
cd /Users/diego/Dev/non-toxic/job-applications/hireboost-ops-ai-manager
python3 -m pytest tests/ -v --tb=short
```
Expected: All tests PASS (26+ tests across 10 test files)

- [ ] **Step 2: Run full scrape with all scrapers**

Run:
```bash
python3 -m hireboost_scraper.cli -q "AI Operations Manager" -o /tmp/hireboost-full-test
```
Expected: Scrapes from all 8 boards, writes deduped CSV + markdown

- [ ] **Step 3: Verify output is compatible with ranker-7**

Run:
```bash
head -50 /tmp/hireboost-full-test/all-postings.md
```
Expected: Markdown format matches what ranker-7 expects (## Title -- Company, **Source:**, **Salary:**, etc.)

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: hireboost-scraper CLI v0.1.0 -- 8 board scrapers"
```

---

## Post-Implementation: Future Tasks (Not in this plan)

These are out of scope for v0.1.0 but documented for future iterations:

1. **Playwright scrapers** for LLMHire, aijobs.net, gm.careers (SPAs)
2. **GetOnBoard API** with free token registration
3. **DevRel Talent + RemoteFront** BS4 structure inspection
4. **Query filtering** -- match query keywords against job title/description to filter irrelevant results
5. **Rate limiting** -- add configurable delays between requests per board
6. **Caching** -- skip re-scraping if results are < N hours old
7. **Update scout-1.md** to call `hireboost-scraper` CLI instead of raw python-jobspy
