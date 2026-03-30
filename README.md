# Agent Job Research Pipeline

A 4-phase job research pipeline that scrapes job postings, scores them against a candidate's skills inventory, finds hiring managers, and generates personalized pitch materials. Quality over quantity -- anti-mass-apply.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the full pipeline
claude --agent lead-0
```

## How It Works

The pipeline runs as a Claude Code agent team, orchestrated by `lead-0`:

| Phase | Agent | What it does |
|-------|-------|-------------|
| 1 | scout-1 | Scrapes 10 job boards via `board-aggregator` CLI |
| 2 | ranker-7 | Scores postings against `skills-inventory.md` (salary, skills match, experience, growth, remote fit) |
| 3 | recon-3 | Finds hiring managers via Exa + Chrome (parallel per company) |
| 4 | composer-4 | Generates 30-40s video scripts + DM drafts (parallel per company) |

## board-aggregator CLI

The scraping engine is a standalone Python CLI:

```bash
# Scrape all 10 boards
.venv/bin/board-aggregator -q "AI Operations Lead" -o output_dir

# Scrape specific boards only
.venv/bin/board-aggregator -q "query" -s himalayas -s remoteok

# List available scrapers
.venv/bin/board-aggregator --list-scrapers
```

**Boards covered:**
- python-jobspy: Indeed, LinkedIn
- Custom scrapers: Himalayas, We Work Remotely, HN Who's Hiring, CryptoJobsList, crypto.jobs, web3.career, CryptocurrencyJobs, RemoteOK

## Project Structure

```
.claude/agents/          # Agent definitions (lead-0, scout-1, ranker-7, recon-3, composer-4)
board_aggregator/        # Python package -- job board scraping engine
  scrapers/              # 9 scraper classes (registry pattern)
  cli.py                 # Click CLI entrypoint
  runner.py              # Orchestration + dedup
  models.py              # JobPosting Pydantic model
  output.py              # CSV + Markdown writers
tests/                   # Per-scraper tests with mocked HTTP + real fixtures
research/runs/           # Pipeline output (gitignored, timestamped per run)
skills-inventory.md      # Candidate skills inventory (input to Phase 2+4)
resume-*.md              # Tailored resume (input to Phase 4)
docs/CODEBASE_MAP.md     # Detailed architecture map
```

## Run Versioning

Each pipeline run writes to `research/runs/<timestamp>/` with phase subdirectories. The `research/latest` symlink always points to the most recent run. Last 5 runs are retained.

## Tests

```bash
.venv/bin/pytest
```

Tests use mocked HTTP responses with real HTML/JSON fixtures captured from live sites.

## Requirements

- Python >= 3.12
- Claude Code CLI with Exa MCP and Claude-in-Chrome MCP configured
