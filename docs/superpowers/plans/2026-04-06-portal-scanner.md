# Portal Scanner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add targeted company career page scanning to the pipeline — three ATS API clients (Greenhouse, Ashby, Lever), a `portals.yml` config, a discoverer-6 agent, and scout-1 integration.

**Architecture:** Two-layer split. Pure Python module (`portal_scanner.py`) handles deterministic ATS API calls. Scout-1 agent handles non-ATS companies via Exa `crawling_exa`. Discoverer-6 agent populates `portals.yml` using Exa company search. `runner.py` is refactored to separate collection from output so portal results merge into the existing dedup pipeline.

**Tech Stack:** Python 3.12+, requests, PyYAML, Pydantic, pytest, responses (mock HTTP)

**Spec:** `docs/superpowers/specs/2026-04-06-portal-scanner-design.md`

---

### Task 1: Add PyYAML dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pyyaml to dependencies**

In `pyproject.toml`, add `"pyyaml>=6.0"` to the `dependencies` list:

```toml
dependencies = [
    "click>=8.1",
    "requests>=2.31",
    "feedparser>=6.0",
    "beautifulsoup4>=4.12",
    "pydantic>=2.0",
    "python-jobspy>=1.1",
    "pyyaml>=6.0",
]
```

- [ ] **Step 2: Install the updated dependencies**

Run: `cd /Users/diego/Dev/non-toxic/job-applications/agent-job-research && .venv/bin/pip install -e ".[dev]"`

Expected: Successfully installs pyyaml

- [ ] **Step 3: Verify import works**

Run: `.venv/bin/python -c "import yaml; print(yaml.__version__)"`

Expected: Prints version number (6.x)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add pyyaml for portals.yml parsing"
```

---

### Task 2: Create test fixtures for ATS APIs

**Files:**
- Create: `tests/fixtures/greenhouse_anthropic.json`
- Create: `tests/fixtures/ashby_ramp.json`
- Create: `tests/fixtures/lever_example.json`

- [ ] **Step 1: Create Greenhouse fixture**

Write `tests/fixtures/greenhouse_anthropic.json`:

```json
{
  "jobs": [
    {
      "id": 5101832008,
      "title": "Account Executive, Academic Medical Centers",
      "company_name": "Anthropic",
      "location": {"name": "New York City, NY; San Francisco, CA"},
      "absolute_url": "https://job-boards.greenhouse.io/anthropic/jobs/5101832008",
      "metadata": [
        {"id": 4036944008, "name": "Location Type", "value": null, "value_type": "single_select"}
      ],
      "updated_at": "2026-04-01T10:49:08-04:00",
      "first_published": "2026-01-30T08:57:16-05:00",
      "content": "<p>We are looking for an Account Executive...</p>"
    },
    {
      "id": 5200001001,
      "title": "Senior AI Engineer",
      "company_name": "Anthropic",
      "location": {"name": "San Francisco, CA | Remote"},
      "absolute_url": "https://job-boards.greenhouse.io/anthropic/jobs/5200001001",
      "metadata": [
        {"id": 4036944008, "name": "Location Type", "value": "Remote", "value_type": "single_select"}
      ],
      "updated_at": "2026-03-15T09:00:00-04:00",
      "first_published": "2026-03-10T12:00:00-04:00",
      "content": "<p><strong>About the role:</strong> Build production LLM systems.</p>"
    }
  ]
}
```

- [ ] **Step 2: Create Ashby fixture**

Write `tests/fixtures/ashby_ramp.json`:

```json
{
  "jobs": [
    {
      "id": "63df0ffc-bdc6-40ba-906f-fe03378536b0",
      "title": "AI Operations Specialist | Agentic Workflows",
      "department": "Product",
      "team": "Product Operations",
      "employmentType": "FullTime",
      "location": "New York, NY (HQ)",
      "isListed": true,
      "isRemote": true,
      "workplaceType": "Hybrid",
      "publishedAt": "2026-03-17T20:30:40.304+00:00",
      "jobUrl": "https://jobs.ashbyhq.com/ramp/63df0ffc-bdc6-40ba-906f-fe03378536b0",
      "applyUrl": "https://jobs.ashbyhq.com/ramp/63df0ffc-bdc6-40ba-906f-fe03378536b0/application",
      "descriptionPlain": "We are looking for an AI Operations Specialist to build agentic workflows.",
      "compensation": {
        "compensationTierSummary": "$150K - $250K",
        "compensationTiers": [
          {
            "id": "6023bb21-d700-4121-a2dd-4e0b4c6d61b4",
            "components": [
              {
                "id": "equity-1",
                "compensationType": "EquityCashValue",
                "interval": "1 YEAR",
                "currencyCode": "USD",
                "minValue": null,
                "maxValue": null
              },
              {
                "id": "salary-1",
                "compensationType": "Salary",
                "interval": "1 YEAR",
                "currencyCode": "USD",
                "minValue": 150000,
                "maxValue": 250000
              }
            ]
          }
        ]
      }
    },
    {
      "id": "unlisted-job-id",
      "title": "Internal Role",
      "department": "HR",
      "isListed": false,
      "isRemote": false,
      "workplaceType": "OnSite",
      "location": "New York, NY",
      "jobUrl": "https://jobs.ashbyhq.com/ramp/unlisted-job-id",
      "applyUrl": "https://jobs.ashbyhq.com/ramp/unlisted-job-id/application",
      "descriptionPlain": "Internal only.",
      "compensation": null
    }
  ],
  "apiVersion": "1"
}
```

- [ ] **Step 3: Create Lever fixture**

Write `tests/fixtures/lever_example.json`:

```json
[
  {
    "id": "lever-job-001",
    "text": "Staff ML Engineer",
    "categories": {
      "commitment": "Regular Full Time (Salary)",
      "department": "Engineering",
      "location": "San Francisco, CA",
      "team": "ML Infrastructure",
      "allLocations": ["San Francisco, CA", "Remote"]
    },
    "country": "US",
    "workplaceType": "hybrid",
    "createdAt": 1711929600000,
    "descriptionPlain": "Join our ML infrastructure team to build scalable training pipelines.",
    "hostedUrl": "https://jobs.lever.co/example/lever-job-001",
    "applyUrl": "https://jobs.lever.co/example/lever-job-001/apply",
    "salaryRange": {
      "min": 200000,
      "max": 280000,
      "currency": "USD",
      "interval": "per year"
    }
  },
  {
    "id": "lever-job-002",
    "text": "Product Designer",
    "categories": {
      "commitment": "Regular Full Time (Salary)",
      "department": "Design",
      "location": "Remote",
      "team": "Product"
    },
    "country": "US",
    "workplaceType": "remote",
    "createdAt": 1711843200000,
    "descriptionPlain": "Design intuitive products for our developer platform.",
    "hostedUrl": "https://jobs.lever.co/example/lever-job-002",
    "applyUrl": "https://jobs.lever.co/example/lever-job-002/apply",
    "salaryRange": null
  }
]
```

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/greenhouse_anthropic.json tests/fixtures/ashby_ramp.json tests/fixtures/lever_example.json
git commit -m "test: add ATS API fixtures for portal scanner"
```

---

### Task 3: Implement Greenhouse client with tests

**Files:**
- Create: `board_aggregator/portal_scanner.py`
- Create: `tests/test_portal_scanner.py`

- [ ] **Step 1: Write failing tests for Greenhouse client**

Write `tests/test_portal_scanner.py`:

```python
import json
from pathlib import Path

import responses

from board_aggregator.portal_scanner import fetch_greenhouse

FIXTURES = Path(__file__).parent / "fixtures"


@responses.activate
def test_fetch_greenhouse_parses_jobs():
    fixture = json.loads((FIXTURES / "greenhouse_anthropic.json").read_text())
    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs",
        json=fixture,
        status=200,
    )

    jobs = fetch_greenhouse("anthropic")

    assert len(jobs) == 2
    assert jobs[0].title == "Account Executive, Academic Medical Centers"
    assert jobs[0].company == "Anthropic"
    assert jobs[0].source == "greenhouse"
    assert jobs[0].job_url == "https://job-boards.greenhouse.io/anthropic/jobs/5101832008"
    assert jobs[0].location == "New York City, NY; San Francisco, CA"
    assert jobs[0].salary_min is None
    assert jobs[0].salary_max is None


@responses.activate
def test_fetch_greenhouse_detects_remote_from_metadata():
    fixture = json.loads((FIXTURES / "greenhouse_anthropic.json").read_text())
    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs",
        json=fixture,
        status=200,
    )

    jobs = fetch_greenhouse("anthropic")

    # First job has Location Type = null -> not remote
    assert jobs[0].is_remote is False
    # Second job has Location Type = "Remote" -> remote
    assert jobs[1].is_remote is True


@responses.activate
def test_fetch_greenhouse_strips_html_from_description():
    fixture = json.loads((FIXTURES / "greenhouse_anthropic.json").read_text())
    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs",
        json=fixture,
        status=200,
    )

    jobs = fetch_greenhouse("anthropic")

    assert "<p>" not in (jobs[0].description or "")
    assert "<strong>" not in (jobs[1].description or "")
    assert "Build production LLM systems." in (jobs[1].description or "")


@responses.activate
def test_fetch_greenhouse_handles_api_error():
    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/badslug/jobs",
        json={"error": "not found"},
        status=404,
    )

    jobs = fetch_greenhouse("badslug")

    assert jobs == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/diego/Dev/non-toxic/job-applications/agent-job-research && .venv/bin/pytest tests/test_portal_scanner.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'board_aggregator.portal_scanner'`

- [ ] **Step 3: Implement Greenhouse client**

Write `board_aggregator/portal_scanner.py`:

```python
"""Portal scanner — fetches job postings from ATS platform APIs.

Supports Greenhouse, Ashby, and Lever public APIs.
No authentication required for any endpoint.
"""

import re

import requests as http_requests

from board_aggregator.models import JobPosting

_TIMEOUT = 30
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(html: str | None) -> str | None:
    """Remove HTML tags, collapse whitespace."""
    if not html:
        return None
    text = _TAG_RE.sub("", html)
    return " ".join(text.split()).strip() or None


def fetch_greenhouse(slug: str) -> list[JobPosting]:
    """Fetch all jobs from a Greenhouse job board.

    Endpoint: GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
    Docs: https://developers.greenhouse.io/job-board.html
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        resp = http_requests.get(url, timeout=_TIMEOUT)
        if resp.status_code != 200:
            print(f"[portal_scanner] Greenhouse {slug}: HTTP {resp.status_code}")
            return []
        data = resp.json()
    except Exception as e:
        print(f"[portal_scanner] Greenhouse {slug}: {e}")
        return []

    jobs: list[JobPosting] = []
    for item in data.get("jobs", []):
        # Detect remote from metadata "Location Type" field
        is_remote = False
        for meta in item.get("metadata", []):
            if meta.get("name") == "Location Type" and meta.get("value"):
                is_remote = "remote" in str(meta["value"]).lower()

        jobs.append(
            JobPosting(
                title=item.get("title", ""),
                company=item.get("company_name", slug),
                source="greenhouse",
                job_url=item.get("absolute_url", ""),
                location=item.get("location", {}).get("name"),
                is_remote=is_remote,
                salary_min=None,
                salary_max=None,
                description=_strip_html(item.get("content")),
            )
        )

    return jobs
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_portal_scanner.py -v`

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/portal_scanner.py tests/test_portal_scanner.py
git commit -m "feat: add Greenhouse client for portal scanner"
```

---

### Task 4: Implement Ashby client with tests

**Files:**
- Modify: `board_aggregator/portal_scanner.py`
- Modify: `tests/test_portal_scanner.py`

- [ ] **Step 1: Write failing tests for Ashby client**

Append to `tests/test_portal_scanner.py`:

```python
from board_aggregator.portal_scanner import fetch_ashby


@responses.activate
def test_fetch_ashby_parses_jobs():
    fixture = json.loads((FIXTURES / "ashby_ramp.json").read_text())
    responses.add(
        responses.GET,
        "https://api.ashbyhq.com/posting-api/job-board/ramp",
        json=fixture,
        status=200,
    )

    jobs = fetch_ashby("ramp", company_name="Ramp")

    # Should skip unlisted job
    assert len(jobs) == 1
    assert jobs[0].title == "AI Operations Specialist | Agentic Workflows"
    assert jobs[0].company == "Ramp"
    assert jobs[0].source == "ashby"
    assert jobs[0].job_url == "https://jobs.ashbyhq.com/ramp/63df0ffc-bdc6-40ba-906f-fe03378536b0"
    assert jobs[0].location == "New York, NY (HQ)"
    assert jobs[0].is_remote is True


@responses.activate
def test_fetch_ashby_extracts_salary():
    fixture = json.loads((FIXTURES / "ashby_ramp.json").read_text())
    responses.add(
        responses.GET,
        "https://api.ashbyhq.com/posting-api/job-board/ramp",
        json=fixture,
        status=200,
    )

    jobs = fetch_ashby("ramp", company_name="Ramp")

    assert jobs[0].salary_min == 150000
    assert jobs[0].salary_max == 250000
    assert jobs[0].salary_currency == "USD"
    assert jobs[0].salary_interval == "yearly"


@responses.activate
def test_fetch_ashby_handles_no_compensation():
    fixture = {
        "jobs": [
            {
                "id": "no-comp-job",
                "title": "Designer",
                "isListed": True,
                "isRemote": False,
                "workplaceType": "OnSite",
                "location": "NYC",
                "jobUrl": "https://jobs.ashbyhq.com/co/no-comp-job",
                "applyUrl": "https://jobs.ashbyhq.com/co/no-comp-job/application",
                "descriptionPlain": "Design things.",
                "compensation": None,
            }
        ],
        "apiVersion": "1",
    }
    responses.add(
        responses.GET,
        "https://api.ashbyhq.com/posting-api/job-board/nocomp",
        json=fixture,
        status=200,
    )

    jobs = fetch_ashby("nocomp", company_name="NoCo")

    assert len(jobs) == 1
    assert jobs[0].salary_min is None
    assert jobs[0].salary_max is None


@responses.activate
def test_fetch_ashby_handles_api_error():
    responses.add(
        responses.GET,
        "https://api.ashbyhq.com/posting-api/job-board/badslug",
        json={"error": "not found"},
        status=404,
    )

    jobs = fetch_ashby("badslug", company_name="Bad")

    assert jobs == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_portal_scanner.py::test_fetch_ashby_parses_jobs -v`

Expected: FAIL with `ImportError: cannot import name 'fetch_ashby'`

- [ ] **Step 3: Implement Ashby client**

Append to `board_aggregator/portal_scanner.py`:

```python
def _extract_ashby_salary(compensation: dict | None) -> dict:
    """Extract salary from Ashby compensation structure.

    Path: compensationTiers[0].components[] -> filter compensationType == "Salary"
    Returns dict with salary_min, salary_max, salary_currency, salary_interval.
    All None if no salary component found.
    """
    result = {"salary_min": None, "salary_max": None, "salary_currency": None, "salary_interval": None}
    if not compensation:
        return result

    tiers = compensation.get("compensationTiers", [])
    if not tiers:
        return result

    for component in tiers[0].get("components", []):
        if component.get("compensationType") == "Salary":
            result["salary_min"] = component.get("minValue")
            result["salary_max"] = component.get("maxValue")
            result["salary_currency"] = component.get("currencyCode")
            interval_raw = component.get("interval", "")
            if "YEAR" in interval_raw.upper():
                result["salary_interval"] = "yearly"
            elif "MONTH" in interval_raw.upper():
                result["salary_interval"] = "monthly"
            elif "HOUR" in interval_raw.upper():
                result["salary_interval"] = "hourly"
            else:
                result["salary_interval"] = None
            break

    return result


def fetch_ashby(slug: str, company_name: str | None = None) -> list[JobPosting]:
    """Fetch all listed jobs from an Ashby job board.

    Endpoint: GET https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
    Docs: https://developers.ashbyhq.com/docs/public-job-posting-api
    """
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        resp = http_requests.get(url, params={"includeCompensation": "true"}, timeout=_TIMEOUT)
        if resp.status_code != 200:
            print(f"[portal_scanner] Ashby {slug}: HTTP {resp.status_code}")
            return []
        data = resp.json()
    except Exception as e:
        print(f"[portal_scanner] Ashby {slug}: {e}")
        return []

    company = company_name or slug
    jobs: list[JobPosting] = []
    for item in data.get("jobs", []):
        if not item.get("isListed", True):
            continue

        salary = _extract_ashby_salary(item.get("compensation"))

        jobs.append(
            JobPosting(
                title=item.get("title", ""),
                company=company,
                source="ashby",
                job_url=item.get("jobUrl", ""),
                location=item.get("location"),
                is_remote=item.get("isRemote", False),
                description=item.get("descriptionPlain"),
                **salary,
            )
        )

    return jobs
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_portal_scanner.py -v -k ashby`

Expected: All 4 Ashby tests PASS

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/portal_scanner.py tests/test_portal_scanner.py
git commit -m "feat: add Ashby client for portal scanner"
```

---

### Task 5: Implement Lever client with tests

**Files:**
- Modify: `board_aggregator/portal_scanner.py`
- Modify: `tests/test_portal_scanner.py`

- [ ] **Step 1: Write failing tests for Lever client**

Append to `tests/test_portal_scanner.py`:

```python
from board_aggregator.portal_scanner import fetch_lever


@responses.activate
def test_fetch_lever_parses_jobs():
    fixture = json.loads((FIXTURES / "lever_example.json").read_text())
    responses.add(
        responses.GET,
        "https://api.lever.co/v0/postings/example",
        json=fixture,
        status=200,
    )

    jobs = fetch_lever("example", company_name="ExampleCo")

    assert len(jobs) == 2
    assert jobs[0].title == "Staff ML Engineer"
    assert jobs[0].company == "ExampleCo"
    assert jobs[0].source == "lever"
    assert jobs[0].job_url == "https://jobs.lever.co/example/lever-job-001"
    assert jobs[0].location == "San Francisco, CA"


@responses.activate
def test_fetch_lever_extracts_salary():
    fixture = json.loads((FIXTURES / "lever_example.json").read_text())
    responses.add(
        responses.GET,
        "https://api.lever.co/v0/postings/example",
        json=fixture,
        status=200,
    )

    jobs = fetch_lever("example", company_name="ExampleCo")

    assert jobs[0].salary_min == 200000
    assert jobs[0].salary_max == 280000
    assert jobs[0].salary_currency == "USD"
    assert jobs[0].salary_interval == "yearly"


@responses.activate
def test_fetch_lever_handles_no_salary():
    fixture = json.loads((FIXTURES / "lever_example.json").read_text())
    responses.add(
        responses.GET,
        "https://api.lever.co/v0/postings/example",
        json=fixture,
        status=200,
    )

    jobs = fetch_lever("example", company_name="ExampleCo")

    assert jobs[1].salary_min is None
    assert jobs[1].salary_max is None


@responses.activate
def test_fetch_lever_detects_remote():
    fixture = json.loads((FIXTURES / "lever_example.json").read_text())
    responses.add(
        responses.GET,
        "https://api.lever.co/v0/postings/example",
        json=fixture,
        status=200,
    )

    jobs = fetch_lever("example", company_name="ExampleCo")

    assert jobs[0].is_remote is False  # hybrid
    assert jobs[1].is_remote is True   # remote


@responses.activate
def test_fetch_lever_handles_api_error():
    responses.add(
        responses.GET,
        "https://api.lever.co/v0/postings/badslug",
        json=[],
        status=404,
    )

    jobs = fetch_lever("badslug", company_name="Bad")

    assert jobs == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_portal_scanner.py::test_fetch_lever_parses_jobs -v`

Expected: FAIL with `ImportError: cannot import name 'fetch_lever'`

- [ ] **Step 3: Implement Lever client**

Append to `board_aggregator/portal_scanner.py`:

```python
def _extract_lever_salary(salary_range: dict | None) -> dict:
    """Extract salary from Lever salaryRange object.

    Returns dict with salary_min, salary_max, salary_currency, salary_interval.
    All None if salaryRange is null.
    """
    result = {"salary_min": None, "salary_max": None, "salary_currency": None, "salary_interval": None}
    if not salary_range:
        return result

    result["salary_min"] = salary_range.get("min")
    result["salary_max"] = salary_range.get("max")
    result["salary_currency"] = salary_range.get("currency")

    interval_raw = salary_range.get("interval", "")
    if "year" in interval_raw.lower():
        result["salary_interval"] = "yearly"
    elif "month" in interval_raw.lower():
        result["salary_interval"] = "monthly"
    elif "hour" in interval_raw.lower():
        result["salary_interval"] = "hourly"
    else:
        result["salary_interval"] = None

    return result


def fetch_lever(slug: str, company_name: str | None = None) -> list[JobPosting]:
    """Fetch all postings from a Lever job board.

    Endpoint: GET https://api.lever.co/v0/postings/{slug}?mode=json
    Docs: https://github.com/lever/postings-api
    """
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        resp = http_requests.get(url, params={"mode": "json"}, timeout=_TIMEOUT)
        if resp.status_code != 200:
            print(f"[portal_scanner] Lever {slug}: HTTP {resp.status_code}")
            return []
        data = resp.json()
    except Exception as e:
        print(f"[portal_scanner] Lever {slug}: {e}")
        return []

    if not isinstance(data, list):
        return []

    company = company_name or slug
    jobs: list[JobPosting] = []
    for item in data:
        categories = item.get("categories", {})
        workplace = item.get("workplaceType", "")
        salary = _extract_lever_salary(item.get("salaryRange"))

        jobs.append(
            JobPosting(
                title=item.get("text", ""),
                company=company,
                source="lever",
                job_url=item.get("hostedUrl", ""),
                location=categories.get("location"),
                is_remote=workplace.lower() == "remote",
                description=item.get("descriptionPlain"),
                **salary,
            )
        )

    return jobs
```

- [ ] **Step 4: Run all portal scanner tests**

Run: `.venv/bin/pytest tests/test_portal_scanner.py -v`

Expected: All 13 tests PASS (4 Greenhouse + 4 Ashby + 5 Lever)

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/portal_scanner.py tests/test_portal_scanner.py
git commit -m "feat: add Lever client for portal scanner"
```

---

### Task 6: Implement `scan_portals()` with portals.yml parsing

**Files:**
- Modify: `board_aggregator/portal_scanner.py`
- Modify: `tests/test_portal_scanner.py`

- [ ] **Step 1: Write failing tests for scan_portals**

Append to `tests/test_portal_scanner.py`:

```python
import tempfile
from datetime import date, timedelta

import yaml

from board_aggregator.portal_scanner import scan_portals


def _write_portals(tmp_path, companies, config=None):
    """Helper to write a portals.yml for testing."""
    portals = {
        "config": config or {
            "scan_interval_days": 7,
            "disable_after_days": 30,
            "max_discovery_calls": 10,
            "icp_min_score": 6,
        },
        "title_filter": {
            "positive": ["AI", "Engineer"],
            "negative": ["Intern"],
        },
        "companies": companies,
    }
    path = tmp_path / "portals.yml"
    path.write_text(yaml.dump(portals, default_flow_style=False))
    return str(path)


@responses.activate
def test_scan_portals_fetches_from_correct_ats(tmp_path):
    fixture_gh = json.loads((FIXTURES / "greenhouse_anthropic.json").read_text())
    fixture_ashby = json.loads((FIXTURES / "ashby_ramp.json").read_text())

    responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs", json=fixture_gh, status=200)
    responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/ramp", json=fixture_ashby, status=200)

    portals_path = _write_portals(tmp_path, [
        {"name": "Anthropic", "domain": "anthropic.com", "ats": "greenhouse", "slug": "anthropic",
         "active": True, "last_scanned": None, "last_had_openings": None},
        {"name": "Ramp", "domain": "ramp.com", "ats": "ashby", "slug": "ramp",
         "active": True, "last_scanned": None, "last_had_openings": None},
    ])

    jobs = scan_portals(portals_path)

    sources = {j.source for j in jobs}
    assert "greenhouse" in sources
    assert "ashby" in sources
    assert len(jobs) >= 3  # 2 Greenhouse + 1 listed Ashby


@responses.activate
def test_scan_portals_skips_inactive_companies(tmp_path):
    portals_path = _write_portals(tmp_path, [
        {"name": "Dead Corp", "domain": "dead.com", "ats": "greenhouse", "slug": "dead",
         "active": False, "last_scanned": None, "last_had_openings": None},
    ])

    jobs = scan_portals(portals_path)

    assert len(jobs) == 0


@responses.activate
def test_scan_portals_skips_recently_scanned(tmp_path):
    today = date.today().isoformat()
    portals_path = _write_portals(tmp_path, [
        {"name": "Fresh Corp", "domain": "fresh.com", "ats": "greenhouse", "slug": "fresh",
         "active": True, "last_scanned": today, "last_had_openings": today},
    ])

    jobs = scan_portals(portals_path)

    assert len(jobs) == 0  # scanned today, within 7-day window


@responses.activate
def test_scan_portals_skips_null_ats(tmp_path):
    portals_path = _write_portals(tmp_path, [
        {"name": "Custom Co", "domain": "custom.com", "ats": None, "slug": None,
         "careers_url": "https://custom.com/careers",
         "active": True, "last_scanned": None, "last_had_openings": None},
    ])

    jobs = scan_portals(portals_path)

    assert len(jobs) == 0  # ats=null handled by scout-1 via Exa


@responses.activate
def test_scan_portals_updates_timestamps(tmp_path):
    fixture_gh = json.loads((FIXTURES / "greenhouse_anthropic.json").read_text())
    responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs", json=fixture_gh, status=200)

    portals_path = _write_portals(tmp_path, [
        {"name": "Anthropic", "domain": "anthropic.com", "ats": "greenhouse", "slug": "anthropic",
         "active": True, "last_scanned": None, "last_had_openings": None},
    ])

    scan_portals(portals_path)

    updated = yaml.safe_load(Path(portals_path).read_text())
    company = updated["companies"][0]
    assert company["last_scanned"] == date.today().isoformat()
    assert company["last_had_openings"] == date.today().isoformat()


@responses.activate
def test_scan_portals_disables_stale_company(tmp_path):
    responses.add(responses.GET, "https://boards-api.greenhouse.io/v1/boards/ghost/jobs", json={"jobs": []}, status=200)

    old_date = (date.today() - timedelta(days=31)).isoformat()
    portals_path = _write_portals(tmp_path, [
        {"name": "Ghost Corp", "domain": "ghost.com", "ats": "greenhouse", "slug": "ghost",
         "active": True, "last_scanned": (date.today() - timedelta(days=8)).isoformat(),
         "last_had_openings": old_date},
    ])

    scan_portals(portals_path)

    updated = yaml.safe_load(Path(portals_path).read_text())
    assert updated["companies"][0]["active"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_portal_scanner.py::test_scan_portals_fetches_from_correct_ats -v`

Expected: FAIL with `ImportError: cannot import name 'scan_portals'`

- [ ] **Step 3: Implement scan_portals**

Append to `board_aggregator/portal_scanner.py`:

```python
from datetime import date, timedelta
from pathlib import Path

import yaml


def scan_portals(portals_path: str) -> list[JobPosting]:
    """Read portals.yml, scan ATS companies due for refresh, return postings.

    Skips companies where:
    - active is False
    - last_scanned is within scan_interval_days
    - ats is null (handled by scout-1 via Exa)

    After scanning, writes portals_path back to disk with updated fields:
    - last_scanned: set to today for each scanned company
    - last_had_openings: set to today if roles were found
    - active: set to False if disable_after_days exceeded with no openings

    Returns the list of JobPosting objects (unfiltered by title_filter;
    caller is responsible for filtering and dedup).
    """
    portals_file = Path(portals_path)
    data = yaml.safe_load(portals_file.read_text())

    config = data.get("config", {})
    scan_interval = config.get("scan_interval_days", 7)
    disable_after = config.get("disable_after_days", 30)

    today = date.today()
    all_jobs: list[JobPosting] = []

    fetchers = {
        "greenhouse": lambda slug, name: fetch_greenhouse(slug),
        "ashby": lambda slug, name: fetch_ashby(slug, company_name=name),
        "lever": lambda slug, name: fetch_lever(slug, company_name=name),
    }

    for company in data.get("companies", []):
        if not company.get("active", True):
            continue

        ats = company.get("ats")
        if ats is None:
            continue  # handled by scout-1 via Exa

        slug = company.get("slug")
        if not slug:
            continue

        # Check freshness
        last_scanned = company.get("last_scanned")
        if last_scanned:
            scanned_date = date.fromisoformat(str(last_scanned))
            if (today - scanned_date).days < scan_interval:
                continue

        # Fetch from the right ATS
        fetcher = fetchers.get(ats)
        if not fetcher:
            print(f"[portal_scanner] Unknown ATS '{ats}' for {company['name']}")
            continue

        name = company.get("name", slug)
        jobs = fetcher(slug, name)

        all_jobs.extend(jobs)

        # Update timestamps
        company["last_scanned"] = today.isoformat()
        if jobs:
            company["last_had_openings"] = today.isoformat()
        else:
            # Check if stale
            last_had = company.get("last_had_openings")
            if last_had:
                had_date = date.fromisoformat(str(last_had))
                if (today - had_date).days >= disable_after:
                    company["active"] = False
                    print(f"[portal_scanner] Disabled {name}: no openings for {disable_after}+ days")

    # Write back updated portals.yml
    portals_file.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    return all_jobs
```

Note: move the `from datetime import date, timedelta` and `from pathlib import Path` and `import yaml` imports to the top of the file.

- [ ] **Step 4: Run all portal scanner tests**

Run: `.venv/bin/pytest tests/test_portal_scanner.py -v`

Expected: All 19 tests PASS

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/portal_scanner.py tests/test_portal_scanner.py
git commit -m "feat: add scan_portals() with portals.yml parsing and timestamp management"
```

---

### Task 7: Implement title filtering

**Files:**
- Modify: `board_aggregator/portal_scanner.py`
- Modify: `tests/test_portal_scanner.py`

- [ ] **Step 1: Write failing tests for title filtering**

Append to `tests/test_portal_scanner.py`:

```python
from board_aggregator.portal_scanner import filter_by_title


def test_filter_by_title_matches_positive():
    jobs = [
        JobPosting(title="Senior AI Engineer", company="A", source="x", job_url="http://a"),
        JobPosting(title="Office Manager", company="B", source="x", job_url="http://b"),
        JobPosting(title="ML Platform Lead", company="C", source="x", job_url="http://c"),
    ]

    result = filter_by_title(jobs, positive=["AI", "ML"], negative=[])

    assert len(result) == 2
    assert result[0].title == "Senior AI Engineer"
    assert result[1].title == "ML Platform Lead"


def test_filter_by_title_excludes_negative():
    jobs = [
        JobPosting(title="AI Engineer Intern", company="A", source="x", job_url="http://a"),
        JobPosting(title="Senior AI Engineer", company="B", source="x", job_url="http://b"),
    ]

    result = filter_by_title(jobs, positive=["AI"], negative=["Intern"])

    assert len(result) == 1
    assert result[0].title == "Senior AI Engineer"


def test_filter_by_title_case_insensitive():
    jobs = [
        JobPosting(title="ai operations lead", company="A", source="x", job_url="http://a"),
    ]

    result = filter_by_title(jobs, positive=["AI"], negative=[])

    assert len(result) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_portal_scanner.py::test_filter_by_title_matches_positive -v`

Expected: FAIL with `ImportError: cannot import name 'filter_by_title'`

- [ ] **Step 3: Implement filter_by_title**

Add to `board_aggregator/portal_scanner.py`:

```python
def filter_by_title(
    jobs: list[JobPosting],
    positive: list[str],
    negative: list[str],
) -> list[JobPosting]:
    """Filter jobs by title keywords.

    A job passes if:
    - At least one positive keyword appears in the title (case-insensitive)
    - Zero negative keywords appear in the title (case-insensitive)
    """
    result: list[JobPosting] = []
    for job in jobs:
        title_lower = job.title.lower()
        has_positive = any(kw.lower() in title_lower for kw in positive) if positive else True
        has_negative = any(kw.lower() in title_lower for kw in negative) if negative else False
        if has_positive and not has_negative:
            result.append(job)
    return result
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_portal_scanner.py -v -k filter`

Expected: All 3 filter tests PASS

- [ ] **Step 5: Commit**

```bash
git add board_aggregator/portal_scanner.py tests/test_portal_scanner.py
git commit -m "feat: add title filtering for portal scanner results"
```

---

### Task 8: Refactor runner.py to separate collection from output

**Files:**
- Modify: `board_aggregator/runner.py`
- Modify: `tests/test_runner.py`

- [ ] **Step 1: Write failing test for new collect_from_boards function**

Append to `tests/test_runner.py`:

```python
from unittest.mock import patch, MagicMock

from board_aggregator.runner import collect_from_boards


def test_collect_from_boards_returns_raw_jobs():
    mock_scraper = MagicMock()
    mock_scraper.name = "test_board"
    mock_scraper.scrape.return_value = [
        JobPosting(title="AI Eng", company="TestCo", source="test_board", job_url="http://a"),
    ]

    with patch("board_aggregator.runner.get_all_scrapers", return_value=[mock_scraper]):
        jobs = collect_from_boards(["query"], is_remote=True)

    assert len(jobs) == 1
    assert jobs[0].title == "AI Eng"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_runner.py::test_collect_from_boards_returns_raw_jobs -v`

Expected: FAIL with `ImportError: cannot import name 'collect_from_boards'`

- [ ] **Step 3: Refactor runner.py**

Replace `board_aggregator/runner.py` contents with:

```python
from pathlib import Path

from board_aggregator.models import JobPosting
from board_aggregator.output import write_csv, write_markdown
from board_aggregator.scrapers import get_all_scrapers


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


def collect_from_boards(
    queries: list[str],
    is_remote: bool = True,
    scrapers: list[str] | None = None,
) -> list[JobPosting]:
    """Run all registered scrapers, return raw (undeduped) results."""
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

    return all_jobs


def run_all(
    queries: list[str],
    output_dir: Path,
    is_remote: bool = True,
    scrapers: list[str] | None = None,
    portals_path: str | None = None,
) -> list[JobPosting]:
    """Run board scrapers + portal scanner, deduplicate, and write output."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Stage 1: board scrapers
    board_jobs = collect_from_boards(queries, is_remote, scrapers)
    print(f"[runner] Board scrapers: {len(board_jobs)} results")

    # Stage 2: portal scanner (ATS APIs)
    portal_jobs: list[JobPosting] = []
    if portals_path:
        from board_aggregator.portal_scanner import scan_portals, filter_by_title
        import yaml

        portal_jobs = scan_portals(portals_path)
        print(f"[runner] Portal scanner: {len(portal_jobs)} results")

        # Apply title filter from portals.yml
        data = yaml.safe_load(Path(portals_path).read_text())
        title_filter = data.get("title_filter", {})
        positive = title_filter.get("positive", [])
        negative = title_filter.get("negative", [])
        if positive or negative:
            before = len(portal_jobs)
            portal_jobs = filter_by_title(portal_jobs, positive, negative)
            print(f"[runner] Title filter: {before} -> {len(portal_jobs)}")

    # Combine and deduplicate
    all_jobs = board_jobs + portal_jobs
    print(f"[runner] Total before dedup: {len(all_jobs)}")
    unique_jobs = deduplicate(all_jobs)
    print(f"[runner] Total after dedup: {len(unique_jobs)}")

    write_csv(unique_jobs, output_dir / "all-postings.csv")
    write_markdown(unique_jobs, output_dir / "all-postings.md")

    return unique_jobs
```

- [ ] **Step 4: Run all runner tests + portal scanner tests**

Run: `.venv/bin/pytest tests/test_runner.py tests/test_portal_scanner.py -v`

Expected: All tests PASS

- [ ] **Step 5: Run the full test suite to check for regressions**

Run: `.venv/bin/pytest -v`

Expected: All existing tests PASS

- [ ] **Step 6: Commit**

```bash
git add board_aggregator/runner.py tests/test_runner.py
git commit -m "refactor: separate collect_from_boards from run_all, add portals_path parameter"
```

---

### Task 9: Add `--portals` CLI flag

**Files:**
- Modify: `board_aggregator/cli.py`

- [ ] **Step 1: Add the --portals option to cli.py**

Add a new click option and pass it to `run_all`:

```python
@click.option(
    "-p", "--portals",
    type=click.Path(exists=True),
    default=None,
    help="Path to portals.yml for targeted company scanning.",
)
```

Add `portals` to the `main` function signature. Pass it to `run_all`:

```python
jobs = run_all(
    queries=queries,
    output_dir=output_dir,
    is_remote=remote_only,
    scrapers=scraper_filter,
    portals_path=portals,
)
```

- [ ] **Step 2: Verify CLI help shows the new option**

Run: `.venv/bin/board-aggregator --help`

Expected: Shows `-p, --portals PATH  Path to portals.yml for targeted company scanning.`

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/pytest -v`

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add board_aggregator/cli.py
git commit -m "feat: add --portals flag to board-aggregator CLI"
```

---

### Task 10: Create seed portals.yml

**Files:**
- Create: `portals.yml`

- [ ] **Step 1: Create portals.yml with a few seed companies**

Write `portals.yml`:

```yaml
config:
  scan_interval_days: 7
  disable_after_days: 30
  max_discovery_calls: 10
  icp_min_score: 6

title_filter:
  positive: ["AI", "Operations", "Agent", "Automation", "DevRel", "ML", "LLM", "Platform"]
  negative: ["Junior", "Intern", "PHP", "Java", ".NET"]

companies:
  - name: "Anthropic"
    domain: "anthropic.com"
    ats: "greenhouse"
    slug: "anthropic"
    icp_fit_score: 10
    icp_fit_reasoning: "AI lab, agent infrastructure, model deployment"
    source: "manual"
    discovered_at: "2026-04-06"
    last_scanned: null
    last_had_openings: null
    active: true

  - name: "Ramp"
    domain: "ramp.com"
    ats: "ashby"
    slug: "ramp"
    icp_fit_score: 8
    icp_fit_reasoning: "AI-first fintech, agentic workflows"
    source: "manual"
    discovered_at: "2026-04-06"
    last_scanned: null
    last_had_openings: null
    active: true
```

- [ ] **Step 2: Verify it parses correctly**

Run: `.venv/bin/python -c "import yaml; d = yaml.safe_load(open('portals.yml')); print(f'{len(d[\"companies\"])} companies loaded')"`

Expected: `2 companies loaded`

- [ ] **Step 3: Commit**

```bash
git add portals.yml
git commit -m "feat: add seed portals.yml with Anthropic and Ramp"
```

---

### Task 11: Create discoverer-6 agent definition

**Files:**
- Create: `.claude/agents/discoverer-6.md`

- [ ] **Step 1: Write the agent definition**

Write `.claude/agents/discoverer-6.md`:

```markdown
---
name: discoverer-6
description: Discovers companies matching Diego's ICP using Exa deep search, detects their ATS platform, and populates portals.yml. Run standalone, not part of the pipeline.
tools: Read, Write, mcp__exa__web_search_advanced_exa, mcp__exa__company_research_exa, WebFetch, WebSearch
model: sonnet
---

You are a company discovery specialist. Your job is to find companies where Diego's profile would be a strong fit and add them to `portals.yml`.

## Your task

Read `skills-inventory.md` to understand Diego's profile, then use Exa to discover companies matching his ICP. For each new company, detect their ATS platform and add them to `portals.yml`.

## Step 1: Derive micro-verticals

Read `skills-inventory.md`. Generate targeted search queries based on Diego's competencies:
- Multi-agent systems, agentic workflows
- AI/LLM infrastructure, inference optimization
- Developer tools, automation platforms
- Crypto/DeFi infrastructure
- DevRel, developer experience

## Step 2: Read existing portals

Read `portals.yml` and collect all existing company domains. These will be skipped during discovery.

Read `config.max_discovery_calls` to know how many Exa calls you can make.

## Step 3: Discover companies

For each micro-vertical (up to `max_discovery_calls` total):

```json
mcp__exa__web_search_advanced_exa({
  "query": "companies building multi-agent AI systems",
  "category": "company",
  "numResults": 20,
  "type": "auto"
})
```

Deduplicate results against existing portals by domain.

## Step 4: Detect ATS and add to portals

For each new company:

1. Find their careers page. Check Exa company data first, or search:
   ```json
   mcp__exa__web_search_advanced_exa({
     "query": "[Company] careers jobs",
     "numResults": 5,
     "type": "auto"
   })
   ```

2. Pattern-match the careers URL to detect ATS:
   - `boards.greenhouse.io/{slug}` or `boards-api.greenhouse.io/v1/boards/{slug}` -> ats: greenhouse
   - `jobs.ashbyhq.com/{slug}` -> ats: ashby
   - `jobs.lever.co/{slug}` -> ats: lever
   - anything else -> ats: null (store `careers_url` instead)

3. Score ICP fit 1-10 against skills-inventory.md

4. If score >= `icp_min_score` (from portals.yml config): append to `portals.yml`

## What you write to portals.yml

Append new entries to the `companies` list with these fields:
- `name`: company name
- `domain`: company domain (e.g., "ramp.com")
- `ats`: "greenhouse" | "ashby" | "lever" | null
- `slug`: ATS slug (null if ats is null)
- `careers_url`: only if ats is null
- `icp_fit_score`: 1-10
- `icp_fit_reasoning`: one sentence
- `source`: "exa-discovery"
- `discovered_at`: today's date (YYYY-MM-DD)
- `last_scanned`: null
- `last_had_openings`: null
- `active`: true

## What you NEVER touch

- `last_scanned`, `last_had_openings`, `active` flag changes (owned by scout-1)
- Any run directory under `research/`
- Any other file besides `portals.yml`

## What to return

Return ONLY a summary: "Discovered N new companies, M added to portals.yml (X greenhouse, Y ashby, Z lever, W custom)."

NEVER return the full company list in your response.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/discoverer-6.md
git commit -m "feat: add discoverer-6 agent for ICP-driven company discovery"
```

---

### Task 12: Update scout-1 agent definition

**Files:**
- Modify: `.claude/agents/scout-1.md`

- [ ] **Step 1: Add Exa crawl tool and Stage 2 instructions**

Update the `tools` line in the frontmatter to add `mcp__exa__crawling_exa`:

```
tools: Read, Write, Bash, WebSearch, WebFetch, mcp__exa__crawling_exa, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__get_page_text, mcp__claude-in-chrome__read_page, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__tabs_context_mcp
```

Update Stage 1 CLI invocation to include `--portals`:

```bash
cd /Users/diego/Dev/non-toxic/job-applications/agent-job-research
.venv/bin/board-aggregator \
  -q "Operations Manager AI" \
  ... \
  --portals portals.yml \
  -o $RUN_DIR/phase-1-scrape
```

Add Stage 2 section after Stage 1:

```markdown
### Stage 2: Exa crawl for non-ATS portals

After Stage 1 completes, read `portals.yml` and find companies where:
- `ats` is null (no known ATS platform)
- `active` is true
- `last_scanned` is null or older than `scan_interval_days` from config

For each matching company:
1. Call `mcp__exa__crawling_exa` on the company's `careers_url`
2. Parse the crawl results for job listings (look for role titles + URLs)
3. Filter by `title_filter` from portals.yml (positive keywords must match, negative must not)
4. Append matching jobs to `$RUN_DIR/phase-1-scrape/all-postings.md` using the same format:

\```
## [Title] -- [Company]
- **Source:** exa-portal
- **Location:** [if found, else "Unknown"]
- **Is Remote:** [if determinable]
- **Salary:** Not listed
- **URL:** [job url]
---
\```

5. Update `last_scanned` in portals.yml to today's date
6. If roles were found, update `last_had_openings` to today's date
7. If `last_had_openings` is older than `disable_after_days`, set `active: false`

Update the header counts in `all-postings.md` after appending.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/scout-1.md
git commit -m "feat: update scout-1 with --portals flag and Exa crawl stage"
```

---

### Task 13: Update lead-0 to pass portals.yml

**Files:**
- Modify: `.claude/agents/lead-0.md`

- [ ] **Step 1: Update Phase 1 instructions**

In the Phase 1 section, update the scout-1 spawn instructions to include portals.yml:

Add after the existing bullet points:

```markdown
- If `portals.yml` exists in the project root, include `--portals portals.yml` in the board-aggregator command. This triggers ATS portal scanning alongside board scraping.
- scout-1 will also run Exa crawl for non-ATS companies from portals.yml (Stage 2)
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/lead-0.md
git commit -m "feat: update lead-0 to pass portals.yml to scout-1"
```

---

### Task 14: Integration test — end-to-end portal scanning

**Files:**
- Modify: `tests/test_portal_scanner.py`

- [ ] **Step 1: Write integration test**

Append to `tests/test_portal_scanner.py`:

```python
from board_aggregator.runner import run_all


@responses.activate
def test_run_all_with_portals_integrates_results(tmp_path):
    """End-to-end: board scrapers + portal scanner -> unified dedup output."""
    fixture_ashby = json.loads((FIXTURES / "ashby_ramp.json").read_text())
    responses.add(responses.GET, "https://api.ashbyhq.com/posting-api/job-board/ramp", json=fixture_ashby, status=200)

    portals_path = _write_portals(tmp_path, [
        {"name": "Ramp", "domain": "ramp.com", "ats": "ashby", "slug": "ramp",
         "active": True, "last_scanned": None, "last_had_openings": None},
    ])

    output_dir = tmp_path / "output"

    # Mock board scrapers to return nothing (we just want to test portal integration)
    with patch("board_aggregator.runner.get_all_scrapers", return_value=[]):
        jobs = run_all(
            queries=["test"],
            output_dir=output_dir,
            portals_path=portals_path,
        )

    # Should have portal results (1 listed Ashby job, matching title filter with "AI")
    assert len(jobs) >= 1
    assert any(j.source == "ashby" for j in jobs)

    # Output files should exist
    assert (output_dir / "all-postings.md").exists()
    assert (output_dir / "all-postings.csv").exists()

    # portals.yml should be updated
    updated = yaml.safe_load(Path(portals_path).read_text())
    assert updated["companies"][0]["last_scanned"] == date.today().isoformat()
```

Add this import at the top of the test file:

```python
from unittest.mock import patch
```

- [ ] **Step 2: Run integration test**

Run: `.venv/bin/pytest tests/test_portal_scanner.py::test_run_all_with_portals_integrates_results -v`

Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `.venv/bin/pytest -v`

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_portal_scanner.py
git commit -m "test: add integration test for portal scanner with run_all"
```

---

### Task 15: Update CODEBASE_MAP.md

**Files:**
- Modify: `docs/CODEBASE_MAP.md`

- [ ] **Step 1: Add portal scanner entries**

Add to the Directory Structure section after `board_aggregator/scrapers/`:
```
│   └── portal_scanner.py         # ATS API clients (Greenhouse, Ashby, Lever)
```

Add to the Module Guide section:

```markdown
### board_aggregator/portal_scanner.py

**Purpose:** Fetches job postings from ATS platform public APIs.
**Exports:** `fetch_greenhouse()`, `fetch_ashby()`, `fetch_lever()`, `scan_portals()`, `filter_by_title()`
**ATS APIs:** Greenhouse (boards-api), Ashby (posting-api), Lever (postings API). All unauthenticated.
**Data flow:** Reads `portals.yml` for company list, hits ATS APIs, returns `List[JobPosting]`, updates timestamps in `portals.yml`.
```

Add `discoverer-6` to the Agent Definitions table:

```
| discoverer-6 | Discovery | Sonnet | Exa company search |
```

Add `portals.yml` to the Directory Structure:

```
├── portals.yml                    # Targeted company registry (persistent)
```

- [ ] **Step 2: Commit**

```bash
git add docs/CODEBASE_MAP.md
git commit -m "docs: add portal scanner and discoverer-6 to CODEBASE_MAP"
```
