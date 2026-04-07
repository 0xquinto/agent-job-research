# agent-job-research

Agent pipeline that scrapes 10+ job boards, scores postings against your skills, finds hiring managers, and drafts personalized pitches. Anti-mass-apply.

## Two ways to use this

### Just the scraper

Install the multi-board job scraper CLI:

```bash
pip install board-aggregator
```

```bash
board-aggregator -q "AI engineer" -q "ML ops" -o ./results
```

This scrapes Indeed, LinkedIn, Himalayas, We Work Remotely, HN Who's Hiring, CryptoJobsList, crypto.jobs, web3.career, CryptocurrencyJobs, RemoteOK, and Reddit — deduplicates results, and writes CSV + Markdown output.

To also scan specific companies via their ATS (Greenhouse, Ashby, Lever), pass a `portals.yml`:

```bash
board-aggregator -q "AI engineer" -o ./results --portals portals.yml
```

### Full pipeline

Clone the repo and run the guided setup:

```bash
git clone https://github.com/0xQuinto/agent-job-research.git
cd agent-job-research
python setup_wizard.py
```

The wizard walks you through:
- Python venv + dependency installation
- Creating your skills inventory and resume from templates
- Configuring API keys (Exa for contact research)
- Validating the installation

Then run the pipeline:

```bash
claude --agent lead-0
```

**Requires:** Python 3.12+, [Claude Code](https://claude.ai/download), git

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
