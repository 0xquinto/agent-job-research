# Glassdoor City Test — 2026-03-27

## Query
- search_term: "Operations Manager AI"
- results_wanted: 15
- hours_old: 72
- is_remote: True

## Results

| City | Results | Error |
|------|---------|-------|
| New York, NY | 0 | "Error encountered in API response" |
| San Francisco, CA | 0 | "Error encountered in API response" |
| Austin, TX | 0 | "Error encountered in API response" |

## Diagnostic

A broader test (no hours_old filter, simpler query "Operations Manager", NYC) returned:
`Glassdoor response status code 400 — location not parsed`

This is a **Glassdoor API-level failure**, not a city-specific behavior difference. python-jobspy's
Glassdoor connector is returning HTTP 400 across all cities and query variants, indicating the
underlying API endpoint or authentication token is broken/blocked as of this date.

## Overlap Analysis

Cannot be performed — no data returned from any city.

## Verdict

**INCONCLUSIVE — Glassdoor API currently broken (HTTP 400 on all requests)**

The city-comparison question cannot be answered today because python-jobspy's Glassdoor scraper
is returning errors for all tested locations. The question remains open for a future re-test.

### Recommendation for scout-1

- Drop `site_name=['glassdoor']` from scrape calls until the connector is repaired upstream
  (track: https://github.com/Bunsly/JobSpy/issues)
- If Glassdoor coverage is needed, fall back to Chrome-based browsing of glassdoor.com directly
- Re-run this city test when a new JobSpy version is released that fixes the 400 error

### If/when Glassdoor is restored — cities to test

If results differ by city, recommend a **3-city loop**: New York, San Francisco, Austin. These
represent the three largest US tech/ops hiring markets and are geographically distinct enough to
surface different local postings if Glassdoor uses geo-partitioned indexes.
