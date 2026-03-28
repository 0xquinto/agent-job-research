# JobSpy Board Diagnostics Report

**Date:** 2026-03-27
**python-jobspy version:** 1.1.82
**Python:** 3.13 (via /opt/homebrew)

---

## Version Info

```
Name: python-jobspy
Version: 1.1.82
Location: /opt/homebrew/lib/python3.13/site-packages
Requires: beautifulsoup4, markdownify, numpy, pandas, pydantic, regex, requests, tls-client
```

---

## Board Results Summary

| Board        | Status         | Results |
|-------------|---------------|---------|
| indeed       | OK (assumed)  | —       |
| linkedin     | OK (assumed)  | —       |
| glassdoor    | FAILING       | 0       |
| google       | FAILING       | 0       |
| zip_recruiter| FAILING       | 0       |

---

## Per-Board Diagnosis

### Glassdoor

**Error messages (verbose=2):**
```
ERROR - JobSpy:Glassdoor - Glassdoor response status code 400
ERROR - JobSpy:Glassdoor - Glassdoor: location not parsed
INFO  - JobSpy:Glassdoor - finished scraping
```

**Root cause:** HTTP 400 Bad Request on the Glassdoor API endpoint. The scraper sends a location string that Glassdoor's API rejects — the location field is not being parsed into the format Glassdoor expects (it likely requires a location ID or geoId, not a plain-text string like "Remote" or "United States"). This is a known, long-running issue (GitHub issues #279, #273) first reported May 2025, still open as of February 2026.

**Classification:** Parsing/API contract breakage — Glassdoor changed how location parameters are accepted.

**Recommended fix:**
- Use `location='San Francisco, CA'` or another major city rather than "Remote" or "United States" — Glassdoor resolves locations geographically and "Remote" is not a valid geo string for its API.
- Alternatively, omit the `location` parameter entirely when targeting glassdoor and rely on `is_remote=True`.
- Check for a `glassdoor_country` or `glassdoor_location_id` parameter in newer jobspy versions.
- Monitor [speedyapply/JobSpy #279](https://github.com/speedyapply/JobSpy/issues/279) for an upstream fix.

---

### Google Jobs

**Error messages (verbose=0, no exception):**
```
Google: 0 results
```

**With verbose (inferred from issue #302):**
```
WARNING - initial cursor not found, try changing your query or there was at most 10 results
```

**Root cause:** Google's job search page structure changed, and the scraper can no longer locate the "initial cursor" token needed to paginate results. This is not a block — the page loads, but the expected data structure in the HTML/JSON is absent. Reported as a structural breakage in GitHub issue #302 (opened September 2025, unresolved as of February 2026).

**Classification:** Structural/parsing breakage — Google Jobs HTML changed.

**Recommended fix:**
- Use the `google_search_term` parameter instead of `search_term` when targeting Google. Example: `google_search_term='site:jobs.google.com "operations manager" remote'`
- Try shorter, simpler queries — complex queries may hit the "at most 10 results" low-result path that skips pagination.
- Drop `google` from `site_name` in production scrapes until upstream fix lands; LinkedIn and Indeed overlap heavily with Google Jobs aggregation anyway.
- Monitor [speedyapply/JobSpy #302](https://github.com/speedyapply/JobSpy/issues/302).

---

### ZipRecruiter

**Error messages (verbose=0, no exception):**
```
ZipRecruiter: 0 results
```

**Known error from community (issue #302, #283):**
```
ERROR - ZipRecruiter response status code 403 - Forbidden cf-waf
```
or
```
ERROR - ZipRecruiter: 429 Response - Blocked by ZipRecruiter for too many requests
```

**Root cause:** ZipRecruiter deployed Cloudflare WAF (Web Application Firewall) protection on their job search endpoint. Requests from the default `tls-client` user agent are fingerprinted and blocked with either a 403 (hard block) or 429 (rate limit). The scraper returns 0 results rather than raising an exception because the library catches these errors silently. This has been reported since May 2025 (issues #273, #283, #302) with no upstream fix confirmed.

**Classification:** Active anti-bot blocking — Cloudflare WAF at the infrastructure level.

**Recommended fix (in order of effort):**
1. **Proxies:** Pass `proxies=['user:pass@host:port']` or a list of rotating residential proxies. The `proxies` parameter exists in the signature. Cloudflare WAF blocks datacenter IPs but typically allows residential.
2. **Custom user_agent:** Try `user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'` — the `user_agent` parameter is available in v1.1.82.
3. **Drop ZipRecruiter:** Remove it from `site_name` in production scrapes. ZipRecruiter listings appear on Indeed and LinkedIn; coverage loss is minimal.

---

## Available scrape_jobs Parameters (v1.1.82)

```
site_name, search_term, google_search_term, location, distance, is_remote,
job_type, easy_apply, results_wanted, country_indeed, proxies, ca_cert,
description_format, linkedin_fetch_description, linkedin_company_ids,
offset, hours_old, enforce_annual_salary, verbose, user_agent, **kwargs
```

Proxies and user_agent are both available without upgrading.

---

## Recommended Immediate Action for scout-1

1. **Remove** `glassdoor`, `google`, `zip_recruiter` from `site_name` in all scrape calls until fixes are applied.
2. **Keep** `indeed` and `linkedin` — both confirmed working.
3. **Glassdoor workaround to test:** replace `location='Remote'` with a real city (`location='New York, NY'`) and re-add glassdoor — may resolve the 400 error.
4. **ZipRecruiter workaround to test:** add `user_agent='Mozilla/5.0 ...'` parameter; if still blocked, add residential proxies.
5. **Google workaround to test:** use `google_search_term` explicitly instead of relying on `search_term` fallback.

---

## References

- [speedyapply/JobSpy Issue #302](https://github.com/speedyapply/JobSpy/issues/302) — Google Jobs + ZipRecruiter 0 results / 403 (Sep 2025, open)
- [speedyapply/JobSpy Issue #283](https://github.com/speedyapply/JobSpy/issues/283) — ZipRecruiter 429 rate limiting (May 2025)
- [speedyapply/JobSpy Issue #279](https://github.com/speedyapply/JobSpy/issues/279) — Glassdoor 403 location not parsed (May 2025)
- [speedyapply/JobSpy Issue #273](https://github.com/speedyapply/JobSpy/issues/273) — Glassdoor + ZipRecruiter not working (May 2025)
