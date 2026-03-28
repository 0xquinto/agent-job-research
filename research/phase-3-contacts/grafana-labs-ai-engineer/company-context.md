# Company Context: Grafana Labs

## Overview
Grafana Labs builds the open-source Grafana observability platform used by 20M+ users and 7,000+ organizations worldwide (including 70% of the Fortune 50). Their commercial product, Grafana Cloud, is a fully managed observability stack (metrics, logs, traces, profiles) with a growing AI layer: Grafana Assistant (GA as of Oct 2025), Sift (ML-powered incident diagnostics), and Assistant Investigations (public preview). They are a 100% remote company with 1,400+ employees across 40+ countries, operating at $400M+ ARR.

## Recent News (Last 3 Months)
- **Mar 2026:** Grafana Labs 4th Annual Observability Survey released — findings highlight AI, economics, complexity, and open source at an industry crossroads.
- **Mar 2026:** GrafanaCON 2026 agenda announced (Seattle). Active conference season signals hiring and team expansion.
- **Feb 2026:** Reported in talks to raise at a $9 billion valuation, up from $6.6B — led by Singapore's GIC sovereign wealth fund. Series E ~$250M.
- **Feb 2026:** Company published "Caps a Breakout Year" press release: $400M+ ARR, 7,000+ customers, 100+ new employees in 2025, new Japan subsidiary.
- **Oct 2025:** Grafana Assistant reached GA; Assistant Investigations launched in public preview at ObservabilityCON 2025 (London). Named Leader in 2025 Gartner Magic Quadrant for Observability Platforms (#13 Forbes Cloud 100 for 5th consecutive year).
- **Aug 2025:** Grafana Assistant public preview launched (before GA in Oct).

## Culture Signals
- **Remote-first, async-friendly:** 1,400+ people in 40+ countries; no headquarters.
- **Open source identity:** Heavy OSS roots (Prometheus, Loki, Cortex, Tempo). Engineers expected to be active in the open source community.
- **Maker/builder culture:** Tom Wilkie (CTO) has posted about 3D printers and maker side projects; informal, technically-driven leadership.
- **Engineering blog is substantive:** Engineers and managers publish deeply technical blog posts regularly — a signal that writing and public communication are valued.
- **"Anti-toil" philosophy:** The Grafana Ops/IRM AI team's stated mission is to reduce toil for SREs — reflected in product, hiring, and how they talk publicly.
- **Calm growth:** Not a hypergrowth-at-all-costs company — methodical product expansion, multi-year open source strategy before monetization.

## Tech Stack (from job postings and engineering blog)
- **Languages:** Go (primary backend), TypeScript/React (frontend)
- **Data/ML:** Python for ML pipeline components, Prometheus, Loki, Tempo, Pyroscope (internal stack)
- **AI/ML infrastructure:** LLM integration (Grafana Assistant uses LLM backends), vector search, anomaly detection, forecasting
- **Observability/infra:** Kubernetes, OpenTelemetry, Grafana Cloud (own stack), AWS/GCP (BYOC support)
- **Databases:** Various (Grafana supports 150+ data sources)
- **AI-specific:** LLM APIs, ML-powered alerting, Sift uses supervised/unsupervised ML for incident pattern detection

## Team Size & Growth
- **Company:** ~1,400 employees (100+ added in 2025 alone); 40+ countries
- **Engineering org:** Multiple VP-level engineering leaders (Manoj Acharya, Dee Kitchen, plus Directors); team structured by product area
- **Grafana Ops AI/ML team:** Appears to be a focused squad within the IRM/Observability product area; multiple concurrent open roles (Senior AI Engineer + Staff AI Engineer both listed) signals active team expansion
- **Hiring velocity:** Active on LinkedIn with 54 US jobs listed as of March 2026; multiple technical recruiters (Amy Wang Morales, Lauren Godfrey, Emily Hartmann, Ryan McKellips); Senior Technical Recruiter for R&D also being hired — strong signal of continued engineering growth
- **Funding trajectory:** $6.6B → $9B valuation raise in progress; $400M ARR puts them firmly in pre-IPO territory

## AI Strategy Context
Grafana Labs is betting on AI as the next layer of the observability platform — not a standalone product but embedded throughout the stack. Their Grafana Assistant (GA Oct 2025) allows natural language queries in PromQL/LogQL/TraceQL. Sift automates incident investigation. Assistant Investigations uses a multi-agent architecture to find root cause. Tom Wilkie's public statements consistently frame this as "AI that's grounded in context, not magic" — a technically rigorous approach rather than hype-driven.

The "Grafana Ops, AI/ML" team specifically builds the AIOps layer for incident detection, response, and resolution. This is distinct from the core ML platform team (Ben Sully's team) and more focused on applied AI for the IRM workflow.
