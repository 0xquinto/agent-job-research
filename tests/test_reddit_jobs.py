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


@patch.dict(os.environ, {}, clear=True)
def test_get_token_missing_credentials_returns_none():
    scraper = RedditJobsScraper()
    token = scraper._get_token()
    assert token is None
