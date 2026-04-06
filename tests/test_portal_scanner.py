import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import responses
import yaml

from board_aggregator.models import JobPosting
from board_aggregator.portal_scanner import (
    fetch_ashby,
    fetch_greenhouse,
    fetch_lever,
    filter_by_title,
    scan_portals,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Greenhouse
# ---------------------------------------------------------------------------


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

    assert jobs[0].is_remote is False  # Location Type = null
    assert jobs[1].is_remote is True  # Location Type = "Remote"


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


# ---------------------------------------------------------------------------
# Ashby
# ---------------------------------------------------------------------------


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
    # When no salary data, Pydantic defaults apply (USD, yearly)
    assert jobs[0].salary_currency == "USD"
    assert jobs[0].salary_interval == "yearly"


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


# ---------------------------------------------------------------------------
# Lever
# ---------------------------------------------------------------------------


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
    assert jobs[1].is_remote is True  # remote


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


# ---------------------------------------------------------------------------
# Title filtering
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# scan_portals
# ---------------------------------------------------------------------------


def _write_portals(tmp_path, companies, config=None):
    """Helper to write a portals.yml for testing."""
    portals = {
        "config": config
        or {
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

    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs",
        json=fixture_gh,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.ashbyhq.com/posting-api/job-board/ramp",
        json=fixture_ashby,
        status=200,
    )

    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Anthropic",
                "domain": "anthropic.com",
                "ats": "greenhouse",
                "slug": "anthropic",
                "active": True,
                "last_scanned": None,
                "last_had_openings": None,
            },
            {
                "name": "Ramp",
                "domain": "ramp.com",
                "ats": "ashby",
                "slug": "ramp",
                "active": True,
                "last_scanned": None,
                "last_had_openings": None,
            },
        ],
    )

    jobs = scan_portals(portals_path)

    sources = {j.source for j in jobs}
    assert "greenhouse" in sources
    assert "ashby" in sources
    assert len(jobs) >= 3  # 2 Greenhouse + 1 listed Ashby


@responses.activate
def test_scan_portals_skips_inactive_companies(tmp_path):
    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Dead Corp",
                "domain": "dead.com",
                "ats": "greenhouse",
                "slug": "dead",
                "active": False,
                "last_scanned": None,
                "last_had_openings": None,
            },
        ],
    )

    jobs = scan_portals(portals_path)

    assert len(jobs) == 0


@responses.activate
def test_scan_portals_skips_recently_scanned(tmp_path):
    today = date.today().isoformat()
    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Fresh Corp",
                "domain": "fresh.com",
                "ats": "greenhouse",
                "slug": "fresh",
                "active": True,
                "last_scanned": today,
                "last_had_openings": today,
            },
        ],
    )

    jobs = scan_portals(portals_path)

    assert len(jobs) == 0


@responses.activate
def test_scan_portals_skips_null_ats(tmp_path):
    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Custom Co",
                "domain": "custom.com",
                "ats": None,
                "slug": None,
                "careers_url": "https://custom.com/careers",
                "active": True,
                "last_scanned": None,
                "last_had_openings": None,
            },
        ],
    )

    jobs = scan_portals(portals_path)

    assert len(jobs) == 0


@responses.activate
def test_scan_portals_updates_timestamps(tmp_path):
    fixture_gh = json.loads((FIXTURES / "greenhouse_anthropic.json").read_text())
    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/anthropic/jobs",
        json=fixture_gh,
        status=200,
    )

    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Anthropic",
                "domain": "anthropic.com",
                "ats": "greenhouse",
                "slug": "anthropic",
                "active": True,
                "last_scanned": None,
                "last_had_openings": None,
            },
        ],
    )

    scan_portals(portals_path)

    updated = yaml.safe_load(Path(portals_path).read_text())
    company = updated["companies"][0]
    assert company["last_scanned"] == date.today().isoformat()
    assert company["last_had_openings"] == date.today().isoformat()


@responses.activate
def test_scan_portals_disables_stale_company(tmp_path):
    responses.add(
        responses.GET,
        "https://boards-api.greenhouse.io/v1/boards/ghost/jobs",
        json={"jobs": []},
        status=200,
    )

    old_date = (date.today() - timedelta(days=31)).isoformat()
    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Ghost Corp",
                "domain": "ghost.com",
                "ats": "greenhouse",
                "slug": "ghost",
                "active": True,
                "last_scanned": (date.today() - timedelta(days=8)).isoformat(),
                "last_had_openings": old_date,
            },
        ],
    )

    scan_portals(portals_path)

    updated = yaml.safe_load(Path(portals_path).read_text())
    assert updated["companies"][0]["active"] is False


# ---------------------------------------------------------------------------
# Integration: run_all with portals
# ---------------------------------------------------------------------------


@responses.activate
def test_run_all_with_portals_integrates_results(tmp_path):
    """End-to-end: board scrapers + portal scanner -> unified dedup output."""
    from board_aggregator.runner import run_all

    fixture_ashby = json.loads((FIXTURES / "ashby_ramp.json").read_text())
    responses.add(
        responses.GET,
        "https://api.ashbyhq.com/posting-api/job-board/ramp",
        json=fixture_ashby,
        status=200,
    )

    portals_path = _write_portals(
        tmp_path,
        [
            {
                "name": "Ramp",
                "domain": "ramp.com",
                "ats": "ashby",
                "slug": "ramp",
                "active": True,
                "last_scanned": None,
                "last_had_openings": None,
            },
        ],
    )

    output_dir = tmp_path / "output"

    with patch("board_aggregator.runner.get_all_scrapers", return_value=[]):
        jobs = run_all(
            queries=["test"],
            output_dir=output_dir,
            portals_path=portals_path,
        )

    # Should have portal results (1 listed Ashby job matching title filter "AI")
    assert len(jobs) >= 1
    assert any(j.source == "ashby" for j in jobs)

    # Output files should exist
    assert (output_dir / "all-postings.md").exists()
    assert (output_dir / "all-postings.csv").exists()

    # portals.yml should be updated
    updated = yaml.safe_load(Path(portals_path).read_text())
    assert updated["companies"][0]["last_scanned"] == date.today().isoformat()
