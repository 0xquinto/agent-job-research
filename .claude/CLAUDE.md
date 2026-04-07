# Agent Job Research Pipeline

## What this project is

A 4-phase job research pipeline that scrapes job postings, scores them against the user's skills, finds hiring managers, and generates personalized pitch materials. Anti-mass-apply: quality over quantity.

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
- `discoverer-6` — standalone company discovery via Exa (populates portals.yml, not part of main pipeline)

## board-aggregator CLI

Scout-1 calls the `board-aggregator` CLI (installed in `.venv/`) which scrapes 11 boards:
- python-jobspy: Indeed, LinkedIn
- Custom scrapers: Himalayas, We Work Remotely, HN Who's Hiring, CryptoJobsList, crypto.jobs, web3.career, CryptocurrencyJobs, RemoteOK, Reddit

Source code: `board_aggregator/` — registry-pattern scrapers with Pydantic models, dedup, CSV+MD output.

## Run versioning

Each pipeline run writes to a timestamped directory under `research/runs/`. The lead-0 orchestrator generates a `RUN_ID` at pipeline start and passes `RUN_DIR` to every subagent.

```
research/
  runs/
    2026-03-28T14-05-00/          # RUN_ID = ISO 8601, colons replaced with dashes
      meta.json                    # written by lead-0: timing, phase stats, queries
      phase-1-scrape/
      phase-2-rank/
      phase-3-contacts/{company-slug}/
      phase-4-pitch/{company-slug}/
    2026-03-27T09-22-11/          # previous run preserved
      ...
  latest -> runs/2026-03-28T14-05-00/   # symlink, always points to most recent run
```

**Rules:**
- lead-0 generates `RUN_ID` and computes `RUN_DIR=research/runs/$RUN_ID`
- lead-0 passes `RUN_DIR` to EVERY subagent prompt (not hardcoded in agent definitions)
- Subagents write ALL output under `$RUN_DIR/phase-X/`
- lead-0 updates the `research/latest` symlink after each successful run
- lead-0 writes `meta.json` at run start (partial) and updates it at run end (complete)
- Retention: keep last 5 runs. lead-0 prunes oldest before starting.

## Directory conventions

- `research/runs/$RUN_ID/phase-1-scrape/` — Scraped postings (created at runtime by scout-1)
- `research/runs/$RUN_ID/phase-2-rank/` — Scored and tiered opportunities (created by ranker-7)
- `research/runs/$RUN_ID/phase-3-contacts/[company-slug]/` — Contact profiles + company context (created by recon-3)
- `research/runs/$RUN_ID/phase-4-pitch/[company-slug]/` — Video scripts + DM drafts + outreach status (created by composer-4)
- `research/latest/` — Symlink to most recent run (updated by lead-0)

## Key input files

- `skills-inventory.md` — The user's complete skills inventory (input to Phase 2)
- `resume.md` — Tailored resume (input to Phase 4)

## Subagent output contract

ALL subagents MUST:
1. Write verbose output to `$RUN_DIR/` files (path provided by lead-0 in each prompt)
2. Return ONLY 1-2 sentence summaries to the lead agent
3. NEVER return raw data in responses

This constraint survives context compaction because it is in CLAUDE.md.

## Codebase Overview

4-phase Claude agent pipeline + Python scraping engine. Agents orchestrated by lead-0 (Opus), scrapers via `board_aggregator` Click CLI.

**Stack**: Python 3.12+, Click, Pydantic, python-jobspy, requests, feedparser, BeautifulSoup, Exa MCP, Claude-in-Chrome MCP
**Structure**: `.claude/agents/` (6 agent defs), `board_aggregator/` (10 scrapers, 11 boards), `tests/` (mocked HTTP)

For detailed architecture, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).

## Forbidden patterns

- Never mass-apply or auto-submit applications
- Never send DMs automatically (human-in-the-loop always)
- Never fabricate skills or experience in pitch materials
- Never accumulate large data in agent context (write to files)
- Never edit the same file from multiple parallel agents
- Never write to `research/` root — always write under `research/runs/$RUN_ID/`
