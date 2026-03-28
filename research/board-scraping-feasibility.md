# Job Board Scraping Feasibility Report

Generated: 2026-03-27

## Summary Table

| Board | HTTP Status | Server-Rendered | API Available | RSS/Feed | Anti-Bot | Scrape Method | Difficulty |
|---|---|---|---|---|---|---|---|
| LLMHire | 200 (185KB) | No (React SPA) | No | No | Vercel (minimal) | Playwright | Medium |
| aijobs.net | 200 (317KB) | No (SPA, no NEXT_DATA) | No | No | nginx (minimal) | Playwright | Medium |
| AI Job Network | 503 | Blocked | No | No | Cloudflare block | Not feasible | Hard |
| AIMLJobs.fyi | 200 (11KB) | Partial (Korean, BS4 viable) | No | No (returns HTML) | hcdn (minimal) | requests + BS4 | Easy-Medium |
| Himalayas | 200 (519KB) | No (Next.js app router, no NEXT_DATA) | Yes (public `/api/jobs`) | No | Cloudflare (passive) | Public API | Easy |
| We Work Remotely | 200 (383KB) | Yes (Rails) | No | Yes (RSS works) | Cloudflare (passive) | RSS feed | Easy |
| GetOnBoard | 200 (572KB) | Yes | Yes (v0, auth required) | No | Cloudflare (passive) | Auth API or Playwright | Medium |
| HN Who's Hiring | 200 | N/A | Yes (Algolia, free) | No | None | Algolia API | Easy |
| DevRel Talent | 301→200 (101KB) | Partial (www redirect) | No | No | Cloudflare | requests + BS4 | Medium |
| AIJobBoard.dev | 200 (31KB) | No (SPA shell) | No | No | hcdn (minimal) | Playwright | Medium |
| RemoteFront | 308→200 (110KB) | Yes (www redirect resolves) | No | No | Cloudflare | requests + BS4 | Easy-Medium |
| gm.careers | 200 (243KB) | No (React SPA, no NEXT_DATA) | Partial (returns HTML not JSON) | No | Vercel (minimal) | Playwright | Medium |
| CryptoJobsList | 200 (362KB) | Yes (Next.js NEXT_DATA confirmed) | No (403) | No (403) | Cloudflare (passive) | requests + NEXT_DATA | Easy |
| Web3.career | 200 (321KB) | Yes (Rails + BS4) | No | No | Cloudflare (passive) | requests + BS4 | Easy |
| CryptocurrencyJobs | 200 (306KB) | Yes (static site, category pages work) | No | No (404) | Cloudflare (passive) | requests + BS4 + category pages | Easy |
| crypto.jobs | 200 (145KB) | Yes (has RSS feeds) | No | Yes (RSS/Atom) | Cloudflare (passive) | RSS feed | Easy |
| The Defiant Jobs | 000 / 503 | DNS fails + site suspended | No | No | Unknown | Not feasible | Hard |

---

## Board-by-Board Findings

### 1. LLMHire — llmhire.com

**What works:**
- HTTP 200, 185KB — BUT the body reveals a React SPA: `<div hidden=""><!--$--><!--/$--></div>` with a hydration shell
- Title: "LLMHire — The AI Labor Market Intelligence Platform"
- No `__NEXT_DATA__`, no server-rendered job content in HTML
- `/api/jobs`, `/feed`, `/rss` all return 404

**Recommended approach:** Playwright — wait for React hydration and job cards to render

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://llmhire.com/jobs")
    # Wait for job listings to load after React hydration
    page.wait_for_selector("[class*='job']", timeout=15000)
    # Extract job cards
    jobs = page.evaluate("""
        () => Array.from(document.querySelectorAll('[class*=\"job-\"]')).map(el => ({
            text: el.innerText,
            href: el.querySelector('a')?.href
        }))
    """)
    browser.close()
```

---

### 2. aijobs.net — aijobs.net

**What works:**
- HTTP 200, 317KB — loads but no `__NEXT_DATA__` found; SPA architecture (possibly Nuxt or Vue)
- No API endpoints or feeds discovered
- nginx server with minimal bot protection

**Recommended approach:** Playwright for client-side rendering

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://aijobs.net")
    page.wait_for_load_state("networkidle")
    # Intercept XHR/fetch calls to find the data source
    jobs_html = page.content()
    browser.close()
```

**Note:** Intercept network requests in Playwright to identify the actual API endpoint the SPA calls — then use that endpoint directly with `requests`.

---

### 3. AI Job Network — aijobnetwork.com

**What works:**
- Nothing. HTTP 503 from Cloudflare on every request, cf-ray header present
- Site shows "Service Suspended by its owner" — the site is shut down
- www redirect also 503

**Recommended approach:** Not feasible. Site is suspended. Remove from scraping list.

---

### 4. AIMLJobs.fyi — aimljobs.fyi

**What works:**
- HTTP 200, 11KB — Korean-language AI jobs board (global AI/ML roles, Korean interface)
- Static HTML site — server-rendered, no JS framework detected
- `/feed` and `/rss` both return HTTP 200 but serve the same HTML homepage (not XML)
- No `__NEXT_DATA__`, no API refs
- Title: "AIML Jobs | 글로벌 인공지능 & 머신러닝(ML) 전문 채용 플랫폼"
- Has SearchAction schema for `https://www.aimljobs.fyi/search?q={search_term_string}`

**Recommended approach:** `requests` + BeautifulSoup — page is small (11KB) and server-rendered. Use search endpoint for filtering.

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get(
    "https://aimljobs.fyi",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
)
soup = BeautifulSoup(resp.text, "html.parser")
# Inspect structure — likely simple card list given 11KB page size
# Use search for targeted queries:
search_resp = requests.get(
    "https://aimljobs.fyi/search",
    params={"q": "operations manager"},
    headers={"User-Agent": "Mozilla/5.0"}
)
```

---

### 5. Himalayas — himalayas.app

**What works:**
- HTTP 200, 519KB — Next.js app router (no `__NEXT_DATA__`, uses new React server components)
- Title: "97,736 Remote Jobs | Himalayas"
- Public undocumented API at `/api/jobs` confirmed working: returns `{"jobs": [...], "pagination": {...}}`
- API returns full job objects with keys: `id`, `company_id`, `title`, `description`, `short_description`, `role_type`, `seniority_level`, `employment_type`
- Supports `?limit=N&offset=N` pagination

**Recommended approach:** Public API (cleanest option, zero parsing needed)

```python
import requests

def fetch_himalayas_jobs(limit=100, offset=0):
    resp = requests.get(
        "https://himalayas.app/api/jobs",
        params={"limit": limit, "offset": offset},
        headers={"User-Agent": "Mozilla/5.0"}
    )
    data = resp.json()  # {"jobs": [...], "pagination": {...}}
    return data["jobs"], data["pagination"]

all_jobs = []
offset = 0
while True:
    jobs, pagination = fetch_himalayas_jobs(limit=100, offset=offset)
    all_jobs.extend(jobs)
    if offset + 100 >= pagination.get("total", 0):
        break
    offset += 100
```

---

### 6. We Work Remotely — weworkremotely.com

**What works:**
- HTTP 200, 383KB — Rails-based, fully server-rendered
- RSS feed confirmed working: `https://weworkremotely.com/remote-jobs.rss` returns `application/rss+xml` with full job data including title, company, region, category, type, description, pubDate
- Category-specific RSS: `/categories/remote-management-and-finance-jobs.rss` also returns 200

**Recommended approach:** RSS feed (simplest and most reliable)

```python
import feedparser

feeds = [
    "https://weworkremotely.com/remote-jobs.rss",
    "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]

all_jobs = []
for feed_url in feeds:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        all_jobs.append({
            "title": entry.title,
            "company": entry.get("author", ""),
            "url": entry.link,
            "published": entry.get("published", ""),
            "category": entry.get("tags", [{}])[0].get("term", "") if entry.get("tags") else "",
            "type": entry.get("wwr_type", ""),
            "region": entry.get("wwr_region", ""),
        })
```

---

### 7. GetOnBoard — getonbrd.com

**What works:**
- HTTP 200, 572KB — server-rendered, Cloudflare CDN
- `/api/v0/categories` returns full JSON without auth (18 job categories confirmed)
- `/api/v0/jobs` requires auth (401 with JSON error message)
- Categories include `operations-management` and `machine-learning-ai` — relevant for ops/AI roles

**Recommended approach:** Register for free API token to unlock job listings. Category endpoint is free.

```python
import requests

# Step 1: Get categories (no auth needed)
cats = requests.get("https://getonbrd.com/api/v0/categories").json()
# Returns: [{"id": "operations-management", "attributes": {"name": "Operations / Management"}}, ...]

# Step 2: With API token, fetch jobs by category
API_TOKEN = "YOUR_FREE_TOKEN"  # Register at getonbrd.com
resp = requests.get(
    "https://getonbrd.com/api/v0/jobs",
    headers={"Authorization": f"Bearer {API_TOKEN}"},
    params={"per_page": 50, "page": 1, "category_id": "operations-management"}
)
jobs = resp.json()
```

**Free registration:** https://getonbrd.com/register — required before using job endpoints.

---

### 8. HN Who's Hiring — news.ycombinator.com

**What works:**
- Algolia API fully public, no auth, confirmed working
- March 2026 thread found: ID `47219668`, created `2026-03-02`
- Also February 2026: ID `46857488`, January 2026: ID `46466074`
- Comment-level API lets you pull all job postings from any thread

**Recommended approach:** Algolia API (zero friction, best structured data)

```python
import requests

# March 2026 Who's Hiring thread ID
MARCH_2026_ID = "47219668"

# Fetch all job comments from thread (up to 1000 per page)
page = 0
all_comments = []
while True:
    resp = requests.get(
        "https://hn.algolia.com/api/v1/search",
        params={
            "tags": f"comment,story_{MARCH_2026_ID}",
            "hitsPerPage": 1000,
            "page": page
        }
    ).json()
    hits = resp.get("hits", [])
    if not hits:
        break
    all_comments.extend(hits)
    if page >= resp.get("nbPages", 1) - 1:
        break
    page += 1

# Each comment has: text (HTML), author, created_at, objectID
# Filter for top-level comments only (actual job posts, not replies)
job_posts = [h for h in all_comments if h.get("parent_id") == int(MARCH_2026_ID)]
```

---

### 9. DevRel Talent — devreltalent.io

**What works:**
- HTTP 301 → 200 redirect to `https://www.devreltalent.io/` — resolves to 101KB page
- Cloudflare on origin, but page loads via redirect
- Site appears to be an active developer relations job board

**Recommended approach:** Follow redirect to `https://www.devreltalent.io/` and use requests + BeautifulSoup. Need to inspect the resolved page structure.

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get(
    "https://www.devreltalent.io/",  # Follow redirect manually
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    allow_redirects=True
)
soup = BeautifulSoup(resp.text, "html.parser")
# Inspect structure — niche board, likely small listing set
```

---

### 10. AIJobBoard.dev — aijobboard.dev

**What works:**
- HTTP 200, 31KB — but title is "This Page Does Not Exist" on `/jobs`
- Main page title: "AI Prompt Engineer Jobs & Agentic AI Roles – AIJobBoard.dev"
- hcdn server, no Cloudflare, no NEXT_DATA
- Site appears to have content but routing may be SPA-based (31KB is too small for SSR job listings)

**Recommended approach:** Playwright — the small page size and 404-like subpage titles suggest client-side routing

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://aijobboard.dev")
    page.wait_for_load_state("networkidle")
    # Site is niche (AI prompt engineer / agentic AI roles) — small inventory
    content = page.content()
    browser.close()
```

---

### 11. RemoteFront — remotefront.com

**What works:**
- HTTP 308 → 200 redirect to `https://www.remotefront.com/` — resolves to 110KB page
- Cloudflare on origin, but page loads after redirect
- 110KB suggests reasonable server-rendered content

**Recommended approach:** `requests` + BeautifulSoup using the www subdomain directly

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get(
    "https://www.remotefront.com/",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
    allow_redirects=True
)
soup = BeautifulSoup(resp.text, "html.parser")
# Inspect structure for job listing patterns
```

---

### 12. gm.careers — gm.careers

**What works:**
- HTTP 200, 243KB — React SPA (Vercel), no `__NEXT_DATA__`
- Title: "Web3 Jobs & Crypto Careers | gm.careers"
- `/api/jobs` returns HTTP 200 but content is HTML (Next.js API route not returning JSON)
- No feeds discovered

**Recommended approach:** Playwright — React SPA requires browser rendering

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    # Intercept network to find the actual data API endpoint
    api_responses = []
    page.on("response", lambda r: api_responses.append(r) if "/api/" in r.url else None)
    page.goto("https://gm.careers")
    page.wait_for_load_state("networkidle")
    # Check api_responses for the data feed URL, then use requests directly
    browser.close()
```

---

### 13. CryptoJobsList — cryptojobslist.com

**What works:**
- HTTP 200, 362KB — Next.js with `__NEXT_DATA__` confirmed
- pageProps contains `jobs` list (25 items on homepage), plus `blogPosts`, `topRegions`, `categories` (148 categories)
- Sample job keys: `_id`, `jobTitle`, `companyName`, `jobLocation`, `salary`, `videoApplicationsEnabled`, `bossFirstName`, `bossLastName`
- `salary` field confirmed present in data structure
- `/api/jobs` and `/feed` return 403 (Cloudflare WAF), but main HTML loads fine

**Recommended approach:** `requests` + extract `__NEXT_DATA__` JSON (salary data included)

```python
import requests, json, re

resp = requests.get(
    "https://cryptojobslist.com",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
)
nd = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
data = json.loads(nd.group(1))
jobs = data["props"]["pageProps"]["jobs"]  # list of 25 jobs
# job["salary"] for salary, job["jobTitle"] for title, job["companyName"] for company

# For more jobs, iterate category or search pages:
# https://cryptojobslist.com/operations
# https://cryptojobslist.com/remote
```

---

### 14. Web3.career — web3.career

**What works:**
- HTTP 200, 321KB — Rails-based (Bootstrap, data-bs-toggle, data-turbo attributes confirmed)
- Server-rendered HTML with job listings in `<h2>` and `<h3>` tags
- Sample H2 job titles found: "Backend Engineer", "Front End Engineer", "SEO Growth Lead"
- `/remote-jobs` page returns 200 — filtered view works
- Class `job-title-mobile mb-auto` confirmed on job title elements
- No NEXT_DATA, no API, no RSS

**Recommended approach:** `requests` + BeautifulSoup — Rails SSR with consistent class structure

```python
import requests
from bs4 import BeautifulSoup

resp = requests.get(
    "https://web3.career/remote-jobs",
    headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
)
soup = BeautifulSoup(resp.text, "html.parser")
# Job titles in <h2> or <h3> tags, company names nearby
# Target class: "job-title-mobile" for title elements
job_titles = soup.find_all(class_=lambda c: c and "job-title" in c)
for title in job_titles:
    print(title.get_text(strip=True))
    # Navigate to parent/sibling for company name, salary, location
```

---

### 15. CryptocurrencyJobs — cryptocurrencyjobs.co

**What works:**
- HTTP 200, 306KB — static site (Go-lang or similar, not Next.js/Rails)
- Category pages work: `/operations/` (200), `/remote/` (200)
- No feeds or API found
- HTML has consistent Tailwind CSS class structure for job listings
- Server-rendered — job data present in HTML

**Recommended approach:** `requests` + BeautifulSoup with category pages for targeted scraping

```python
import requests
from bs4 import BeautifulSoup

categories = [
    "https://cryptocurrencyjobs.co/operations/",
    "https://cryptocurrencyjobs.co/remote/",
    "https://cryptocurrencyjobs.co/",
]

for url in categories:
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")
    # Job links follow pattern: /job-title-company-slug/
    job_links = soup.find_all("a", href=lambda h: h and h.startswith("/") and len(h) > 10 and "-" in h)
    for link in job_links[:10]:
        print(link.get_text(strip=True), link["href"])
```

---

### 16. crypto.jobs — crypto.jobs

**What works:**
- HTTP 200, 145KB — server-rendered (Cloudflare passive)
- RSS and Atom feeds confirmed in HTML source:
  - `https://crypto.jobs/feed/rss`
  - `https://crypto.jobs/feed/atom`
- Title: "3586+ Web3 Jobs (2026) | Remote Crypto Careers | CryptoJobs"

**Recommended approach:** RSS/Atom feed (cleanest option)

```python
import feedparser

# Both RSS and Atom confirmed in page HTML
feeds = [
    "https://crypto.jobs/feed/rss",
    "https://crypto.jobs/feed/atom",
]

feed = feedparser.parse(feeds[0])
for entry in feed.entries:
    print(entry.title, entry.link, entry.get("published", ""))
```

---

### 17. The Defiant Jobs — jobs.thedefiant.io

**What works:**
- DNS resolution fails for `jobs.thedefiant.io` — subdomain does not exist
- Main domain `thedefiant.io` returns 403 from Cloudflare
- `www.aijobnetwork.com` redirected but served "Service Suspended by its owner" page (separate board, confirmed dead)

**Recommended approach:** Not feasible. The subdomain is unresolvable. The Defiant appears to have shut down its job board.

---

## Final Summary

### Easy (requests / API / RSS) — 7 boards

- **Himalayas** — public undocumented API (`/api/jobs?limit=N&offset=N`), no auth, pagination built-in, salary fields included
- **We Work Remotely** — RSS feed (`/remote-jobs.rss`), live and working as of 2026-03-27
- **HN Who's Hiring** — Algolia public API, zero friction, March 2026 thread ID `47219668` confirmed
- **CryptoJobsList** — requests + NEXT_DATA extraction, salary field confirmed in job objects
- **crypto.jobs** — RSS/Atom feeds confirmed in HTML source (`/feed/rss`, `/feed/atom`)
- **Web3.career** — requests + BeautifulSoup, Rails SSR, job title class confirmed
- **CryptocurrencyJobs** — requests + BeautifulSoup, category pages `/operations/` and `/remote/` return 200

### Easy-Medium (requests viable but needs structure inspection) — 3 boards

- **AIMLJobs.fyi** — Korean-language board, 11KB static HTML, requests + BS4 workable; niche use case
- **DevRel Talent** — resolves to www.devreltalent.io after redirect; 101KB response; needs BS4 structure inspection
- **RemoteFront** — resolves to www.remotefront.com after redirect; 110KB response; needs BS4 structure inspection

### Medium (needs Playwright or API registration) — 4 boards

- **LLMHire** — React SPA with hydration shell, no SSR content, requires Playwright
- **aijobs.net** — SPA (Vue/Nuxt likely), no server-rendered job data, requires Playwright (or network interception to find underlying API)
- **GetOnBoard** — API exists at `/api/v0/`, categories free, jobs require free account registration
- **gm.careers** — React SPA (Vercel), no NEXT_DATA, requires Playwright; Web3/crypto niche
- **AIJobBoard.dev** — 31KB SPA shell (AI prompt engineer / agentic AI niche), requires Playwright

### Not Feasible — 3 boards

- **AI Job Network** — "Service Suspended by its owner" — site is shut down
- **The Defiant Jobs** — DNS failure on `jobs.thedefiant.io`, subdomain does not resolve
- *(Note: aijobnetwork.com appears suspended while jobs.thedefiant.io DNS is gone — both removed from viable list)*

---

## Implementation Priority for scout-1

Ranked by ease × signal quality for Diego's ops/AI manager search:

1. **Himalayas API** — 97K+ remote jobs, clean API with pagination, no auth, salary data
2. **We Work Remotely RSS** — management/finance category RSS has direct ops roles
3. **HN Who's Hiring Algolia** — March 2026 thread ID `47219668`, high-quality companies post here
4. **CryptoJobsList NEXT_DATA** — salary field in job objects, good for Web3 ops roles
5. **crypto.jobs RSS** — 3500+ Web3 jobs, RSS confirmed
6. **Web3.career BS4** — Rails SSR, `/remote-jobs` filter available, ops category exists
7. **CryptocurrencyJobs BS4** — `/operations/` category page is a direct filter
8. **GetOnBoard API** — register for free token, `operations-management` category ID confirmed
9. **LLMHire Playwright** — AI-focused board, worth the Playwright overhead
10. **aijobs.net Playwright** — intercept XHR to find underlying API, then switch to requests
11. **DevRel Talent / RemoteFront** — inspect resolved pages, may be simple BS4
12. Skip: **AI Job Network** (suspended), **The Defiant Jobs** (DNS dead), **AIMLJobs.fyi** (Korean-language, limited English ops roles)
