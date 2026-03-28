# Himalayas API Field Mapping

Captured from: `GET https://himalayas.app/jobs/api?limit=3&offset=0`
Captured on: 2026-03-28

## Correct endpoint

The working endpoint is `/jobs/api` (NOT `/api/jobs`).

- Browse: `https://himalayas.app/jobs/api?limit=20&offset=0`
- Search: `https://himalayas.app/jobs/api/search?q=...`

Max `limit` per request is 20.

## Top-level response fields

| Field | Type | Example value |
|---|---|---|
| `comments` | string | `"13/03/2026: The API has been updated to include the companySlug field in the response."` |
| `updatedAt` | number (Unix ms) | `1774692720` |
| `offset` | number | `0` |
| `limit` | number | `3` |
| `totalCount` | number | `95423` |
| `jobs` | array of job objects | see below |

## Job object fields

| Field | Type | Nullable | Example value |
|---|---|---|---|
| `title` | string | no | `"Senior Front-End Developer"` |
| `excerpt` | string | no | `"Miratech is a global IT services..."` |
| `companyName` | string | no | `"Miratech"` |
| `companySlug` | string | no | `"miratech"` |
| `companyLogo` | string (URL) | no | `"https://cdn-images.himalayas.app/..."` |
| `employmentType` | string (enum) | no | `"Full Time"` |
| `minSalary` | number | yes (null) | `108700` or `null` |
| `maxSalary` | number | yes (null) | `163100` or `null` |
| `seniority` | array of strings | no | `["Senior"]` |
| `currency` | string (ISO 4217) | no | `"USD"` or `"PHP"` |
| `locationRestrictions` | array of strings | no | `["Ukraine"]` or `["United States", "Canada"]` or `[]` for worldwide |
| `timezoneRestrictions` | array of numbers | no | `[2, 3]` (UTC offsets as numbers, including fractions like `-3.5`) |
| `categories` | array of strings | no | `["Senior-Frontend-Engineer", "Front-End-Developer"]` (slug format) |
| `parentCategories` | array of strings | no | `["Developer"]` or `[]` |
| `description` | string (sanitized HTML) | no | `"<p>...</p>"` |
| `pubDate` | number (Unix ms) | no | `1774692720` |
| `expiryDate` | number (Unix ms) | no | `1779876720` |
| `applicationLink` | string (URL) | no | `"https://himalayas.app/companies/miratech/jobs/..."` |
| `guid` | string (URL) | no | `"https://himalayas.app/companies/miratech/jobs/..."` (same as applicationLink) |

## Key schema notes for test fixtures

- Salary fields: `minSalary` / `maxSalary` (NOT `salary_min`/`salary_max` or `min_salary`/`max_salary`)
- Company name: `companyName` (camelCase, NOT `company_name` or `company`)
- Company slug: `companySlug` (added 2026-03-13)
- Dates: `pubDate` and `expiryDate` are Unix timestamps in **milliseconds** (not seconds)
- `locationRestrictions`: array of country name strings (NOT alpha2 codes) — e.g., `"United States"` not `"US"`
  - Note: the API docs schema shows objects with `{alpha2, name, slug}` but the actual live response returns plain strings
- `timezoneRestrictions`: array of numbers representing UTC offsets (can be fractional, e.g., `-3.5`, `5.5`, `8.75`)
- `seniority`: always an array even when single value
- `employmentType` enum values observed: `"Full Time"` (with space, not hyphen)
- `guid` and `applicationLink` contain the same Himalayas URL value

## Observed employment type values (from docs)

`Full Time` | `Part Time` | `Contractor` | `Temporary` | `Intern` | `Volunteer` | `Other`

## Observed seniority values (from docs)

`Entry-level` | `Mid-level` | `Senior` | `Manager` | `Director` | `Executive`
