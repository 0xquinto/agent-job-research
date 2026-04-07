import re

import responses

from board_aggregator.scrapers.reddit_jobs import RedditJobsScraper

LISTING_URL_PATTERN = re.compile(r"https://www\.reddit\.com/r/.+/new\.json")

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
def test_fetch_listings_paginates():
    responses.add(responses.GET, LISTING_URL_PATTERN, json=LISTING_RESPONSE_PAGE_1, status=200)
    responses.add(responses.GET, LISTING_URL_PATTERN, json=LISTING_RESPONSE_PAGE_2, status=200)

    scraper = RedditJobsScraper()
    posts = scraper._fetch_listings()

    assert len(posts) == 3


@responses.activate
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

    responses.add(responses.GET, LISTING_URL_PATTERN, json=listing, status=200)

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


@responses.activate
def test_scrape_returns_empty_on_error():
    responses.add(responses.GET, LISTING_URL_PATTERN, json={"error": "forbidden"}, status=403)

    scraper = RedditJobsScraper()
    jobs = scraper.scrape(["any"])
    assert jobs == []


@responses.activate
def test_fetch_listings_retries_on_429():
    responses.add(responses.GET, LISTING_URL_PATTERN, json={"error": "rate limited"}, status=429)
    responses.add(
        responses.GET,
        LISTING_URL_PATTERN,
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
    posts = scraper._fetch_listings()

    assert len(posts) == 1
    assert len(responses.calls) == 2


def test_extract_company_pipe_format():
    scraper = RedditJobsScraper()
    # Bracket prefix detected in parts[0], returns parts[1]
    assert scraper._extract_company("[Hiring] Acme Corp | Backend Dev | Remote", "forhire") == "Backend Dev"


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
