import os
import re
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


@patch.dict(os.environ, {}, clear=True)
def test_get_token_missing_credentials_returns_none():
    scraper = RedditJobsScraper()
    token = scraper._get_token()
    assert token is None


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
