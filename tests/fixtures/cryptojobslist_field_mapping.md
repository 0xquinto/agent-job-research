# CryptoJobsList __NEXT_DATA__ Field Mapping

Extracted from `props.pageProps.jobs` array on the homepage listing page (2026-03-28).
Single job detail pages return 403, so this reflects the listing-level data shape.

## All Confirmed Keys (props.pageProps.jobs[0].???)

| Field Path | Type | Example Value | Notes |
|---|---|---|---|
| `_id.$oid` | string | `"69bd0a8d86d7913525d656c8"` | MongoDB ObjectId, nested |
| `id` | string | `"69bd0a8d86d7913525d656c8"` | Flattened duplicate of `_id.$oid` |
| `jobTitle` | string | `"Talent Acquisition Specialist"` | Job title |
| `companyName` | string | `"Kleros"` | Company name |
| `companySlug` | string | `"kleros"` | URL-safe company identifier |
| `companyLogo` | string | `"https://img.cryptojobslist.com/..."` | Logo image URL |
| `companyTwitter` | string | `"kleros_io"` | Twitter/X handle (no @) |
| `companyVerified` | boolean | `false` | Whether company is verified |
| `jobLocation` | string | `""` | Location string (empty when remote) |
| `remote` | boolean | `true` | Remote flag |
| `locationEnhancedObj` | null/object | `null` | Structured location (null when remote) |
| `locationSchema` | null/object | `null` | Schema.org location data |
| `salary.unitText` | string | `"YEAR"` | Pay period: `"YEAR"`, `"MONTH"`, `"HOUR"` |
| `salary.currency` | string | `"USD"` | ISO currency code |
| `salary.minValue` | number | `30000` | Minimum salary |
| `salary.maxValue` | number | `60000` | Maximum salary |
| `salaryString` | string | `"$30k-60k/year"` | Pre-formatted human-readable salary |
| `estimatedSalary` | null/object | `null` | Estimated salary if not provided |
| `tags` | string[] | `["full-time","non-tech","web3",...]` | Lowercase hyphenated tags array |
| `category` | null/string | `null` | Job category |
| `seoSlug` | string | `"talent-acquisition-specialist-at-kleros"` | URL slug for job detail page |
| `bossFirstName` | string | `"Taieb"` | Poster's first name |
| `bossLastName` | string | `"Chaouch"` | Poster's last name |
| `bossPicture` | string | `"https://img.cryptojobslist.com/..."` | Poster's avatar URL |
| `videoApplicationsEnabled` | boolean | `false` | Video application option available |
| `videoApplicationsRequired` | boolean | `false` | Video application mandatory |
| `directApplicationsQty` | number | `56` | Count of direct applications |
| `applicationLinkClicks` | number | `0` | Count of external apply link clicks |
| `applicationQuantityTitle` | string | `"56 direct applications."` | Pre-formatted application count string |
| `published` | boolean | `true` | Listing is live |
| `publishedAt` | ISO8601 string | `"2026-03-20T08:51:25.124Z"` | Publish timestamp |
| `isFeatured` | boolean | `true` | Featured listing flag |
| `featuredAt` | ISO8601 string | `"2026-03-20T08:51:25.097Z"` | When featured status was set |
| `lastApplicationAt` | ISO8601 string | `"2026-03-28T09:06:17.842Z"` | Most recent application timestamp |
| `filled` | boolean | `false` | Job has been filled |
| `isActive` | boolean | `true` | Computed active status |
| `notAJobAd` | boolean | `false` | Non-job content flag |
| `logoDarkMode` | null/string | `null` | Dark-mode logo variant |
| `telegramDiscussionLink` | string | `"https://t.me/cryptojobslist/10772"` | Telegram thread URL |
| `twitterDiscussionLink` | string | `"https://x.com/CryptoJobsList/status/..."` | X/Twitter thread URL |
| `timeSinceJobCreation` | string | `"1w"` | Human-readable age: `"1w"`, `"1d"`, `"3w"`, etc. |
| `applicationLinkClicks` | number | `0` | External apply link click count |

## Key Findings

### Confirmed from feasibility research
All 8 predicted keys verified:
- `_id` (as `_id.$oid` nested object)
- `jobTitle`
- `companyName`
- `jobLocation`
- `salary`
- `videoApplicationsEnabled`
- `bossFirstName`
- `bossLastName`

### Job URL construction
Detail page URL pattern: `https://cryptojobslist.com/{seoSlug}-{id}`
Example: `https://cryptojobslist.com/talent-acquisition-specialist-at-kleros-69bd0a8d86d7913525d656c8`

### Salary parsing
- Structured: `salary.minValue`, `salary.maxValue`, `salary.currency`, `salary.unitText`
- Pre-formatted: `salaryString` (e.g. `"$30k-60k/year"`, `"EUR 125k-138k/year"`)
- Fallback: `estimatedSalary` (null when salary is provided)
- Some listings have no salary (fields present but salary object may be null)

### Remote detection
- `remote: true` means fully remote
- `jobLocation: ""` is empty string when remote (not null)
- `locationEnhancedObj: null` when remote; structured object when office location

### Date fields
- Use `publishedAt` for "date posted" (full ISO8601 timestamp)
- `timeSinceJobCreation` is a pre-computed display string only (not reliable for filtering)

### Poster identity
- `bossFirstName` + `bossLastName` = job poster name (hiring manager or recruiter)
- `bossPicture` = poster avatar URL
- `companyTwitter` = company X/Twitter handle

### Tags taxonomy
Tags are lowercase hyphenated strings. Common values observed:
`full-time`, `remote`, `non-tech`, `web3`, `developer`, `engineering`, `senior`, `marketing`,
`defi`, `nft`, `solana`, `ethereum`, `pay-in-crypto`, `react`, `java`, `python`, `trading`,
`sales`, `community`, `startup`, `cex`, `exchange`

## Fields NOT present at listing level
These fields are likely on the job detail page (403 blocked):
- `jobDescription` (full job description HTML/text)
- `applyUrl` (external application link)
- `companyWebsite`
- `companyDescription`
- `employmentType` (though inferrable from tags: `full-time`, `part-time`, `contract`)
- `experienceLevel` (inferrable from tags: `senior`, `entry-level`, `intern`)
- `equity` / `benefits`

## Source
- Page: `https://cryptojobslist.com`
- Extraction date: 2026-03-28
- Data path: `window.__NEXT_DATA__.props.pageProps.jobs`
- Total jobs in listing: 361 (25 shown per page, paginated)
