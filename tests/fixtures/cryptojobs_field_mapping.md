# Field Mapping: crypto.jobs RSS Feed

Source URL: `https://crypto.jobs/feed/rss`
Fetched: 2026-03-28

## Feed-level tags (inside `<channel>`)

| Tag | Example value | Notes |
|-----|--------------|-------|
| `<title>` | `CryptoJobs - Latest Web3 Jobs` | Feed title, not job title |
| `<link>` | `https://crypto.jobs` | Canonical site URL |
| `<description>` | `The latest cryptocurrency and Web3 job postings from crypto.jobs` | Feed subtitle |
| `<language>` | `en-us` | |
| `<lastBuildDate>` | `Wed, 25 Mar 2026 22:02:47 +0000` | RFC 2822 format |
| `<atom:link>` | `href="https://crypto.jobs/feed/rss"` | Self-referential link; requires `xmlns:atom` namespace |
| `<image>` | nested `<url>`, `<title>`, `<link>` | Feed logo block |

## Item-level tags (per job posting inside `<item>`)

| Tag | Example value | Notes |
|-----|--------------|-------|
| `<title>` | `GALINA World — CEO / Co-Founder at GALINA world` | Pattern: `[Company] — [Role] at [Company]` or `[Role] at [Company]` |
| `<link>` | `https://crypto.jobs/jobs/galina-world-ceo-co-founder-at-galina-world?utm_source=rss&utm_medium=feed&utm_campaign=job-feed` | Includes UTM params; canonical URL is in `<guid>` without UTM params |
| `<guid isPermaLink="true">` | `https://crypto.jobs/jobs/galina-world-ceo-co-founder-at-galina-world` | Clean URL without UTM params; use this as the canonical job URL |
| `<description>` | HTML wrapped in `<![CDATA[...]]>` | See structure below |
| `<category>` | `Business Development` | Single category tag per item; job function/department |
| `<pubDate>` | `Wed, 25 Mar 2026 22:02:47 +0000` | RFC 2822 format, same as `lastBuildDate` |

## Description field structure (HTML inside CDATA)

The `<description>` field contains an HTML snippet with these `<p>` blocks in order:

```
<p><strong>Company:</strong> [company name]</p>
<p><strong>Location:</strong> [location string, often "Remote"]</p>
<p><strong>Salary:</strong> [salary string, free-form]</p>
<p><strong>Type:</strong> [Full Time | Part Time | Contract | ...]</p>
<p><strong>Skills:</strong> [comma-separated skills]</p>
<p>[excerpt or tagline from job description]</p>
```

Parsing notes:
- Company name is NOT a standalone XML attribute — it must be extracted from the HTML inside `<description>`
- Salary is free-form text (e.g. `"5000"`, `"180-280K USD a year"`, or token grant strings)
- The final `<p>` is a short excerpt; it may be quoted with `"..."` or unquoted prose
- feedparser will parse CDATA as `.summary` or `.description`; use `BeautifulSoup` or regex to extract structured fields

## XML namespaces

| Prefix | URI | Used for |
|--------|-----|---------|
| `atom` | `http://www.w3.org/2005/Atom` | `<atom:link rel="self">` in channel header |

No custom/proprietary namespaces (no `dc:`, `content:`, `media:`, or job-board-specific extensions observed).

## feedparser field mapping (Python)

| feedparser attribute | Source XML tag | Notes |
|---------------------|---------------|-------|
| `entry.title` | `<title>` | Full title string including company name pattern |
| `entry.link` | `<link>` | Contains UTM params |
| `entry.id` | `<guid>` | Clean URL, preferred for deduplication |
| `entry.summary` | `<description>` | Raw HTML string; parse with BS4 |
| `entry.tags[0].term` | `<category>` | Job function category |
| `entry.published` | `<pubDate>` | Parsed to `time.struct_time` by feedparser |
| `entry.published_parsed` | `<pubDate>` | UTC tuple |

## Extraction patterns (regex / BS4)

To extract structured fields from `entry.summary`:

```python
from bs4 import BeautifulSoup

def parse_cryptojobs_description(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for p in soup.find_all("p"):
        strong = p.find("strong")
        if strong:
            key = strong.get_text(strip=True).rstrip(":")
            value = p.get_text(strip=True)[len(key) + 1:].strip()
            fields[key] = value
    return fields
# Returns keys: Company, Location, Salary, Type, Skills
```

## Key observations

- The job title in `<title>` follows `"[Role] at [Company]"` — company name can be split on ` at ` as a fallback, but the HTML description is more reliable.
- There is no `<author>` tag per item.
- There are no `<enclosure>`, `<source>`, or `<comments>` tags.
- The feed returned 51 items total as of 2026-03-28.
- Dates use RFC 2822 with `+0000` timezone offset (UTC).
