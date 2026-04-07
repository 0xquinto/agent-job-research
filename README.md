# agent-job-research

Agent pipeline that scrapes 10+ job boards, scores postings against your skills, finds hiring managers, and drafts personalized pitches. Anti-mass-apply.

## Prerequisites

1. **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
2. **Claude Code** — [claude.ai/download](https://claude.ai/download)
3. **git** — [git-scm.com](https://git-scm.com/)

## Setup

```bash
git clone https://github.com/0xQuinto/agent-job-research.git
cd agent-job-research
python setup_wizard.py
```

The wizard handles everything else: venv creation, dependency installation, profile templates (skills inventory + resume), Exa MCP server configuration, and validation.

Then run the pipeline:

```bash
claude --agent lead-0
```

## How the pipeline works

```
Phase 1 — Scrape       scout-1 runs board-aggregator CLI across 11 boards
Phase 2 — Rank         ranker-7 scores each posting against your skills inventory
Phase 3 — Research     recon-3 finds hiring managers via Exa + Chrome (parallel per company)
Phase 4 — Pitch        composer-4 generates video scripts + DM drafts (parallel per company)
```

The pipeline orchestrator (`lead-0`) runs phases sequentially. Within Phases 3 and 4, one subagent spawns per company in parallel.

**Optional pre-step:** Run `discoverer-6` to find companies matching your target profile and populate `portals.yml` for targeted ATS scanning in Phase 1.

Each run writes to a timestamped directory under `research/runs/`. The most recent run is symlinked at `research/latest/`.

## Architecture

```mermaid
graph TB
    subgraph Pipeline["Claude Agent Pipeline"]
        Lead[lead-0<br/>Orchestrator]
        Scout[scout-1<br/>Scrape]
        Ranker[ranker-7<br/>Rank]
        Recon[recon-3<br/>Contacts]
        Composer[composer-4<br/>Pitch]
    end

    subgraph Scraper["board-aggregator CLI"]
        CLI[Click CLI]
        Scrapers["10 scrapers"]
    end

    Lead -->|foreground| Scout
    Lead -->|foreground| Ranker
    Lead -->|"background ×N companies"| Recon
    Lead -->|"background ×N companies"| Composer
    Scout --> CLI
    CLI --> Scrapers
```

## Adding a scraper

1. Create `board_aggregator/scrapers/your_board.py`
2. Subclass `BaseScraper` and implement `scrape()`
3. Decorate with `@register`
4. Import in `board_aggregator/cli.py`
5. Add a test with a fixture in `tests/`

See `board_aggregator/scrapers/remoteok.py` for a minimal example.

## Development

```bash
git clone https://github.com/0xQuinto/agent-job-research.git
cd agent-job-research
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## License

MIT — see [LICENSE](LICENSE).
