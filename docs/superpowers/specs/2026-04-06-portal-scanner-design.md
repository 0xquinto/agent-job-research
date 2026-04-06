# Portal Scanner Design Spec

## Problem

The pipeline discovers jobs through 10 broad board scrapers (board-aggregator CLI). This misses roles posted only on company career pages, especially companies using Greenhouse, Ashby, or Lever as their ATS. There's no mechanism to target specific companies or discover new companies matching Diego's profile.

## Solution

Two new components:

1. **discoverer-6** — standalone Claude agent that uses Exa deep search to find companies matching Diego's ICP, detects their ATS platform, and populates `portals.yml`.
2. **Portal scanner module** — Python module in `board_aggregator/` that reads `portals.yml` and fetches open roles from ATS APIs (Greenhouse, Ashby, Lever). Non-ATS companies are handled by scout-1 via Exa `crawling_exa`.

## Architecture

```
discoverer-6 (on-demand, standalone)
  reads: skills-inventory.md, portals.yml
  writes: portals.yml (new companies only)
  does: Exa deep search -> ATS detection -> ICP scoring -> append

scout-1 (during pipeline run)
  reads: portals.yml
  writes: $RUN_DIR/phase-1-scrape/
  does:
    Stage 1: board-aggregator -q "queries" --portals portals.yml -o dir
             (10 board scrapers + ATS portal scanner + dedup + output)
    Stage 2: Exa crawl for non-ATS portals (ats: null, stale only)
             (appends to all-postings.md, updates portals.yml timestamps)
```

### Field ownership

| Field | Written by | When |
|-------|-----------|------|
| `name`, `domain`, `ats`, `slug` | discoverer-6 | at discovery |
| `icp_fit_score`, `icp_fit_reasoning` | discoverer-6 | at discovery |
| `source`, `discovered_at` | discoverer-6 | at discovery |
| `last_scanned` | scout-1 | after scanning |
| `last_had_openings` | scout-1 | after scanning (if roles found) |
| `active` | scout-1 | set false after `disable_after_days` with no openings |

No field is written by both agents.

## portals.yml schema

```yaml
config:
  scan_interval_days: 7       # scan companies at most once per 7 days
  disable_after_days: 30      # auto-disable if no relevant openings for 30 days
  max_discovery_calls: 10     # cap Exa calls per discoverer-6 run
  icp_min_score: 6            # minimum fit score to add to portals

title_filter:
  positive: ["AI", "Operations", "Agent", "Automation", "DevRel", "ML", "LLM"]
  negative: ["Junior", "Intern", "PHP", "Java", ".NET"]

companies:
  - name: "Ramp"
    domain: "ramp.com"
    ats: "ashby"              # greenhouse | ashby | lever | null
    slug: "ramp"              # ATS-specific company slug
    icp_fit_score: 8
    icp_fit_reasoning: "AI-first fintech, agent automation"
    source: "exa-discovery"   # exa-discovery | manual
    discovered_at: "2026-04-06"
    last_scanned: null
    last_had_openings: null
    active: true
```

### ATS detection

discoverer-6 pattern-matches the careers URL to detect the ATS platform:

| URL pattern | ATS | Slug extraction |
|------------|-----|-----------------|
| `boards.greenhouse.io/{slug}` or `boards-api.greenhouse.io/v1/boards/{slug}` | `greenhouse` | path segment |
| `jobs.ashbyhq.com/{slug}` | `ashby` | path segment |
| `jobs.lever.co/{slug}` | `lever` | path segment |
| anything else | `null` | N/A (uses `careers_url` field instead) |

Companies with `ats: null` store a `careers_url` field for Exa crawling:

```yaml
  - name: "SomeStartup"
    domain: "somestartup.com"
    ats: null
    slug: null
    careers_url: "https://somestartup.com/careers"
    # ... other fields ...
```

## Portal scanner module

### Location

`board_aggregator/portal_scanner.py` — pure Python, no Exa dependency.

### Interface

```python
def scan_portals(portals_path: str) -> List[JobPosting]:
    """Read portals.yml, scan ATS companies due for refresh, return postings.
    
    Skips companies where:
    - active is False
    - last_scanned is within scan_interval_days
    - ats is null (handled by scout-1 via Exa)
    
    After scanning, writes portals_path back to disk with updated fields:
    - last_scanned: set to today for each scanned company
    - last_had_openings: set to today if roles were found
    - active: set to False if disable_after_days exceeded with no openings
    
    Returns the list of JobPosting objects (unfiltered by title_filter;
    caller is responsible for filtering and dedup).
    """
```

### ATS clients

Three functions, one per platform:

```python
def fetch_greenhouse(slug: str) -> List[JobPosting]
def fetch_ashby(slug: str) -> List[JobPosting]
def fetch_lever(slug: str) -> List[JobPosting]
```

### ATS API endpoints

| ATS | Endpoint | Auth |
|-----|----------|------|
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs` | None |
| Ashby | `GET https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true` | None |
| Lever | `GET https://api.lever.co/v0/postings/{slug}?mode=json` | None |

### Field mapping to JobPosting model

| `JobPosting` field | Greenhouse | Ashby | Lever |
|---|---|---|---|
| `title` | `title` | `title` | `text` |
| `company` | `company_name` | from portals.yml | from portals.yml |
| `description` | strip HTML from `content` | `descriptionPlain` | `descriptionPlain` |
| `job_url` | `absolute_url` | `jobUrl` | `hostedUrl` |
| `location` | `location.name` | `location` | `categories.location` |
| `is_remote` | parse `metadata` for "Location Type" | `isRemote` | `workplaceType == "remote"` |
| `salary_min` | `None` | `compensationTiers[0].components[0].minValue` | `salaryRange.min` |
| `salary_max` | `None` | `compensationTiers[0].components[0].maxValue` | `salaryRange.max` |
| `salary_currency` | `None` | `compensationTiers[0].components[0].currencyCode` | `salaryRange.currency` |
| `salary_interval` | `None` | parse from `interval` ("1 YEAR" -> "yearly") | `salaryRange.interval` |
| `source` | `"greenhouse"` | `"ashby"` | `"lever"` |

Salary fields are `None` when absent. No praying — deterministic path or nothing.

Ashby compensation extraction path: `compensation.compensationTiers[0].components[0]` — take the first tier's first salary-type component. Filter for `compensationType == "Salary"` to skip equity/bonus components.

### CLI integration

New flag on `board-aggregator`:

```bash
board-aggregator -q "query1" -q "query2" --portals portals.yml -o $RUN_DIR/phase-1-scrape
```

When `--portals` is passed, `runner.py` runs board scrapers first, then `scan_portals()`, feeds all results into one `deduplicate()` call, writes one unified `all-postings.md` and `all-postings.csv`.

### Title filtering

Portal results are filtered using `title_filter` from `portals.yml`:
- At least one `positive` keyword must appear in the title (case-insensitive)
- Zero `negative` keywords may appear
- Applied after ATS fetch, before dedup

### Deduplication

Uses existing `runner.py` `deduplicate()` with key `(title.lower(), company.lower())`. On collision, keeps the version with higher richness score (salary +3, description +2, date/type +1). Portal results naturally win most collisions due to richer structured data from ATS APIs.

No fuzzy title matching. Near-duplicates reaching ranker-7 is acceptable; false-positive dedup (merging different roles) is worse.

### Testing

Mocked HTTP with real JSON fixtures from each API. Same pattern as existing scrapers:
- `tests/fixtures/greenhouse_anthropic.json`
- `tests/fixtures/ashby_ramp.json`
- `tests/fixtures/lever_figma.json`
- `tests/test_portal_scanner.py`

## discoverer-6 agent definition

```
File: .claude/agents/discoverer-6.md

Name: discoverer-6
Tools: Read, Write, mcp__exa__web_search_advanced_exa,
       mcp__exa__company_research_exa, WebFetch
Model: sonnet
```

### Flow

1. Read `skills-inventory.md` -- derive micro-verticals (targeted Exa queries)
2. Read `portals.yml` -- collect existing domains to skip
3. For each micro-vertical (up to `max_discovery_calls`):
   - `web_search_advanced_exa` with `category: "company"`
   - Deduplicate against existing portals by domain
4. For each new company:
   - Find careers URL from Exa company data or quick web search
   - Pattern-match URL to detect ATS platform + extract slug
   - Score ICP fit 1-10 against skills inventory
   - If score >= `icp_min_score`: append to `portals.yml`
5. Return summary: "Discovered N new companies, M added to portals.yml"

### Micro-vertical derivation

The agent reads skills-inventory.md and generates queries like:
- "companies building multi-agent AI systems" (from agentic engineering)
- "AI inference optimization startups" (from inference portfolio)
- "LLM observability platforms" (from vLLM/SGLang experience)
- "developer tools AI automation" (from MCP server work)
- "crypto trading infrastructure" (from autoresearch-trading)

Each query uses `web_search_advanced_exa` with `category: "company"`, `numResults: 20`, `type: "auto"`.

### What it writes

Only `portals.yml` -- appending new entries to `companies[]` with fields: `name`, `domain`, `ats`, `slug`, `icp_fit_score`, `icp_fit_reasoning`, `source: "exa-discovery"`, `discovered_at`, `active: true`.

### What it never touches

`last_scanned`, `last_had_openings`, `active` flag changes, any run directory, any other file.

### Invocation

Standalone, not part of the pipeline:
```bash
claude --agent discoverer-6
```

## scout-1 changes

scout-1 gains one new stage and an updated CLI invocation.

### Updated Stage 1

```bash
cd /Users/diego/Dev/non-toxic/job-applications/agent-job-research
.venv/bin/board-aggregator \
  -q "Operations Manager AI" \
  -q "AI Operations Lead" \
  ... \
  --portals portals.yml \
  -o $RUN_DIR/phase-1-scrape
```

The `--portals` flag triggers ATS portal scanning alongside board scraping. Dedup is unified.

### New Stage 2: Exa crawl for non-ATS portals

After Stage 1, scout-1 reads `portals.yml` and filters for companies where:
- `ats` is `null` (no known ATS platform)
- `active` is `true`
- `last_scanned` is null or older than `scan_interval_days`

For each matching company:
1. Call `mcp__exa__crawling_exa` on the `careers_url`
2. Parse the crawl results for job listings (title + URL)
3. Apply `title_filter` from portals.yml
4. Create `JobPosting` objects and append to `$RUN_DIR/phase-1-scrape/all-postings.md`
5. Update `last_scanned` in `portals.yml`
6. Update `last_had_openings` if roles were found
7. Set `active: false` if `disable_after_days` exceeded with no openings

### Tool additions

scout-1 needs `mcp__exa__crawling_exa` added to its tool list.

## lead-0 changes

Minimal:
- Pass `portals.yml` path to scout-1 if the file exists
- No changes to phases 2-4

## Files changed / created

| File | Action |
|------|--------|
| `portals.yml` | New: portal registry (persistent, project root) |
| `board_aggregator/portal_scanner.py` | New: ATS client module |
| `board_aggregator/cli.py` | Modified: add `--portals` flag |
| `board_aggregator/runner.py` | Modified: integrate portal scanner into run pipeline |
| `.claude/agents/discoverer-6.md` | New: discovery agent definition |
| `.claude/agents/scout-1.md` | Modified: add Stage 2, add Exa crawl tool |
| `.claude/agents/lead-0.md` | Modified: pass portals.yml to scout-1 |
| `tests/test_portal_scanner.py` | New: portal scanner tests |
| `tests/fixtures/greenhouse_*.json` | New: Greenhouse API fixture |
| `tests/fixtures/ashby_*.json` | New: Ashby API fixture |
| `tests/fixtures/lever_*.json` | New: Lever API fixture |
