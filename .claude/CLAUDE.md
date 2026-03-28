# Board Aggregator Research Pipeline

## What this project is

A 4-phase job research pipeline that scrapes job postings, scores them against Diego's skills, finds hiring managers, and generates personalized pitch materials. Anti-mass-apply: quality over quantity.

## Running the pipeline

```
claude --agent lead-0
```

## Agent names

Non-descriptive names to prevent Claude from inferring default behaviors:
- `lead-0` — pipeline orchestrator
- `scout-1` — Phase 1: job board scraping (board-aggregator CLI + Chrome)
- `ranker-7` — Phase 2: fit scoring against skills-inventory.md
- `recon-3` — Phase 3: contact research (Exa + Chrome)
- `composer-4` — Phase 4: pitch material generation

## board-aggregator CLI

Scout-1 calls the `board-aggregator` CLI (installed in `.venv/`) which scrapes 13 boards:
- python-jobspy: Indeed, LinkedIn, Glassdoor, Google, ZipRecruiter
- Custom scrapers: Himalayas, We Work Remotely, HN Who's Hiring, CryptoJobsList, crypto.jobs, web3.career, CryptocurrencyJobs, RemoteOK

Source code: `board_aggregator/` — registry-pattern scrapers with Pydantic models, dedup, CSV+MD output.

## Directory conventions

- `research/phase-1-scrape/` — Scraped postings (created at runtime by scout-1)
- `research/phase-2-rank/` — Scored and tiered opportunities (created by ranker-7)
- `research/phase-3-contacts/[company-slug]/` — Contact profiles + company context (created by recon-3)
- `research/phase-4-pitch/[company-slug]/` — Video scripts + DM drafts + outreach status (created by composer-4)

## Key input files

- `skills-inventory.md` — Diego's complete skills inventory (input to Phase 2)
- `resume-diego-gomez-ops-ai.md` — Tailored resume (input to Phase 4)
- `vocaroo-script.md` — Voice/tone reference for pitch scripts

## Subagent output contract

ALL subagents MUST:
1. Write verbose output to `research/` files
2. Return ONLY 1-2 sentence summaries to the lead agent
3. NEVER return raw data in responses

This constraint survives context compaction because it is in CLAUDE.md.

## Forbidden patterns

- Never mass-apply or auto-submit applications
- Never send DMs automatically (human-in-the-loop always)
- Never fabricate skills or experience in pitch materials
- Never accumulate large data in agent context (write to files)
- Never edit the same file from multiple parallel agents
