# Reddit Job Scraper Design

## Purpose

Board scraper that scans 20 Reddit subreddits for job-related posts, outputting `JobPosting` objects. Primary value is **discovery** — surfacing companies and roles from Reddit communities that feed into Phase 2 ranking.

## Architecture

Single file: `board_aggregator/scrapers/reddit_jobs.py`
Pattern: `BaseScraper` with `@register` decorator
Dependencies: None new — uses `requests` (already in project)
Credentials: `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` env vars

## Subreddit Tiers

### Tier 1 — Job boards (all posts kept)

`forhire`, `hiring`, `jobbit`, `remotejobs`

These subreddits have structured job posting conventions (`[Hiring]` flair/tags). All posts are kept except `[For Hire]` (people seeking work).

### Tier 2 — Discussion subs (keyword-filtered)

`WorkOnline`, `webdev`, `datascience`, `freelance`, `remotework`, `digitalnomad`, `Upwork`, `freelanceWriters`, `copywriting`, `graphic_design`, `learnprogramming`, `VirtualAssistants`, `socialmedia`, `marketing`, `CustomerSuccess`, `careerguidance`

Posts kept only if title or body matches hiring-signal keywords: `hiring`, `position`, `role`, `looking for`, `we're hiring`, `job opening`, `apply`.

## Auth Flow

Raw OAuth2 client credentials grant — no PRAW dependency.

```
POST https://www.reddit.com/api/v1/access_token
  grant_type=client_credentials
  auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
→ bearer token
```

One token per `scrape()` call. Token outlives the 2-3 requests needed per run. No refresh loop.

If credentials are missing, scraper prints a warning and returns `[]`.

## Fetching

Combined multi-subreddit listing — one request covers all 20 subs:

```
GET https://oauth.reddit.com/r/forhire+hiring+jobbit+...+careerguidance/new.json
  ?limit=100&raw_json=1
  Authorization: Bearer {token}
  User-Agent: "board-aggregator/1.0 (job-research-pipeline)"
```

Paginate with `after` cursor, up to 3 pages (300 posts max).

**Total API calls per run:** 1 token + up to 3 listing pages = 4 max.

## Parsing

Reddit post → `JobPosting` field mapping:

| JobPosting field | Reddit source |
|---|---|
| `title` | `data.title` |
| `company` | Extracted from title/body (see Company Extraction below) |
| `source` | `"reddit"` |
| `job_url` | `https://reddit.com{data.permalink}` |
| `location` | Parsed from title/body, default `None` |
| `is_remote` | Regex for `remote` in title/body |
| `salary_min/max` | `$NNNk-$NNNk` regex (same pattern as HN scraper) |
| `date_posted` | `datetime.fromtimestamp(data.created_utc)` → `YYYY-MM-DD` |
| `description` | `data.selftext[:500]` |

## Company Extraction

Reddit posts don't follow a consistent format. Strategy in priority order:

1. Pipe-separated first line: `Company | Role | Location` (some r/forhire posts)
2. Bracketed: `[Company Name]` in title
3. Bold markdown: `**Company Name**` in title
4. Preposition: `at {Company}` or `@ {Company}` in title
5. Fallback: `r/{subreddit}` (ranker-7 can still extract company from description)

## Skip Rules

- `selftext == "[removed]"` or `"[deleted]"`
- Author is `AutoModerator`
- Title/flair contains `[For Hire]` (people seeking work, not posting jobs)
- Tier 2 posts without hiring-signal keywords

## Error Handling

- Missing credentials → warn + return `[]`
- Token request fails → warn + return `[]`
- 429 response → exponential backoff (same `MAX_RETRIES` / `RETRY_BACKOFF` pattern as HN scraper)
- Network error → retry with backoff, return `[]` if all retries exhausted

## CLI Wiring

Add `import board_aggregator.scrapers.reddit_jobs` to `cli.py` main function.

## Tests

File: `tests/test_reddit_jobs.py`
Pattern: `@responses.activate` mocks (same as `test_hn_hiring.py`)

Test cases:
- Parses job posts from mixed subreddit listing
- Filters out `[For Hire]` posts
- Filters tier 2 discussion posts without hiring signals
- Handles missing credentials gracefully (returns `[]`)
- Handles 429 / error responses with retry
