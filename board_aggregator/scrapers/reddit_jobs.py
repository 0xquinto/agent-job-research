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
