"""Tests for scripts/tracker.py — application tracker merge/dedup logic."""

import sys
from pathlib import Path

import pytest

# Add scripts/ to path so we can import tracker
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from tracker import (
    add_entry,
    dedup,
    find_duplicate,
    fuzzy_role_match,
    normalize_status,
    parse_tracker,
    write_tracker,
)


@pytest.fixture
def states():
    return {
        "evaluated": {"label": "Evaluated", "order": 1, "aliases": ["scored"]},
        "applied": {"label": "Applied", "order": 3, "aliases": ["submitted"]},
        "interview": {"label": "Interview", "order": 5, "aliases": ["screening"]},
        "offer": {"label": "Offer", "order": 6, "aliases": []},
        "rejected": {"label": "Rejected", "order": 10, "aliases": []},
        "skip": {"label": "SKIP", "order": 0, "aliases": ["skipped"]},
    }


class TestFuzzyRoleMatch:
    def test_exact_match(self):
        assert fuzzy_role_match("Research Engineer, Agents", "Research Engineer, Agents")

    def test_partial_match_two_words(self):
        assert fuzzy_role_match("Research Engineer, Agents", "Senior Research Engineer")

    def test_no_match(self):
        assert not fuzzy_role_match("Product Manager", "Research Engineer")

    def test_short_words_ignored(self):
        # "AI" and "ML" are <= 3 chars, shouldn't count
        assert not fuzzy_role_match("AI ML Engineer", "AI ML Designer")


class TestNormalizeStatus:
    def test_canonical(self, states):
        assert normalize_status("evaluated", states) == "evaluated"

    def test_alias(self, states):
        assert normalize_status("scored", states) == "evaluated"
        assert normalize_status("submitted", states) == "applied"

    def test_case_insensitive(self, states):
        assert normalize_status("APPLIED", states) == "applied"

    def test_unknown_passthrough(self, states):
        assert normalize_status("custom-status", states) == "custom-status"


class TestFindDuplicate:
    def test_finds_match(self):
        rows = [
            {
                "num": "1",
                "date": "2026-04-08",
                "company": "Anthropic",
                "role": "Research Engineer, Agents",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            }
        ]
        assert find_duplicate(rows, "Anthropic", "Senior Research Engineer") == 0

    def test_no_match(self):
        rows = [
            {
                "num": "1",
                "date": "2026-04-08",
                "company": "Anthropic",
                "role": "Research Engineer",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            }
        ]
        assert find_duplicate(rows, "Ramp", "Research Engineer") is None


class TestDedup:
    def test_keeps_higher_score(self, states):
        rows = [
            {
                "num": "1",
                "date": "2026-04-01",
                "company": "Anthropic",
                "role": "Research Engineer",
                "score": "7.5",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            },
            {
                "num": "2",
                "date": "2026-04-08",
                "company": "Anthropic",
                "role": "Senior Research Engineer",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            },
        ]
        result = dedup(rows, states)
        assert len(result) == 1
        assert result[0]["score"] == "8.9"

    def test_promotes_status(self, states):
        rows = [
            {
                "num": "1",
                "date": "2026-04-01",
                "company": "Anthropic",
                "role": "Research Engineer",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            },
            {
                "num": "2",
                "date": "2026-04-08",
                "company": "Anthropic",
                "role": "Research Engineer Agents",
                "score": "7.5",
                "status": "interview",
                "archetype": "",
                "url": "",
                "notes": "",
            },
        ]
        result = dedup(rows, states)
        assert len(result) == 1
        assert result[0]["score"] == "8.9"
        assert result[0]["status"] == "interview"  # promoted from lower-score duplicate

    def test_different_companies_kept(self, states):
        rows = [
            {
                "num": "1",
                "date": "2026-04-01",
                "company": "Anthropic",
                "role": "Research Engineer",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            },
            {
                "num": "2",
                "date": "2026-04-01",
                "company": "Ramp",
                "role": "Research Engineer",
                "score": "7.0",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            },
        ]
        result = dedup(rows, states)
        assert len(result) == 2


class TestTrackerRoundtrip:
    def test_write_then_parse(self, tmp_path):
        path = tmp_path / "applications.md"
        rows = [
            {
                "num": "1",
                "date": "2026-04-08",
                "company": "Anthropic",
                "role": "Research Engineer",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "Agentic",
                "url": "https://example.com",
                "notes": "A-tier",
            },
        ]
        write_tracker(path, rows)
        parsed = parse_tracker(path)
        assert len(parsed) == 1
        assert parsed[0]["company"] == "Anthropic"
        assert parsed[0]["score"] == "8.9"


class TestAddEntry:
    def test_add_new(self):
        rows = []
        rows = add_entry(rows, "Anthropic", "Research Engineer", "8.9")
        assert len(rows) == 1
        assert rows[0]["company"] == "Anthropic"

    def test_update_higher_score(self):
        rows = [
            {
                "num": "1",
                "date": "2026-04-01",
                "company": "Anthropic",
                "role": "Research Engineer, Agents",
                "score": "7.0",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            }
        ]
        rows = add_entry(rows, "Anthropic", "Senior Research Engineer", "8.9")
        assert len(rows) == 1  # updated in place, not appended
        assert rows[0]["score"] == "8.9"

    def test_skip_lower_score(self):
        rows = [
            {
                "num": "1",
                "date": "2026-04-01",
                "company": "Anthropic",
                "role": "Research Engineer, Agents",
                "score": "8.9",
                "status": "evaluated",
                "archetype": "",
                "url": "",
                "notes": "",
            }
        ]
        rows = add_entry(rows, "Anthropic", "Senior Research Engineer", "7.0")
        assert len(rows) == 1
        assert rows[0]["score"] == "8.9"  # kept original higher score
