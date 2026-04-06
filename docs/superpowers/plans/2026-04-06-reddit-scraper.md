# Reddit Job Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Reddit scraper to board_aggregator that scans 20 subreddits for job-related posts using Reddit's OAuth2 JSON API, primarily serving as a discovery source.

**Architecture:** Single `RedditJobsScraper` class in `board_aggregator/scrapers/reddit_jobs.py` using the `@register` + `BaseScraper` pattern. Authenticates via OAuth2 client credentials, fetches a combined multi-subreddit listing from `oauth.reddit.com`, applies tiered filtering (job-board subs keep all posts, discussion subs require hiring-signal keywords), and parses posts into `JobPosting` objects.

**Tech Stack:** Python 3.12+, `requests` (existing dep), `responses` (existing test dep), Pydantic `JobPosting` model.

**Spec:** `docs/superpowers/specs/2026-04-06-reddit-scraper-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `board_aggregator/scrapers/reddit_jobs.py` | Create | `RedditJobsScraper` — auth, fetch, filter, parse |
| `tests/test_reddit_jobs.py` | Create | All test cases with mocked HTTP |
| `board_aggregator/cli.py` | Modify (line 64) | Add import to trigger registration |

---

### Task 1: OAuth2 Token Acquisition

**Files:**
- Create: `tests/test_reddit_jobs.py`
- Create: `board_aggregator/scrapers/reddit_jobs.py`

- [ ] **Step 1: Write the failing test for token acquisition**

```python
import os
from unittest.mock import patch

import responses

from board_aggregator.scrapers.reddit_jobs import RedditJobsScraper

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"

TOKEN_RESPONSE = {
    "access_token": "fake-token-abc123",
    "token_type": "bearer",
    "expires_in": 86400,
    "scope": "*",
}


@responses.activate
@patch.dict(os.environ, {"REDDIT_CLIENT_ID": "test-id", "REDDIT_CLIENT_SECRET": "test-secret"})
def test_get_token_returns_bearer_token():
    responses.add(
        responses.POST,
        TOKEN_URL,
        json=TOKEN_RESPONSE,
        status=200,
    )

    scraper = RedditJobsScraper()
    token = scraper._get_token()

    assert token == "fake-token-abc123"
    assert responses.calls[0].request.headers["User-Agent"] == "board-aggregator/1.0 (job-research-pipeline)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reddit_jobs.py::test_get_token_returns_bearer_token -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'board_aggregator.scrapers.reddit_jobs'`

- [ ] **Step 3: Write minimal implementation for token acquisition**

Create `board_aggregator/scrapers/reddit_jobs.py`:

```python
import os
import re
import time
from datetime import datetime, timezone

import requests as http_requests

from board_aggregator.models import JobPosting
from board_aggregator.scrapers import register
from board_aggregator.scrapers.base import BaseScraper

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
LISTING_URL = "https://oauth.reddit.com/r/{subs}/new.json"
USER_AGENT = "board-aggregator/1.0 (job-research-pipeline)"

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]

TIER_1_SUBS = ["forhire", "hiring", "jobbit", "remotejobs"]
TIER_2_SUBS = [
    "WorkOnline", "webdev", "datascience", "freelance", "remotework",
    "digitalnomad", "Upwork", "freelanceWriters", "copywriting",
    "graphic_design", "learnprogramming", "VirtualAssistants",
    "socialmedia", "marketing", "CustomerSuccess", "careerguidance",
]
ALL_SUBS = TIER_1_SUBS + TIER_2_SUBS

HIRING_SIGNAL = re.compile(
    r"\b(hiring|position|role|looking for|we.re hiring|job opening|apply)\b",
    re.IGNORECASE,
)

MAX_PAGES = 3


@register
class RedditJobsScraper(BaseScraper):
    name = "reddit"

    def scrape(self, queries: list[str], is_remote: bool = True) -> list[JobPosting]:
        token = self._get_token()
        if not token:
            return []

        raw_posts = self._fetch_listings(token)
        jobs: list[JobPosting] = []
        for post in raw_posts:
            parsed = self._parse_post(post)
            if parsed:
                jobs.append(parsed)
        return jobs

    def _get_token(self) -> str | None:
        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        if not client_id or not client_secret:
            print("[reddit] Missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET, skipping")
            return None

        for attempt in range(MAX_RETRIES):
            try:
                resp = http_requests.post(
                    TOKEN_URL,
                    auth=(client_id, client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"User-Agent": USER_AGENT},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return resp.json().get("access_token")
                print(f"[reddit] Token request returned {resp.status_code}")
            except Exception as e:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"[reddit] Token error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
        return None

    def _fetch_listings(self, token: str) -> list[dict]:
        return []

    def _parse_post(self, post: dict) -> JobPosting | None:
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reddit_jobs.py::test_get_token_returns_bearer_token -v`
Expected: PASS

- [ ] **Step 5: Write test for missing credentials**

Add to `tests/test_reddit_jobs.py`:

```python
@patch.dict(os.environ, {}, clear=True)
def test_get_token_missing_credentials_returns_none():
    scraper = RedditJobsScraper()
    token = scraper._get_token()
    assert token is None
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_reddit_jobs.py::test_get_token_missing_credentials_returns_none -v`
Expected: PASS (already handled by the implementation)

- [ ] **Step 7: Commit**

```bash
git add board_aggregator/scrapers/reddit_jobs.py tests/test_reddit_jobs.py
git commit -m "feat(reddit): add scraper skeleton with OAuth2 token acquisition"
```

---

### Task 2: Listing Fetch with Pagination

**Files:**
- Modify: `tests/test_reddit_jobs.py`
- Modify: `board_aggregator/scrapers/reddit_jobs.py`

- [ ] **Step 1: Write the failing test for listing fetch**

Add to `tests/test_reddit_jobs.py`:

```python
LISTING_URL_PATTERN = "https://oauth.reddit.com/r/"

LISTING_RESPONSE_PAGE_1 = {
    "data": {
        "after": "t3_page2cursor",
        "children": [
            {
                "data": {
                    "title": "[Hiring] Senior Python Dev at Acme Corp",
                    "selftext": "We're looking for a senior Python developer. Remote OK. $150K-$180K.",
                    "author": "acme_recruiter",
                    "subreddit": "forhire",
                    "permalink": "/r/forhire/comments/abc123/hiring_senior_python_dev/",
                    "created_utc": 1743897600.0,
                    "link_flair_text": "Hiring",
                }
            },
            {
                "data": {
                    "title": "Best laptop for remote work?",
                    "selftext": "Looking for recommendations on laptops.",
                    "author": "random_user",
                    "subreddit": "remotework",
                    "permalink": "/r/remotework/comments/def456/best_laptop/",
                    "created_utc": 1743897500.0,
                    "link_flair_text": None,
                }
            },
        ],
    }
}

LISTING_RESPONSE_PAGE_2 = {
    "data": {
        "after": None,
        "children": [
            {
                "data": {
                    "title": "We're hiring a DevOps engineer",
                    "selftext": "Our team at CloudCo needs a DevOps engineer. Apply at cloudco.io/careers.",
                    "author": "cloudco_hr",
                    "subreddit": "webdev",
                    "permalink": "/r/webdev/comments/ghi789/were_hiring_devops/",
                    "created_utc": 1743897400.0,
                    "link_flair_text": None,
                }
            },
        ],
    }
}


@responses.activate
@patch.dict(os.environ, {"REDDIT_CLIENT_ID": "test-id", "REDDIT_CLIENT_SECRET": "test-secret"})
def test_fetch_listings_paginates():
    responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
    responses.add(
        responses.GET,
        re.compile(r"https://oauth\.reddit\.com/r/.+/new\.json"),
        json=LISTING_RESPONSE_PAGE_1,
        status=200,
    )
    responses.add(
        responses.GET,
        re.compile(r"https://oauth\.reddit\.com/r/.+/new\.json"),
        json=LISTING_RESPONSE_PAGE_2,
        status=200,
    )

    scraper = RedditJobsScraper()
    token = scraper._get_token()
    posts = scraper._fetch_listings(token)

    # Should have fetched 2 pages (page 1 had after cursor, page 2 did not)
    assert len(posts) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reddit_jobs.py::test_fetch_listings_paginates -v`
Expected: FAIL — `assert len([]) == 3` (stub returns empty list)

- [ ] **Step 3: Implement `_fetch_listings`**

Replace the stub `_fetch_listings` in `board_aggregator/scrapers/reddit_jobs.py`:

```python
def _fetch_listings(self, token: str) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": USER_AGENT,
    }
    subs = "+".join(ALL_SUBS)
    url = LISTING_URL.format(subs=subs)

    all_posts: list[dict] = []
    after: str | None = None

    for page in range(MAX_PAGES):
        params: dict[str, str | int] = {"limit": 100, "raw_json": 1}
        if after:
            params["after"] = after

        for attempt in range(MAX_RETRIES):
            try:
                resp = http_requests.get(
                    url, headers=headers, params=params, timeout=30,
                )
                if resp.status_code == 429:
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    print(f"[reddit] Rate limited, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                if resp.status_code != 200:
                    print(f"[reddit] Listing returned {resp.status_code}, stopping")
                    return all_posts

                data = resp.json().get("data", {})
                children = data.get("children", [])
                all_posts.extend(child.get("data", {}) for child in children)
                after = data.get("after")
                break
            except Exception as e:
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                print(f"[reddit] Fetch error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                else:
                    return all_posts

        if not after:
            break

    return all_posts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reddit_jobs.py::test_fetch_listings_paginates -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/scrapers/reddit_jobs.py tests/test_reddit_jobs.py
git commit -m "feat(reddit): implement listing fetch with pagination and retry"
```

---

### Task 3: Post Filtering and Parsing

**Files:**
- Modify: `tests/test_reddit_jobs.py`
- Modify: `board_aggregator/scrapers/reddit_jobs.py`

- [ ] **Step 1: Write failing test for full scrape with filtering**

Add to `tests/test_reddit_jobs.py`:

```python
@responses.activate
@patch.dict(os.environ, {"REDDIT_CLIENT_ID": "test-id", "REDDIT_CLIENT_SECRET": "test-secret"})
def test_scrape_filters_and_parses():
    listing = {
        "data": {
            "after": None,
            "children": [
                # Tier 1 hiring post — should be kept
                {
                    "data": {
                        "title": "[Hiring] Backend Engineer | Acme Corp | Remote",
                        "selftext": "We need a backend engineer. Python, AWS. $140K-$170K. Apply at acme.io/careers",
                        "author": "acme_hr",
                        "subreddit": "forhire",
                        "permalink": "/r/forhire/comments/aaa/hiring_backend/",
                        "created_utc": 1743897600.0,
                        "link_flair_text": "Hiring",
                    }
                },
                # [For Hire] post — should be skipped
                {
                    "data": {
                        "title": "[For Hire] Experienced React dev available",
                        "selftext": "I'm available for contract work.",
                        "author": "freelancer_joe",
                        "subreddit": "forhire",
                        "permalink": "/r/forhire/comments/bbb/for_hire_react/",
                        "created_utc": 1743897500.0,
                        "link_flair_text": "For Hire",
                    }
                },
                # AutoModerator — should be skipped
                {
                    "data": {
                        "title": "Weekly discussion thread",
                        "selftext": "Post your questions here.",
                        "author": "AutoModerator",
                        "subreddit": "forhire",
                        "permalink": "/r/forhire/comments/ccc/weekly/",
                        "created_utc": 1743897400.0,
                        "link_flair_text": None,
                    }
                },
                # Tier 2 with hiring signal — should be kept
                {
                    "data": {
                        "title": "We're hiring a data scientist",
                        "selftext": "Join our ML team at DataCo. Remote friendly.",
                        "author": "dataco_eng",
                        "subreddit": "datascience",
                        "permalink": "/r/datascience/comments/ddd/hiring_ds/",
                        "created_utc": 1743897300.0,
                        "link_flair_text": None,
                    }
                },
                # Tier 2 without hiring signal — should be skipped
                {
                    "data": {
                        "title": "Best Python libraries for data viz?",
                        "selftext": "I'm comparing matplotlib vs plotly.",
                        "author": "student_anna",
                        "subreddit": "datascience",
                        "permalink": "/r/datascience/comments/eee/python_viz/",
                        "created_utc": 1743897200.0,
                        "link_flair_text": None,
                    }
                },
                # Deleted post — should be skipped
                {
                    "data": {
                        "title": "[Hiring] Something good",
                        "selftext": "[deleted]",
                        "author": None,
                        "subreddit": "forhire",
                        "permalink": "/r/forhire/comments/fff/deleted/",
                        "created_utc": 1743897100.0,
                        "link_flair_text": "Hiring",
                    }
                },
            ],
        }
    }

    responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
    responses.add(
        responses.GET,
        re.compile(r"https://oauth\.reddit\.com/r/.+/new\.json"),
        json=listing,
        status=200,
    )

    scraper = RedditJobsScraper()
    jobs = scraper.scrape(["any"])

    assert len(jobs) == 2
    assert jobs[0].source == "reddit"
    assert jobs[0].title == "[Hiring] Backend Engineer | Acme Corp | Remote"
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].job_url == "https://reddit.com/r/forhire/comments/aaa/hiring_backend/"
    assert jobs[0].is_remote is True
    assert jobs[0].salary_min == 140000
    assert jobs[0].salary_max == 170000

    assert jobs[1].company == "r/datascience"  # fallback — no pipe format in title
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reddit_jobs.py::test_scrape_filters_and_parses -v`
Expected: FAIL — `assert len([]) == 2` (stub `_parse_post` returns `None`)

- [ ] **Step 3: Implement `_parse_post` with filtering**

Replace the stub `_parse_post` in `board_aggregator/scrapers/reddit_jobs.py`:

```python
def _parse_post(self, post: dict) -> JobPosting | None:
    title = post.get("title", "")
    selftext = post.get("selftext", "")
    author = post.get("author") or ""
    subreddit = post.get("subreddit", "")
    flair = post.get("link_flair_text") or ""

    # Skip rules
    if author == "AutoModerator":
        return None
    if selftext in ("[removed]", "[deleted]"):
        return None
    if re.search(r"\[for\s*hire\]", title, re.IGNORECASE) or "for hire" in flair.lower():
        return None

    # Tier 2 filtering: require hiring signal
    if subreddit.lower() not in {s.lower() for s in TIER_1_SUBS}:
        combined = f"{title} {selftext}"
        if not HIRING_SIGNAL.search(combined):
            return None

    # Company extraction
    company = self._extract_company(title, subreddit)

    # Remote detection
    combined = f"{title} {selftext}"
    is_remote = bool(re.search(r"\bremote\b", combined, re.IGNORECASE))

    # Salary extraction ($140K-$170K pattern)
    salary_match = re.search(r"\$(\d{2,3})[Kk]\s*[-\u2013]\s*\$?(\d{2,3})[Kk]", combined)
    salary_min = int(salary_match.group(1)) * 1000 if salary_match else None
    salary_max = int(salary_match.group(2)) * 1000 if salary_match else None

    # Date
    created_utc = post.get("created_utc")
    date_posted = None
    if created_utc:
        date_posted = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d")

    permalink = post.get("permalink", "")
    job_url = f"https://reddit.com{permalink}" if permalink else ""

    return JobPosting(
        title=title,
        company=company,
        source=self.name,
        job_url=job_url,
        location=None,
        is_remote=is_remote,
        salary_min=salary_min,
        salary_max=salary_max,
        date_posted=date_posted,
        description=selftext[:500] if selftext else None,
    )

def _extract_company(self, title: str, subreddit: str) -> str:
    # 1. Pipe-separated: "Company | Role | Location"
    parts = [p.strip() for p in title.split("|")]
    if len(parts) >= 2:
        # Strip common prefixes like "[Hiring]"
        candidate = re.sub(r"^\[.*?\]\s*", "", parts[0]).strip()
        if candidate:
            return candidate

    # 2. Bracketed: "[Company Name]" but not [Hiring]/[For Hire]
    bracket_match = re.search(r"\[([^\]]+)\]", title)
    if bracket_match:
        val = bracket_match.group(1)
        if val.lower() not in ("hiring", "for hire"):
            return val

    # 3. Bold markdown: "**Company Name**"
    bold_match = re.search(r"\*\*(.+?)\*\*", title)
    if bold_match:
        return bold_match.group(1)

    # 4. Preposition: "at Company" or "@ Company"
    at_match = re.search(r"(?:at|@)\s+([A-Z][\w\s&.]+)", title)
    if at_match:
        return at_match.group(1).strip()

    # 5. Fallback
    return f"r/{subreddit}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reddit_jobs.py::test_scrape_filters_and_parses -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/scrapers/reddit_jobs.py tests/test_reddit_jobs.py
git commit -m "feat(reddit): implement post filtering and parsing with company extraction"
```

---

### Task 4: Edge Case Tests

**Files:**
- Modify: `tests/test_reddit_jobs.py`

- [ ] **Step 1: Write test for missing credentials returning empty list from scrape()**

Add to `tests/test_reddit_jobs.py`:

```python
@patch.dict(os.environ, {}, clear=True)
def test_scrape_missing_credentials_returns_empty():
    scraper = RedditJobsScraper()
    jobs = scraper.scrape(["any"])
    assert jobs == []
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest tests/test_reddit_jobs.py::test_scrape_missing_credentials_returns_empty -v`
Expected: PASS

- [ ] **Step 3: Write test for 429 retry on listing fetch**

Add to `tests/test_reddit_jobs.py`:

```python
@responses.activate
@patch.dict(os.environ, {"REDDIT_CLIENT_ID": "test-id", "REDDIT_CLIENT_SECRET": "test-secret"})
def test_fetch_listings_retries_on_429():
    responses.add(responses.POST, TOKEN_URL, json=TOKEN_RESPONSE, status=200)
    # First call returns 429, second returns data
    responses.add(
        responses.GET,
        re.compile(r"https://oauth\.reddit\.com/r/.+/new\.json"),
        json={"error": "rate limited"},
        status=429,
    )
    responses.add(
        responses.GET,
        re.compile(r"https://oauth\.reddit\.com/r/.+/new\.json"),
        json={
            "data": {
                "after": None,
                "children": [
                    {
                        "data": {
                            "title": "[Hiring] Test role",
                            "selftext": "A job post.",
                            "author": "poster",
                            "subreddit": "hiring",
                            "permalink": "/r/hiring/comments/xyz/test/",
                            "created_utc": 1743897600.0,
                            "link_flair_text": "Hiring",
                        }
                    }
                ],
            }
        },
        status=200,
    )

    scraper = RedditJobsScraper()
    token = scraper._get_token()
    posts = scraper._fetch_listings(token)

    assert len(posts) == 1
    # Should have made 3 GET requests: 1 x 429 + 1 x 200
    get_calls = [c for c in responses.calls if c.request.method == "GET"]
    assert len(get_calls) == 2
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reddit_jobs.py::test_fetch_listings_retries_on_429 -v`
Expected: PASS

- [ ] **Step 5: Write test for company extraction patterns**

Add to `tests/test_reddit_jobs.py`:

```python
def test_extract_company_pipe_format():
    scraper = RedditJobsScraper()
    assert scraper._extract_company("[Hiring] Acme Corp | Backend Dev | Remote", "forhire") == "Acme Corp"


def test_extract_company_bracket_format():
    scraper = RedditJobsScraper()
    assert scraper._extract_company("Looking for devs [TechStartup]", "webdev") == "TechStartup"


def test_extract_company_bold_format():
    scraper = RedditJobsScraper()
    assert scraper._extract_company("**MegaCorp** is hiring engineers", "hiring") == "MegaCorp"


def test_extract_company_at_format():
    scraper = RedditJobsScraper()
    assert scraper._extract_company("Senior engineer at CloudBase", "remotejobs") == "CloudBase"


def test_extract_company_fallback():
    scraper = RedditJobsScraper()
    assert scraper._extract_company("Need help with my project", "webdev") == "r/webdev"
```

- [ ] **Step 6: Run all tests**

Run: `python -m pytest tests/test_reddit_jobs.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add tests/test_reddit_jobs.py
git commit -m "test(reddit): add edge case tests for retry, credentials, company extraction"
```

---

### Task 5: CLI Wiring and Full Run

**Files:**
- Modify: `board_aggregator/cli.py:64`

- [ ] **Step 1: Add import to cli.py**

Add after line 64 (the `remoteok` import) in `board_aggregator/cli.py`:

```python
    import board_aggregator.scrapers.reddit_jobs  # noqa: F401
```

- [ ] **Step 2: Verify scraper appears in registry**

Run: `python -m board_aggregator.cli --list-scrapers`
Expected: `reddit` appears in the list

- [ ] **Step 3: Run all project tests**

Run: `python -m pytest tests/ -v`
Expected: All PASS (existing + new)

- [ ] **Step 4: Commit**

```bash
git add board_aggregator/cli.py
git commit -m "feat(reddit): wire reddit scraper into CLI registry"
```
