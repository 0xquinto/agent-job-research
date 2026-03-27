# Research Agent — Implementation Plan

## Philosophy

Combines Kache's data-driven approach (scrape job postings, analyze salaries, correlate to skills) with Nader Dabit's personalized outreach (tailored pitch video + DM to the right person). The anti-thesis of "Claude Cowork can apply to 50 jobs in 30 minutes."

**Core principle:** Scan the market broadly, filter ruthlessly by pay + fit, then reach out authentically to the best matches.

---

## Architecture: 4-Phase Pipeline

Based on [Anthropic's multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) and [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents).

```
                    ┌─────────────────────────────────────────────────────┐
                    │          RESEARCH LEAD (main thread via --agent)    │
                    │  Orchestrates all 4 phases sequentially            │
                    │  Spawns ALL subagents directly (no nesting)        │
                    └──┬──────────┬───────────┬──────────────┬──────────┘
                       │          │           │              │
                PHASE 1│   PHASE 2│    PHASE 3│       PHASE 4│
                       │          │           │              │
                       ▼          ▼           ▼              ▼
                ┌────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
                │  scout-1   │ │ranker-7  │ │ recon-3  │ │composer-4│
                │ (fg)       │ │(fg)      │ │ finder   │ │generator │
                │            │ │          │ │ ×N (bg)  │ │ ×N (bg)  │
                └────────────┘ └─────────┘ └──────────┘ └──────────┘
                  JobSpy MCP     Read +      Exa people    Read +
                  + Chrome       reasoning   + Chrome      Write

                fg = foreground (blocking, can prompt for permissions)
                bg = background (parallel, permissions pre-approved)
```

**Key constraint:** Subagents cannot spawn other subagents. The lead agent (running as main thread via `--agent`) directly spawns every worker. Phases 1-2 run sequentially in foreground. Phases 3-4 fan out N parallel background workers per top company.

---

## Phase 1: Scrape Job Postings

**Goal:** Cast a wide net across top job boards to collect postings + expected salaries.

### Primary Tool: JobSpy MCP Server

[JobSpy](https://github.com/speedyapply/JobSpy) is a purpose-built job scraping library that aggregates postings from multiple boards concurrently. A [MCP server](https://github.com/chinpeerapat/jobspy-mcp-server) exposes it to Claude Code.

**Why JobSpy over Exa for scraping:**
- Exa is a semantic search engine, not a scraper — can't paginate job boards, can't get behind login walls
- JobSpy extracts structured data natively (title, salary min/max, company, remote status)
- Indeed has **no rate limiting**; up to 1,000 results per search
- Free and open source — no credit costs

**Setup:** `uv pip install --system --break-system-packages python-jobspy` (no MCP server needed — called via Bash)

### Subagent: `scout-1`
**Tools:** Bash (calls `python3 -c "from jobspy import scrape_jobs; ..."`), Claude in Chrome (supplement), WebSearch (fallback)
**Model:** Sonnet (fast, high-volume)

**JobSpy scrapes these boards concurrently:**
- Indeed (best — no rate limiting, richest data)
- LinkedIn (rate limits around page 10 — supplement with Chrome)
- Glassdoor (includes company reviews + salaries)
- Google Jobs (aggregates from multiple sources)
- ZipRecruiter

**Supplemental sources via Chrome:**
- Wellfound (AngelList) — for startups
- RemoteOK / We Work Remotely — for remote-first roles
- Company career pages (for companies Diego is already interested in)

**Search queries** (tuned to Diego's profile):
- "Operations Manager AI" / "AI Operations Lead"
- "Business Operations AI Integration"
- "AI Process Automation Manager"
- "Technical Operations Manager"
- "AI Agent Developer" / "AI Engineer Operations"
- "Head of Operations" at AI/tech companies
- "Developer Relations" / "DevRel" (leveraging content + technical skills)

**JobSpy parameters per query:**
```python
scrape_jobs(
    site_name=["indeed", "linkedin", "glassdoor", "google", "zip_recruiter"],
    search_term="Operations Manager AI",
    location="Remote",
    results_wanted=50,
    hours_old=720,        # last 30 days
    is_remote=True,
    linkedin_fetch_description=True,
    country_indeed="USA"
)
```

**Output per posting (structured by JobSpy):**
```markdown
- Title
- Company (+ company_url, employees_count, revenue)
- Location / Remote status (is_remote)
- Salary range (min_amount, max_amount, currency, interval)
- URL (job_url)
- Full description
- Date posted
- Job type (fulltime, contract, etc.)
```

**Writes to:** `research/phase-1-scrape/all-postings.md` — single deduplicated master (agents `mkdir -p` at runtime)

**Estimated volume:** ~7 search queries × 50 results × 5 boards = up to 1,750 raw postings (deduplicated down to ~200-500 unique)

---

## Phase 2: Filter & Rank

**Goal:** Score each posting against `skills-inventory.md` and rank by salary × fit.

### Subagent: `ranker-7`
**Tools:** Read, Write, Grep, Glob
**Model:** Sonnet (scoring is pattern matching against skills checklist, not deep reasoning)

**Scoring dimensions:**
| Dimension | Weight | How |
|-----------|--------|-----|
| Salary | 30% | Normalized against market range |
| Skills match | 30% | % of required skills Diego has (from skills-inventory.md) |
| Experience match | 20% | Years/type alignment with Diego's background |
| Growth potential | 10% | Role trajectory, learning opportunities |
| Remote/location fit | 10% | Panama-compatible, timezone overlap |

**Fit grades:**
- **A (80-100):** Strong match — most requirements met, good salary
- **B (60-79):** Solid match — some gaps but addressable
- **C (40-59):** Stretch — significant gaps, lower priority
- **D (0-39):** Skip — poor fit

**Output:** `research/phase-2-rank/ranked-opportunities.md` — sorted by score descending

```markdown
# Ranked Opportunities

## A-Tier
### 1. [Role] at [Company] — Score: 92 | Salary: $X-Y
- Match: skills X, Y, Z align perfectly
- Gap: missing skill W (addressable — similar experience with V)
- Why pursue: [reason]

## B-Tier
...
```

**Top N filter:** Only the top opportunities (A-tier + top B-tier) advance to Phase 3.

---

## Phase 3: Find Contact Personnel

**Goal:** For each top opportunity, identify the right person to DM — hiring manager, team lead, or recruiter.

### Subagent: `recon-3`
**Tools:** Exa people search, Claude in Chrome (LinkedIn + X), WebSearch
**Model:** Sonnet

**Runs in parallel** — one worker per top opportunity.

**Search strategy per opportunity:**
1. **LinkedIn (Exa people search):** Search for "[Company] + [Department] + Manager/Lead/Director"
2. **LinkedIn (Chrome):** Browse company page → People → filter by department
3. **X (Chrome):** Search "[Company] hiring" or company account followers in relevant roles
4. **Company website:** Team/About page for leadership

**Output per contact:**
```markdown
- Name
- Title
- LinkedIn URL
- X handle (if found)
- Recent activity (last 3 posts/shares — for conversation starters)
- Shared connections or interests with Diego
- Recommended outreach channel (LinkedIn DM, X DM, email)
```

**Writes to:** `research/phase-3-contacts/[company-slug]/`

---

## Phase 4: Create Pitch Documents

**Goal:** For each top opportunity, generate a tailored video pitch script + DM draft following Nader's advice.

### Subagent: `composer-4`
**Tools:** Read, Write
**Model:** Opus (needs Diego's authentic voice)

**Inputs:**
- The opportunity details from Phase 2
- Contact info from Phase 3
- `resume-diego-gomez-ops-ai.md` — for positioning
- `skills-inventory.md` — for specific evidence
- `vocaroo-script.md` — for voice/tone reference

**Output per opportunity:**

### Video Script (30-40 seconds)
```markdown
# Video Pitch: [Role] at [Company]

## Opening (5 sec)
"Hey [Contact first name], I'm Diego — [one-line hook referencing their company]"

## Value Prop (15-20 sec)
- Reference specific company need from job posting
- Map to Diego's concrete experience (name the project, the numbers)
- Show you understand their problem

## Close (10 sec)
"I'd love to chat about how I can help [specific thing].
My resume's linked below — happy to jump on a quick call."
```

### DM Draft
```markdown
# DM to [Contact Name] — [Platform]

Hey [Name],

[1 sentence referencing their recent post/company news — shows you did homework]

I saw the [Role] opening and it lines up with what I've been building —
[1 specific example mapped to their need].

I recorded a quick intro: [video link]
Resume: [link]

Would love to connect if you're open to it.

— Diego
```

**Writes to:** `research/phase-4-pitch/[company-slug]/`

---

## Tools Integration

### Phase 1: python-jobspy via Bash (Primary Scraper)
- Called via `Bash`: `python3 -c "from jobspy import scrape_jobs; ..."`
- Scrapes Indeed, LinkedIn, Glassdoor, Google, ZipRecruiter concurrently
- Returns structured pandas DataFrame: title, company, salary (min/max), location, remote, description
- **Free, open source, runs locally** — no API credits, no MCP server needed
- Setup: `uv pip install --system --break-system-packages python-jobspy`
- [JobSpy GitHub](https://github.com/speedyapply/JobSpy)

### Phase 3: Exa MCP (Contact Research)
- `people_search_exa` — find hiring managers, team leads, recruiters (specialized people index)
- `company_research_exa` — company details (funding, size, leadership)
- `web_search_exa` — supplemental research on contacts, company news
- `crawling_exa` — extract content from specific LinkedIn/company URLs
- **Reserve Exa credits for Phase 3** where its specialized indexes shine (~50-100 credits)

### Phases 1+3: Claude in Chrome (Supplement)
- **Phase 1:** Scrape Wellfound, RemoteOK, and company career pages (boards JobSpy doesn't cover)
- **Phase 3:** Browse LinkedIn profiles, X profiles for contact finding
- **Phase 3:** Extract recent posts/activity for conversation starters
- **General:** Screenshot key pages for reference

### Fallback: WebSearch + WebFetch
- When Exa rate limits hit (free tier = 1,000 credits)
- General web research and URL extraction
- Supplemental salary data from Levels.fyi, Payscale

---

## File Structure

Phase-based directories with clear data handoff between stages. Markdown `key: value` format chosen for human readability and natural Claude output — [format does not significantly affect accuracy on frontier models (p=0.484, 9,649 experiments)](https://arxiv.org/abs/2602.05447). 3-4 levels max depth.

```
hireboost-ops-ai-manager/
│
├── .claude/
│   ├── CLAUDE.md                          # Project rules: pipeline flow, conventions, forbidden patterns
│   ├── settings.local.json                # Permissions config (pre-approved for background agents)
│   └── agents/                            # Project-scoped subagents (non-descriptive names)
│       ├── lead-0.md                      # Orchestrator (spawns all workers)
│       ├── scout-1.md                     # Phase 1: fg, sonnet, JobSpy MCP + Chrome
│       ├── ranker-7.md                    # Phase 2: fg, sonnet, Read only
│       ├── recon-3.md                     # Phase 3: bg ×N, sonnet, Exa + Chrome
│       └── composer-4.md                  # Phase 4: bg ×N, opus, Read + Write
│
├── research/                              # Created at runtime by agents (not pre-created)
│   ├── phase-1-scrape/
│   │   └── all-postings.md                # Deduplicated master list (markdown key:value)
│   │
│   ├── phase-2-rank/
│   │   └── ranked-opportunities.md        # Scored + tiered (A/B/C/D sections)
│   │
│   ├── phase-3-contacts/
│   │   └── [company-slug]/
│   │       ├── contacts.md                # Personnel: name, title, LinkedIn, X, activity
│   │       └── company-context.md         # News, culture, team, tech stack, funding
│   │
│   ├── phase-4-pitch/
│   │   └── [company-slug]/
│   │       ├── video-script.md            # 30-40 sec tailored pitch
│   │       ├── dm-draft.md                # Personalized outreach message
│   │       └── status.md                  # Outreach tracking (drafted/sent/replied/scheduled)
│   │
│   └── pipeline-summary.md               # Final overview from lead agent
│
├── resume-diego-gomez-ops-ai.md           # Input to Phase 2 + 4
├── skills-inventory.md                    # Input to Phase 2
├── vocaroo-script.md                      # Tone reference for Phase 4
├── form-answers.md                        # Pre-filled form answers
├── linkedin-updates.md                    # LinkedIn profile updates
├── x-profile-updates.md                  # X profile updates
├── github-updates.md                      # GitHub profile updates
├── research-agent-plan.md                 # This plan
└── README.md                              # Project overview + checklist
```

### Data Format Decisions

| Phase | Format | Why |
|-------|--------|-----|
| Phase 1 | Single markdown key:value file | Human-readable; Claude writes it naturally; format-independent accuracy on frontier models ([McMillan 2026](https://arxiv.org/abs/2602.05447)) |
| Phase 2 | Markdown with score metadata | Diego reviews this directly — readability is the bottleneck, not format accuracy |
| Phase 3 | Markdown per company | Contact profiles + company context co-located; human review before outreach |
| Phase 4 | Markdown per company | Prose content (scripts, DMs) — markdown is the natural choice |

### Data Handoff Between Phases

Each phase reads the previous phase's output directory:
1. **Phase 1 → Phase 2:** `ranker-7` reads `research/phase-1-scrape/all-postings.md`
2. **Phase 2 → Phase 3:** `recon-3` reads `research/phase-2-rank/ranked-opportunities.md` (A+B tier only)
3. **Phase 3 → Phase 4:** `composer-4` reads `research/phase-3-contacts/[company]/` + Phase 2 data
4. **Lead agent** writes `research/pipeline-summary.md` linking all outputs

---

## Execution Flow (Single Command)

```
claude --agent lead-0
```

### What happens:

1. **Research Lead** reads `skills-inventory.md` and `resume-diego-gomez-ops-ai.md` to understand Diego's profile

2. **Phase 1** — Lead spawns `scout-1` in **foreground** (blocking)
   - Foreground because Chrome may need permission prompts for login-gated boards
   - Calls JobSpy MCP `scrape_jobs_tool` for each search query (7 queries × 5 boards)
   - Supplements with Chrome for boards JobSpy doesn't cover (Wellfound, RemoteOK)
   - **Writes results to file as it scrapes** (not accumulated in context):
     - Appends to `research/phase-1-scrape/all-postings.md` per query
     - Deduplicates in-memory after all queries complete, rewrites the master file
   - **Returns to lead:** summary only ("Found 312 unique postings across 7 boards")

3. **Phase 2** — Lead spawns `ranker-7` in **foreground** (blocking)
   - Reads `research/phase-1-scrape/all-postings.md` (the file, not the Phase 1 context)
   - Scores each posting against `skills-inventory.md`
   - Ranks by salary × fit score
   - Writes `research/phase-2-rank/ranked-opportunities.md`
   - **Returns to lead:** top N company names + scores ("5 A-tier, 3 B-tier opportunities")

4. **Phase 3** — Lead reads `ranked-opportunities.md`, then spawns N `recon-3` workers in **background** (parallel)
   - Lead directly spawns one `recon-3` per top company (subagents can't spawn subagents)
   - Each runs independently with company name + role as input
   - Each writes to `research/phase-3-contacts/[company-slug]/contacts.md` + `company-context.md`
   - **Each returns to lead:** summary only ("Found hiring manager Jane Doe, VP Engineering at Acme")
   - Lead waits for all N to complete before proceeding

5. **Phase 4** — Lead spawns N `composer-4` workers in **background** (parallel)
   - Lead directly spawns one `composer-4` per top company
   - Each reads contact data from Phase 3 + opportunity data from Phase 2
   - Each writes to `research/phase-4-pitch/[company-slug]/`
   - **Each returns to lead:** summary only ("Generated video script + DM draft for Acme")
   - Lead waits for all N to complete

6. **Lead** writes `research/pipeline-summary.md` linking all outputs with final stats

### Context window protection:
- Subagents write verbose output to **files**, return only **1-2 sentence summaries** to lead
- Phase 1 scraper appends to file as it goes (doesn't accumulate 500 postings in context)
- Phase 2 scorer reads from file, not from Phase 1's context
- Phases 3+4 background workers each have their own isolated context window
- Lead's context stays lean: profile + summaries + file paths

### What Diego does after:
- Reviews ranked opportunities, removes any that don't feel right
- Reviews/edits pitch scripts for authenticity
- Records video (screen recorder or Vocaroo)
- Sends DMs personally — the human touch

---

## Claude Code Constraints & Configuration

### Constraint: Subagents cannot spawn subagents

The lead agent (main thread via `--agent`) must directly spawn every worker. No intermediate orchestrators. This means:
- Phase 3: Lead spawns N `recon-3` instances, not one "Phase 3 coordinator"
- Phase 4: Lead spawns N `composer-4` instances, not one "Phase 4 coordinator"
- Workers are leaf nodes — they do their job and return a summary

### Constraint: Background subagents auto-deny unprompted permissions

When running in background, subagents can't prompt for permission. Fix:
- **Phases 1-2 run in foreground** (blocking) — Chrome may need interactive permission
- **Phases 3-4 run in background** (parallel) — pre-approve all needed permissions
- Pre-approve in `settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Read", "Write", "Edit", "Glob", "Grep",
      "WebSearch", "WebFetch",
      "Bash(python3 *)",
      "mcp__exa__people_search_exa",
      "mcp__exa__company_research_exa",
      "mcp__exa__web_search_exa",
      "mcp__exa__crawling_exa",
      "mcp__claude-in-chrome__*"
    ]
  }
}
```

### MCP & Tool Configuration

**JobSpy:** No MCP server — called via Bash (`python3 -c "from jobspy import scrape_jobs; ..."`). Requires `python-jobspy` pip package installed system-wide.

**Exa:** Configured globally (already available). Subagents access via `tools` field listing `mcp__exa__*` tool names.

**Chrome:** Auto-connects when extension is active. Subagents access via `tools` field listing `mcp__claude-in-chrome__*` tool names.

Only `name`, `description`, `tools`, and `model` are valid frontmatter fields for agent markdown files.

**Tool access per agent:**
- `scout-1`: Bash (python-jobspy), Chrome tools, WebSearch
- `recon-3`: Exa MCP tools, Chrome tools, WebSearch
- `ranker-7` and `composer-4`: Read/Write only (no MCP, no Bash)

### Agent Naming Convention

Non-descriptive names to prevent Claude from inferring default behaviors that override custom prompts ([source](https://codewithseb.com/blog/claude-code-sub-agents-multi-agent-systems-guide)). Descriptive names like `code-reviewer` cause Claude to apply built-in review behaviors silently.

| Agent | Name | Why non-descriptive |
|-------|------|-------------------|
| Orchestrator | `lead-0` | Avoids "orchestrator"/"coordinator" inference |
| Phase 1 Scraper | `scout-1` | Avoids "scraper"/"crawler" inference |
| Phase 2 Scorer | `ranker-7` | Avoids "scorer"/"analyzer" inference |
| Phase 3 Contact Finder | `recon-3` | Avoids "finder"/"researcher" inference |
| Phase 4 Pitch Generator | `composer-4` | Avoids "generator"/"writer" inference |

### Subagent Output Contract

All subagents MUST follow this pattern:
1. Write full verbose output to designated `research/` files
2. Return to lead agent: **1-2 sentence summary only** (count, key finding, file path)
3. Never return raw scraped data, full job descriptions, or contact profiles in the response

This protects the lead agent's context window from bloat when running many parallel workers.

---

## Design Principles

1. **Broad scan, narrow focus** — Scrape widely, but only invest deep research into top matches
2. **Data-driven decisions** — Salary × fit scoring, not gut feeling
3. **Evidence-based fit** — Score against actual `skills-inventory.md`, not vibes
4. **Human-in-the-loop** — Agent researches and drafts, Diego reviews and sends
5. **Parallel where possible** — Phase 1 scrapers run in parallel, Phase 3+4 workers run in parallel
6. **Respect boundaries** — Rate limit aware, no spam, no aggressive scraping
7. **Authentic voice** — Pitches should sound like Diego, not a bot

---

## Sources

- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Why Personalized Job Outreach Works Better Than Mass Applications – DAVRON](https://www.davron.net/personalized-job-outreach-vs-mass-applications/)
- [Agentic Workflows with Claude – Medium](https://medium.com/@reliabledataengineering/agentic-workflows-with-claude-architecture-patterns-design-principles-production-patterns-72bbe4f7e85a)
- [Exa Pricing](https://exa.ai/pricing) — Free tier 1,000 credits; Core $49/mo for 8,000
- [JobSpy — Job scraper for LinkedIn, Indeed, Glassdoor & more](https://github.com/speedyapply/JobSpy)
- [JobSpy MCP Server (FastMCP)](https://github.com/chinpeerapat/jobspy-mcp-server)
- [Exa vs Linkup — job scraping limitations](https://www.linkup.so/blog/exa-vs-linkup)
- [Why scraping beats search APIs for data](https://scrapegraphai.com/blog/why-scraping-is-more-important-than-search)
- [McMillan 2026: Structured Context Engineering (arXiv:2602.05447)](https://arxiv.org/abs/2602.05447) — 9,649 experiments: format does not significantly affect accuracy on frontier models (p=0.484); model capability is the dominant factor
- [Schmidt et al. 2025: Prompt Engineering for Structured Data](https://www.eurekalert.org/news-releases/1107970) — Claude achieves 85% accuracy, excels with hierarchical formats (JSON/YAML)
- [ShShell 2026: JSON vs YAML vs Markdown Token Benchmarks](https://shshell.com/blog/token-efficiency-module-13-lesson-2-format-comparison) — YAML 30% cheaper than JSON; markdown tables 40% more expensive
- [How agent handoffs work in multi-agent systems](https://towardsdatascience.com/how-agent-handoffs-work-in-multi-agent-systems/) — structured context transfer
- [Claude Code production structure guide](https://dev.to/lizechengnet/how-to-structure-claude-code-for-production-mcp-servers-subagents-and-claudemd-2026-guide-4gjn)
- [Research project folder structure best practices](https://libguides.graduateinstitute.ch/rdm/folders) — 3-4 levels max
