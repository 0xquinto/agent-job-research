# WWR RSS Field Mapping

Fetched: 2026-03-28
Source: https://weworkremotely.com/remote-jobs.rss

## XML Namespaces

| Prefix | URI |
|--------|-----|
| `dc`   | `http://purl.org/dc/elements/1.1/` |
| `media`| `http://search.yahoo.com/mrss` |

No custom `wwr:` namespace. WWR uses plain (non-namespaced) custom tags directly
inside `<item>`.

## Channel-level tags

| Tag | Notes |
|-----|-------|
| `<title>` | Feed title string |
| `<link>` | Feed URL |
| `<description>` | Feed description string |
| `<language>` | e.g. `en-US` |
| `<ttl>` | `60` (minutes) |

## Item-level tags

| Tag | feedparser access | Notes |
|-----|-------------------|-------|
| `<title>` | `entry.title` | Format: `"CompanyName: Job Title"` — company name is the prefix before the first colon |
| `<link>` | `entry.link` | Canonical job URL, e.g. `https://weworkremotely.com/remote-jobs/slug` |
| `<guid>` | `entry.id` | Same value as `<link>` |
| `<pubDate>` | `entry.published` | RFC 2822 format: `Fri, 27 Mar 2026 20:20:27 +0000` |
| `<expires_at>` | `entry.expires_at` (raw) | Non-standard tag; ~30 days after pubDate; feedparser surfaces as raw tag |
| `<description>` | `entry.summary` | HTML-escaped full job description; contains company HQ and apply URL inline |
| `<region>` | `entry.region` (raw) | Plain text, e.g. `"Anywhere in the World"` |
| `<country>` | `entry.country` (raw) | Often empty string |
| `<state>` | `entry.state` (raw) | US state or Canadian province of company HQ |
| `<skills>` | `entry.skills` (raw) | Comma-separated skill tags; may be empty string |
| `<category>` | `entry.tags[0].term` | Job category, e.g. `"Design"`, `"Front-End Programming"` |
| `<type>` | `entry.type` (raw) | Employment type: `"Full-Time"` or `"Contract"` |
| `<media:content>` | `entry.media_content[0]['url']` | Company logo image URL (S3); `type` attribute is always `"image/png"` even for .gif files |

## Key parsing notes

### Company name extraction
There is no dedicated `<company>` tag. Company name must be parsed from `<title>`:
```python
company = entry.title.split(":")[0].strip()
job_title = entry.title.split(":", 1)[1].strip()
```
Watch out for colons in job titles (e.g. "Senior Engineer: Payments") — split on
the first colon only.

### Job URL
`<link>` and `<guid>` are identical and both point to the WWR job listing page.
The actual company apply URL is embedded inside the HTML of `<description>` in a
`"To apply:"` paragraph — not a structured field.

### Date format
RFC 2822: `Fri, 27 Mar 2026 20:20:27 +0000`
feedparser parses this into a `time.struct_time` at `entry.published_parsed`.

### Non-standard tags (no namespace)
`<region>`, `<country>`, `<state>`, `<skills>`, `<type>`, and `<expires_at>` are
bare custom tags with no namespace prefix. feedparser exposes these via
`entry.get("wwr_region")` style only if feedparser namespaces them — in practice
they appear under their tag name directly in `entry` dict when using
`feedparser.parse()`. Verify with: `entry.keys()` or access as
`entry.get("region")`.

### Skills tag
May be an empty string or a comma-and-space separated list:
`"AI Content Creation, Content Creation,  SEO, and Content Strategy"`
Note the double space before "SEO" — strip individual items after splitting on `,`.
