# Field Mapping: cryptocurrencyjobs.co

Source URL: https://cryptocurrencyjobs.co/operations/
Crawl date: 2026-03-28
Method: Chrome browser accessibility tree + live page inspection

---

## Page Architecture

The page renders **two identical `<ul>` lists** of job cards:

1. **Static server-rendered list** — present in raw HTML, parseable by `requests` + BeautifulSoup
2. **Algolia JS-enhanced list** — rendered after JS executes, requires Selenium/Playwright

For `scout-1` (the requests-based scraper), **target the first `<ul>`**.

The static list is preceded by the text "JavaScript is currently disabled" notice, then the job count text (e.g., "4879 blockchain jobs"), then the `<ul>`.

```python
# Reliable selector for the static list
all_uls = soup.find_all('ul')
# The job list is the first large <ul> inside <main>
main = soup.find('main')
job_list = main.find('ul')  # first <ul> in main is the jobs list
job_cards = job_list.find_all('li', recursive=False)
```

---

## Job Card Structure (`<li>`)

Each job card is a `<li>` element with this child structure (in order):

| Position | Element | Content | Notes |
|----------|---------|---------|-------|
| 1 | `<img>` | Company logo | `alt="[Company] logo"`, `src="/startups/assets/logos/[slug].jpg"` |
| 2 | `<h2><a>` | Job title | `href="/[category]/[company-slug]-[job-slug]/"` |
| 3 | `<h3><a>` | Company name | `href="/startups/[company-slug]/"` — `<a>` may be absent if no company profile |
| 4 | `<ul><li><h4><a>` | Location(s) | Multiple `<li>` for multi-location jobs; `href="/remote/"` or `"/[city-slug]/"` |
| 5 | `<h4><a>` | Department | `href="/operations/"` (or other department slug) |
| 6 | `<ul><li><h4><a>` | Employment type(s) | "Full-Time", "Part-Time", "Contract", "Internship" — multiple `<li>` possible |
| 7 | `<span>` | **Salary** | **OPTIONAL** — absent when undisclosed. Format: "$110K – $150K" or "€50K – €75K" |
| 8 | `<ul><li>` | Tags/keywords | Mix of `<a href="/[tag]/">` links and plain `<span>` text nodes |
| 9 | `<span>` | Date posted | Relative: "Today", "1d", "3d", "9w" — no absolute date |
| 10 | `<span>` | Featured badge | **OPTIONAL** — text "Featured", present only for promoted listings |

---

## CSS / Tailwind Classes

**The site uses Tailwind CSS utility classes. Do NOT rely on class selectors for parsing.**

Why: Tailwind classes are presentational (e.g., `flex`, `border-b`, `py-4`, `text-sm`) and encode no semantic meaning. They may change at any deployment.

**Always use tag + structural selectors** (e.g., `li > h2 > a`, `li > span`).

No custom semantic class names were identified on job card elements (e.g., no `.job-card`, `.job-title`, `.company-name`).

---

## BeautifulSoup Field Extraction

```python
from bs4 import BeautifulSoup

def parse_job_card(li):
    """Extract fields from a single job card <li> element."""
    result = {}

    # Job title + URL
    title_tag = li.select_one('h2 a')
    if title_tag:
        result['title'] = title_tag.get_text(strip=True)
        result['url'] = 'https://cryptocurrencyjobs.co' + title_tag['href']

    # Company name
    company_tag = li.find('h3')
    if company_tag:
        company_link = company_tag.find('a')
        result['company'] = company_link.get_text(strip=True) if company_link else company_tag.get_text(strip=True)

    # Company logo
    img = li.find('img')
    if img:
        result['company_logo'] = img.get('src', '')

    # Location(s) — first <ul> inside <li> contains locations
    # Department is a standalone <h4> (not nested in a <ul>)
    # Employment type(s) — second <ul> inside <li> contains types
    uls = li.find_all('ul', recursive=False)

    if len(uls) >= 1:
        locations = [a.get_text(strip=True) for a in uls[0].find_all('a')]
        result['locations'] = locations

    if len(uls) >= 2:
        emp_types = [a.get_text(strip=True) for a in uls[1].find_all('a')]
        result['employment_types'] = emp_types

    # Department: the <h4> that is a direct child of <li> (not inside a <ul>)
    dept_h4 = li.find('h4')  # first h4 encountered in document order
    # NOTE: direct child h4s come AFTER location ul, so find_all then filter
    all_h4 = li.find_all('h4')
    # The department h4 is the one whose parent is the <li> itself
    dept = next((h4 for h4 in all_h4 if h4.parent == li), None)
    if dept:
        result['department'] = dept.get_text(strip=True)

    # Salary: look for a <span> whose text matches salary pattern
    import re
    salary_pattern = re.compile(r'[\$€£][\d,K]+')
    all_spans = li.find_all('span', recursive=False)
    result['salary'] = None
    for span in all_spans:
        text = span.get_text(strip=True)
        if salary_pattern.search(text):
            result['salary'] = text
            break

    # Tags: last <ul> in the <li> (after salary span, before date)
    if len(uls) >= 3:
        tags = [item.get_text(strip=True) for item in uls[2].find_all('li')]
        result['tags'] = tags
    elif len(uls) >= 1:
        # Fallback: tags ul is the last ul
        tags = [item.get_text(strip=True) for item in uls[-1].find_all('li')]
        result['tags'] = tags

    # Date posted + featured status
    # Spans at end of card: [..., date_span] or [..., date_span, featured_span]
    all_spans_list = li.find_all('span', recursive=False)
    non_salary_spans = [s for s in all_spans_list if not salary_pattern.search(s.get_text(strip=True))]

    result['featured'] = False
    result['date_posted'] = None

    if non_salary_spans:
        last_span = non_salary_spans[-1]
        if last_span.get_text(strip=True) == 'Featured':
            result['featured'] = True
            if len(non_salary_spans) >= 2:
                result['date_posted'] = non_salary_spans[-2].get_text(strip=True)
        else:
            result['date_posted'] = last_span.get_text(strip=True)

    return result
```

---

## Salary Data

- **Present when**: employer explicitly discloses compensation
- **Absent when**: not disclosed (no empty placeholder, element simply missing)
- **Currency formats observed**:
  - USD: `$110K – $150K`, `$127.4K – $191.2K`, `$120K` (single value), `$100K – $180K`
  - EUR: `€50K – €75K`, `€31.5K`
- **Location in DOM**: `<span>` as direct child of `<li>`, between employment type `<ul>` and tags `<ul>`
- **Frequency**: roughly 30–40% of listings include salary

---

## Date Format

- **Format**: relative strings only — `"Today"`, `"1d"`, `"2d"`, ..., `"9w"`, `"11w"`
- **No absolute date** is present in the HTML
- To get an absolute date: `date_posted = today - timedelta(days=int(date_str[:-1]))` when suffix is `d`; multiply by 7 for `w`
- `"Today"` = same calendar day as crawl

```python
from datetime import date, timedelta

def parse_relative_date(date_str: str, crawl_date: date = None) -> date:
    if crawl_date is None:
        crawl_date = date.today()
    if date_str == 'Today':
        return crawl_date
    if date_str.endswith('d'):
        return crawl_date - timedelta(days=int(date_str[:-1]))
    if date_str.endswith('w'):
        return crawl_date - timedelta(weeks=int(date_str[:-1]))
    return crawl_date  # fallback
```

---

## Job URL Pattern

```
https://cryptocurrencyjobs.co/[department]/[company-slug]-[job-title-slug]/
```

Examples:
- `/operations/ethena-labs-financial-associate/`
- `/operations/legacy-customer-success-lifecycle-operations-manager/`
- `/operations/copper-business-analyst/`
- `/operations/chainalysis-senior-recruiter-sales-gtm/`

The `[department]` segment matches the category page being scraped (e.g., `operations`).

---

## Company Profile URL Pattern

```
https://cryptocurrencyjobs.co/startups/[company-slug]/
```

---

## Tag/Keyword Links

Tags link to `https://cryptocurrencyjobs.co/[tag-slug]/`. Examples:
- `/defi/`, `/finance/`, `/web3/`, `/non-tech/`, `/operations-manager/`
- `/ai/`, `/customer-success/`, `/recruiter/`, `/product/`

Some tags appear as plain `<span>` text (no `<a>` link) — typically niche skills not given a category page.

---

## Featured vs Non-Featured

- **Featured**: paid/promoted listings; appear at top of list; have `<span>Featured</span>` as last child
- **Non-featured**: organic listings below featured; NO `<span>Featured</span>`
- Both types are structurally identical otherwise

---

## Multi-Location Jobs

When a job lists multiple locations, there are multiple `<li>` items inside the location `<ul>`:

```html
<ul>
  <li><h4><a href="/new-york-ny/">New York (NY)</a></h4></li>
  <li><h4><a href="/remote/">Remote - EU</a></h4></li>
</ul>
```

Observed multi-location patterns:
- `New York (NY)` + `Remote - EU`
- `Paris` + `Remote - -5h GMT up to +2h GMT`
- `New York (NY)` + `San Francisco (CA)`

---

## Page Metadata

- Job count text: `"[N] blockchain jobs"` appears as a `<span>` or `<p>` before the job list
- Category filter shown in `<nav>` before the list (links to subcategory pages)
- Algolia search widget present but degrades gracefully — static list always renders

---

## Scraped Field Summary

| Field | Selector Strategy | Always Present |
|-------|------------------|----------------|
| `title` | `li > h2 > a` text | Yes |
| `url` | `li > h2 > a[href]` | Yes |
| `company` | `li > h3` text | Yes |
| `company_url` | `li > h3 > a[href]` | Usually (absent if no profile) |
| `locations` | `li > ul:first-of-type li a` text | Yes (1+) |
| `department` | `li > h4` (direct child, not nested) text | Yes |
| `employment_types` | `li > ul:nth-of-type(2) li a` text | Yes (1+) |
| `salary` | `li > span` matching `$`/`€` pattern | No (~30-40%) |
| `tags` | `li > ul:last-of-type li` text | Yes (1+) |
| `date_posted` | second-to-last `li > span` (if featured) or last | Yes |
| `featured` | presence of `<span>Featured</span>` | No |
