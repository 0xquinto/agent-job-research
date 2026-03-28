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
