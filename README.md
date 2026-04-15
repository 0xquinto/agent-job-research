# agent-job-research

Agent pipeline that scrapes 10+ job boards, scores postings against your skills, finds hiring managers, and drafts personalized pitches. Anti-mass-apply.

## Quick Start

```bash
git clone https://github.com/0xQuinto/agent-job-research.git
cd agent-job-research
claude --agent lead-0
```

That's it. On first run, `lead-0` detects missing setup and walks you through everything:
- Installing prerequisites (Python 3.12+, git, Homebrew, Node.js 20+)
- Setting up the virtual environment and dependencies
- Installing Playwright + Chromium for CV PDF rendering
- Configuring Exa MCP for contact research
- Building your skills inventory and resume from your existing materials (CV, portfolio, GitHub, LinkedIn)

**Manual alternative:** `python setup_wizard.py` handles venv + deps + Exa MCP without the profile builder.

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

**On-demand agents (outside the pipeline):**
- `applier-2` — generates copy-paste answers for application forms (human-in-the-loop)
- `letter-5` — ATS cover letter generation (keyword injection + SOAR proof points)
- `pdf-9` — tailored ATS PDF CV generation (keyword injection + bullet reordering)
- `filler-10` — hybrid ATS submitter: API-first for Lever/Ashby, browser automation for Greenhouse/Workday/others (human-in-the-loop)

**Utilities:**
- `scripts/tracker.py` — application status tracker CLI (add, update, import-run, dedup, show)
- `dashboard/` — Go TUI for browsing applications (Bubble Tea + Lipgloss)
- `scripts/generate-pdf.mjs` — Playwright-based ATS PDF renderer

## Architecture

```mermaid
graph TB
    subgraph Pipeline["Claude Agent Pipeline"]
        Lead[lead-0<br/>Orchestrator]
        Primer[primer-8<br/>Onboarding]
        Scout[scout-1<br/>Scrape]
        Ranker[ranker-7<br/>Rank]
        Recon[recon-3<br/>Contacts]
        Composer[composer-4<br/>Pitch]
        Discoverer[discoverer-6<br/>Discovery]
        Applier[applier-2<br/>Forms]
        Letter[letter-5<br/>Cover Letter]
        PDF[pdf-9<br/>ATS PDF]
        Filler[filler-10<br/>ATS Submit]
    end

    subgraph Scraper["board-aggregator CLI"]
        CLI[Click CLI]
        Scrapers["10 scrapers"]
    end

    Lead -->|"foreground (if needed)"| Primer
    Lead -->|foreground| Scout
    Lead -->|foreground| Ranker
    Lead -->|"background ×N companies"| Recon
    Lead -->|"background ×N companies"| Composer
    Lead -->|"foreground (optional)"| Discoverer
    Lead -.->|on-demand| Applier
    Lead -.->|on-demand| PDF
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
