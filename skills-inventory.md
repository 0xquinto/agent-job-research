# Diego Gomez -- Skills Inventory

Agentic engineer. I design multi-agent systems and pilot AI agents to produce expert-level work across domains I don't personally specialize in. The projects below are the evidence.

---

## Core Competency: Agentic Engineering

| Skill | Evidence |
|-------|---------|
| Multi-agent system design | limit-break-amm: 9 concurrent agents, 5-phase pipeline, team-lead orchestration pattern, 14K+ lines, 45 modules |
| Agent piloting & iteration | All projects below were built by directing AI agents through complex technical domains |
| Compliance & quality scoring | limit-break-amm: designed 5-dimension scoring framework (0-120 scale, letter grades, trend analysis, regression detection) — improved scores from 13.9 to 112.5 (A) |
| Experiment management | autoresearch-trading + limit-break-amm: structured hypothesis-to-conclusion loops with experiment logs, results ledgers, and formal reports |
| Knowledge system design | limit-break-amm: persistent inventory of 55+ documented patterns, 16 procedural lessons, auto-updated after every run |
| Context engineering | Prompt design, agent tool selection, context window management across all projects |

## Project Evidence

### 1. Inference Engineering Portfolio
**What:** 7 projects covering model compression to SLO-aware serving. 271 tests.
**Domain:** LLM inference optimization
**Key results:**
- Quantization: INT4/FP8 via llmcompressor + MLX
- Prefix caching: 2.3x TTFT speedup
- Speculative decoding: N-gram +14%, MTP +6% on L40S
- Structured output: 100% validity across all backends
- SLO scheduling: 100% goodput vs 70% FCFS at QPS=20
- Cost optimization: edge cascade at $0/M tokens
**Tech:** Python, vLLM, SGLang, Ollama, RunPod (L40S/H200), CUDA, MLX, Docker

### 2. Anthropic Performance Take-Home
**What:** Low-level CPU cycle optimization challenge from Anthropic's recruiting pipeline.
**Domain:** Systems performance engineering
**Key context:** Anthropic's original 4-hour take-home, now public after Claude Opus 4.5 surpassed most human performance. Benchmarks measured in simulated clock cycles.
**Tech:** Python, low-level optimization

### 3. Autoresearch Trading
**What:** Autonomous AI research system for crypto trading — forms hypotheses, runs experiments, tracks KPIs, iterates.
**Domain:** Quantitative finance / crypto
**Key results:**
- 40GB daily data pipeline across 25 crypto assets, zero manual intervention
- Automated collection via Fly.io + Cloudflare R2 + GitHub Actions
- ML direction classifier with triple barrier labeling
- Optuna Bayesian hyperparameter search
- Structured experiment logs with formal reports
**Tech:** Python, DuckDB, Parquet, PyTorch, Fly.io, Cloudflare R2, GitHub Actions CI/CD

### 4. RSS MCP Server
**What:** Published MCP server that gives AI assistants RSS feed management — subscribe, fetch, search, digest.
**Domain:** AI tooling / developer tools
**Key results:**
- Published npm package (@0xquinto/rss-mcp)
- Available as Claude Code plugin
- 11 tools: feed management, FTS5 full-text search, daily digests, HackerNews popularity ranking
- Conditional HTTP requests (ETag/Last-Modified), per-feed rate limiting
**Tech:** TypeScript, SQLite (FTS5), MCP protocol, Bun, npm

### 5. Limit Break AMM Security Audit
**What:** Multi-agent smart contract security audit of Limit Break's AMM system (bug bounty).
**Domain:** Smart contract security / DeFi
**Key results:**
- 9 concurrent AI agents orchestrated through 5-phase audit pipeline
- Quality scores improved from 39.8 (F) to 112.5 (A) over 17 tracked experiments
- Automated static analysis (Slither, Aderyn), hypothesis generation, parallel execution, synthesis, compliance scoring
- A/B testing of agent strategies (pass1_mode variants)
**Tech:** Python, Foundry (forge), Slither, Solidity (reading/auditing), Claude SDK

---

## Crypto & Web3 Experience

| Detail | Evidence |
|--------|---------|
| 10 years in crypto markets | Active participant and investor since 2016 |
| Operations & Content Lead at ParagonsDAO | 2023-2025: managed cross-functional team, 10+ vendor/KOL relationships, 50+ esports tournaments, 500 user onboarding pipeline |
| Live esports production | Casted Parallel TCG World Championship (Las Vegas 2025), 50+ tournaments |
| Web3 community operations | Discord, X, YouTube, Twitch channel management; content SOPs; partner onboarding |
| DeFi security | limit-break-amm audit (AMM, PermitC, EIP-712) |
| Crypto data engineering | autoresearch-trading (25 assets, 40GB daily pipeline) |

---

## Programming Languages

| Language | Level | How I use it |
|----------|-------|-------------|
| Python | Primary | All projects — agent orchestration, data pipelines, inference, CLI tools |
| TypeScript | Secondary | MCP servers (rss-mcp), tooling |
| Solidity | Reading | Security audits — read and analyze contracts, not write production code |

## Operations & Process Management

| Skill | Evidence |
|-------|---------|
| Team management | ParagonsDAO: content creator + video editor, priorities, deliverables |
| Vendor coordination | ParagonsDAO: 10+ vendors, KOLs, partners |
| SOP creation | ParagonsDAO: content production, event logistics, partner onboarding |
| Event production | 50+ tournaments, World Championship logistics |
| Pipeline management | 500 users onboarded through structured program |

## Education & Certifications

| Credential | Institution | Year |
|-----------|------------|------|
| MBA (International) | EAE Business School, Barcelona | 2017 |
| B.S. Industrial Engineering | USMA, Panama | 2014 |
| Claude in Amazon Bedrock | Anthropic | Mar 2026 |
| Claude with Google Cloud's Vertex AI | Anthropic | Mar 2026 |
| Additional Anthropic certifications | Anthropic (via LinkedIn) | 2026 |

## Languages

| Language | Level |
|----------|-------|
| Spanish | Native |
| English | Bilingual / Full professional |

## Tools & Platforms

| Category | Tools |
|----------|-------|
| AI/LLM | Claude, Claude SDK, MCP protocol, GPT, Gemini |
| Inference | vLLM, SGLang, Ollama, llmcompressor, MLX |
| Data | DuckDB, Parquet, pandas, NumPy |
| Security | Foundry (forge), Slither, Aderyn |
| Cloud | Fly.io, Cloudflare R2, RunPod, GitHub Actions |
| Dev | Docker, Git, uv, Bun, npm |
