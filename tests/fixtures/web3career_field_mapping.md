# web3.career HTML Field Mapping

Sources used: Chrome accessibility tree (live DOM, 2026-03-28) + confirmed working
scraper from https://github.com/Charubak/web3-career-bot/blob/main/boards.py

---

## Parent Container

```python
# The job list is a standard HTML table
soup.find("table")
# or with class:
soup.find("table", class_="table")
```

The `<tbody>` element has class `tbody` (same as the 2022 scraper confirmed):

```python
soup.find("tbody", class_="tbody")
```

---

## Job Row Selector (most reliable)

Each job is a `<tr>` element with an `onclick` attribute. This is the correct selector:

```python
rows = soup.select("tr[onclick]")
```

Do NOT use `soup.find_all("tr")` — that catches the header row and ad rows too.

---

## Job URL

Extracted from the `onclick` attribute value, not from an `href`:

```html
<tr onclick="tableTurboRowClick(event, '/senior-product-manager-privacy-base/148070')">
```

```python
import re
onclick = row.get("onclick", "")
match = re.search(r"'(/[^']+)'", onclick)
job_path = match.group(1)          # e.g. '/senior-product-manager-privacy-base/148070'
job_url = "https://web3.career" + job_path
```

URL pattern: `/[job-title-slug]-[company-slug]/[numeric-id]`

---

## Job Title

Inside `tds[0]` (first `<td>`), in an `<h2>` tag:

```html
<td class="job-title-col">
  <a href="/senior-product-manager-privacy-base/148070">
    <h2 class="job-title-mobile mb-auto">Senior Product Manager Privacy</h2>
  </a>
</td>
```

```python
tds = row.find_all("td")
h2 = tds[0].find("h2")
title = h2.get_text(strip=True) if h2 else tds[0].get_text(strip=True)
```

Confirmed class: `job-title-mobile mb-auto` (space-separated, both classes present).
Our feasibility research had `job-title-mobile` correct — the full class is `job-title-mobile mb-auto`.

---

## Company Name

Inside `tds[1]` (second `<td>`), in an `<h3>` tag:

```html
<td class="company-col">
  <a href="/senior-product-manager-privacy-base/148070">
    <h3>Base</h3>
  </a>
</td>
```

```python
h3 = tds[1].find("h3")
company = h3.get_text(strip=True) if h3 else tds[1].get_text(strip=True)
```

Note: Some rows have a company `<img>` logo before the `<a><h3>` — the h3 selector
still works because it searches the whole td.

---

## Posted Time

`<time>` element anywhere in the row (not always present — some older jobs omit it):

```html
<td class="posted-col">
  <time>11h</time>
</td>
```

```python
time_el = row.find("time")
posted = time_el.get_text(strip=True) if time_el else ""
# Values: "4h", "14h", "1d", "2d", etc.
```

---

## Location

Inside a `<td>` containing `<a>` links whose `href` includes `/web3-jobs-`:

```html
<!-- Remote job -->
<td class="location-col">
  <a href="/remote-jobs">Remote</a>
</td>

<!-- City job -->
<td class="location-col">
  <a href="/web3-jobs-warsaw">Warsaw</a>,
  <a href="/web3-jobs-poland">Poland</a>
</td>

<!-- US city -->
<td class="location-col">
  <a href="/web3-jobs-new-york">New York</a>,
  <a href="/web3-jobs-new-york">NY</a>,
  <a href="/web3-jobs-united-states">United States</a>
</td>
```

```python
location = ""
for td in tds[2:]:
    loc_link = td.find("a", href=lambda h: h and "/web3-jobs-" in h)
    if loc_link:
        location = loc_link.get_text(strip=True)
        break
# Returns first location token only (e.g. "Warsaw", "New York")
# For "Remote", href is "/remote-jobs" not "/web3-jobs-*" so this returns ""
# Handle Remote separately:
if not location:
    remote_link = row.find("a", href="/remote-jobs")
    if remote_link:
        location = "Remote"
```

---

## Salary

Inside `tds[4]` (fifth `<td>`), in a `<p>` tag:

```html
<!-- Explicit salary -->
<td class="salary-col">
  <p>$175k - $250k</p>
</td>

<!-- Estimated (no real salary) -->
<td class="salary-col">
  <p class="salary-estimate">Estimated salary based on similar jobs</p>
</td>
```

```python
salary = ""
if len(tds) > 4:
    p = tds[4].find("p")
    if p:
        raw = p.get_text(strip=True)
        # Filter out the "Estimated salary" placeholder
        if raw.startswith("$"):
            salary = raw   # e.g. "$175k - $250k", "$18k - $36k"
```

---

## Tags / Badges

Inside `tds[5]` (sixth `<td>`), each tag is an `<a>` with `href` like `/[tag-name]-jobs`:

```html
<td class="tags-col">
  <a href="/product-manager-jobs" class="badge">product manager</a>
  <a href="/non-tech-jobs" class="badge">non tech</a>
  <a href="/senior-jobs" class="badge">senior</a>
  <a href="/remote-jobs" class="badge">remote</a>
</td>
```

```python
tags = []
if len(tds) > 5:
    tags = [a.get_text(strip=True) for a in tds[5].find_all("a")]
```

---

## Rows to Skip

Not all `<tr onclick>` rows are real jobs. Skip rows where `tds[0]` has no `<h2>`:

```python
for row in soup.select("tr[onclick]"):
    tds = row.find_all("td")
    if len(tds) < 2:
        continue
    h2 = tds[0].find("h2")
    if not h2:
        continue  # ad row (e.g. Metana bootcamp banner)
    title = h2.get_text(strip=True)
    # ... parse rest of fields
```

---

## Complete Extraction Pattern

```python
import re
import requests
from bs4 import BeautifulSoup

BASE = "https://web3.career"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"}

def scrape_web3career(path="/remote-jobs"):
    resp = requests.get(BASE + path, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []
    for row in soup.select("tr[onclick]"):
        tds = row.find_all("td")
        if len(tds) < 2:
            continue
        h2 = tds[0].find("h2")
        if not h2:
            continue  # skip ad rows
        title = h2.get_text(strip=True)

        h3 = tds[1].find("h3")
        company = h3.get_text(strip=True) if h3 else ""

        onclick = row.get("onclick", "")
        match = re.search(r"'(/[^']+)'", onclick)
        url = BASE + match.group(1) if match else ""

        time_el = row.find("time")
        posted = time_el.get_text(strip=True) if time_el else ""

        location = ""
        for td in tds[2:]:
            loc_link = td.find("a", href=lambda h: h and "/web3-jobs-" in h)
            if loc_link:
                location = loc_link.get_text(strip=True)
                break
        if not location and row.find("a", href="/remote-jobs"):
            location = "Remote"

        salary = ""
        if len(tds) > 4:
            p = tds[4].find("p")
            if p:
                raw = p.get_text(strip=True)
                if raw.startswith("$"):
                    salary = raw

        tags = [a.get_text(strip=True) for a in tds[5].find_all("a")] if len(tds) > 5 else []

        jobs.append({
            "title": title,
            "company": company,
            "url": url,
            "posted": posted,
            "location": location,
            "salary": salary,
            "tags": tags,
        })
    return jobs
```

---

## Summary of Confirmed Structure

| Field    | Element        | Class / Selector                          | Notes                                    |
|----------|----------------|-------------------------------------------|------------------------------------------|
| Row      | `<tr>`         | `tr[onclick]`                             | onclick contains URL; skip rows with no h2 |
| URL      | `onclick` attr | regex `'(/[^']+)'`                        | prepend `https://web3.career`            |
| Title    | `<h2>`         | `job-title-mobile mb-auto`                | inside `tds[0]`                          |
| Company  | `<h3>`         | (no class on h3)                          | inside `tds[1]`                          |
| Posted   | `<time>`       | (no class)                                | anywhere in row; absent on older posts   |
| Location | `<a>`          | `href` contains `/web3-jobs-`             | search `tds[2:]`; "Remote" uses `/remote-jobs` |
| Salary   | `<p>`          | (no class, or `salary-estimate`)          | `tds[4]`; only keep if starts with `$`  |
| Tags     | `<a>`          | `href` ends in `-jobs`                    | `tds[5]`                                 |
