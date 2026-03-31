# Exa MCP Upgrade Plan

## Status: Applied

**Date:** 2026-03-31
**Context:** Audited Exa Agent Skills from https://exa.ai/docs/reference/. Upgraded recon-3 to use `web_search_advanced_exa` with category routing.

---

## Current State

The Exa MCP endpoint already exposes 10 tools:

```
web_search_exa, get_code_context_exa, deep_search_exa, crawling_exa,
company_research_exa, linkedin_search_exa, deep_researcher_start,
deep_researcher_check, people_search_exa, web_search_advanced_exa
```

recon-3 previously used only 4 of these (`people_search_exa`, `company_research_exa`, `web_search_exa`, `crawling_exa`) without category routing, numResults control, domain filtering, date filtering, or query variation.

---

## What changed

### recon-3.md tools line

Added `web_search_advanced_exa` (primary) and `linkedin_search_exa` (fallback for LinkedIn-specific searches). Kept `people_search_exa`, `company_research_exa`, and `crawling_exa` as focused fallbacks. Dropped `web_search_exa` (superseded by the advanced variant).

### recon-3.md search strategy

Replaced the 4-step flat list with a 6-step category-routed strategy:

1. **Find contacts** — `category: "people"`, `additionalQueries` for variation, LinkedIn fallbacks
2. **Company context** — `category: "company"`, structured metadata (headcount, funding)
3. **Recent news** — `category: "news"`, date-filtered, domain-scoped to quality sources
4. **Personal sites** — `category: "personal site"`, optional conversation starters
5. **Deep dive** — no category, broad context on specific people
6. **Browser fallback** — Chrome for auth-gated or JS-heavy pages

Each step documents category-specific parameter restrictions (e.g., `people` cannot use date/text filters; `company` cannot use domain filters).

### No MCP endpoint change needed

The existing endpoint already includes `web_search_advanced_exa`. No `claude mcp remove/add` required.

### No permissions change needed

`mcp__exa__*` wildcard in `settings.local.json` covers all Exa tools.

---

## Category parameter restrictions (reference)

| Category | `includeDomains` | `excludeDomains` | Date filters | `includeText`/`excludeText` |
|----------|:-:|:-:|:-:|:-:|
| people | LinkedIn only | NO | NO | NO |
| company | NO | NO | NO | YES |
| news | YES | YES | YES | YES |
| personal site | YES | YES | YES | YES |
| _(none)_ | YES | YES | YES | YES |

Universal: `includeText` and `excludeText` only support **single-item arrays**. Multi-item arrays cause 400 errors.

---

## Validation

1. Run `claude mcp list` to verify `web_search_advanced_exa` is available
2. Spawn recon-3 with a test company and verify it uses the new tool with categories
3. Compare Phase 3 output quality (richer company metadata, better contact coverage) against previous runs

---

## Reference: Exa Skill Sources

| Skill | URL | Used by |
|-------|-----|---------|
| Company Research | https://exa.ai/docs/reference/company-research-claude-skill | recon-3 (Step 2 fallback) |
| People Search | https://exa.ai/docs/reference/people-search-claude-skill | recon-3 (Step 1 fallback) |
| Personal Site Search | https://exa.ai/docs/reference/personal-site-search-claude-skill | recon-3 (Step 4) |
