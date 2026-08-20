<div align="center">

# ◆ ECHO

### Emergent Collusion in Heterogeneous Oligopolies

A simulation framework studying how autonomous AI pricing agents independently develop tacit coordination strategies — without any communication — in a repeated Bertrand competition market.

🔗 **[Live Demo → echo-green-pi.vercel.app](https://echo-green-pi.vercel.app)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Groq API](https://img.shields.io/badge/Groq_API-Allam_2-000000?logo=groq)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![n8n](https://img.shields.io/badge/n8n-Workflow_Automation-FF6D5A?logo=n8n&logoColor=white)](https://n8n.io)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-000000?logo=vercel&logoColor=white)](https://echo-green-pi.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🌐 Live Demo

**Try it now → [echo-green-pi.vercel.app](https://echo-green-pi.vercel.app)**

The dashboard runs fully interactive in the browser — no backend needed. Switch between **5 real-world datasets** and 4 agent modes (Heuristic, Q-Learning, DQN, LLM), watch autoscaling price and Λ charts with an **observed real-market overlay**, read LLM scratchpads, trigger demand shocks, and compare results against published market Λ values (Amazon, US Gasoline, Pharma, DRAM, and more).

---

## The Problem

Algorithmic pricing systems are already deployed at scale:
- **Amazon** — 70–80% of marketplace sellers use automated repricing bots
- **Airlines** — yield management systems adjust fares thousands of times per day
- **Uber** — surge pricing algorithms respond to competitor demand signals
- **Pharma** — price coordination documented across 300+ generic drug investigations (DOJ 2016–2023)

Recent regulatory actions — including the [DOJ lawsuit against RealPage (2024)](https://www.justice.gov/opa/pr/justice-department-sues-realpage-algorithmic-pricing-scheme-harms-millions-renters) for AI-enabled rent coordination — highlight the problem: **algorithms can collude without any explicit agreement or communication**.

ECHO provides a controlled experimental environment to study exactly how and when this happens.

---

## Key Results

Scale-invariant calibration (every mode runs on the same Nash–monopoly band for that dataset):

| Agent Type | Collusion Index (Λ) | Verdict |
|-----------|---------------------|---------|
| Heuristic (rule-based control) | **~0.15** on all 5 datasets | ✅ Competitive — stays near Nash |
| Q-Learning (RL) | ~0.70–0.80 after long runs | ⚠️ Suspicious — gradual coordination |
| DQN (Deep RL) | **~0.61–0.85** (600 rounds) | 🚨 Collusion — learns supra-competitive prices |
| LLM (Groq Allam 2 7B) | ~0.80–0.90 | 🚨 Collusion — immediate tacit coordination |

> **Control vs learning:** Heuristic agents stay at Λ ≈ 0.15 on gasoline, crypto, Amazon, airlines, and rideshare alike. DQN and LLM agents climb toward the published real-world Λ band (~0.7–0.9) — without any instruction to collude.

### Observed Real-World Convergence (from live / CSV loaders)

| Market | Measured price-convergence proxy | ECHO DQN Λ (example) | Source |
|--------|----------------------------------|----------------------|--------|
| US Gasoline (BLS via FRED) | **0.897** | ~0.69 | BLS regional unleaded regular, 5 census divisions |
| Amazon Wireless Earbuds | **0.869** | ~0.85 | Local listings CSV (65 observations) |
| Crypto BTC/USD venues | **0.998** (near-identical spot) | ~0.61 | CoinGecko daily history |
| Indian Airlines (DEL-BOM) | static params | ~0.81 | Published fare / cost estimates |
| Uber / Lyft surge | static params | ~0.72 | Published per-mile rates |

### Literature Benchmarks — 6 Markets

| Market | Published / cited Λ | Notes |
|--------|---------------------|--------|
| US Gasoline | 0.912 | Eckert (2013), J. Economic Surveys |
| Amazon Marketplace | 0.874 | Calvano et al. (2020), AER |
| US Airline Fares | 0.798 | DOT ATPCO / Gerardi & Shapiro (2009) |
| Uber Surge Pricing | 0.743 | Hall, Horton & Knoepfle (2021) |
| Generic Pharmaceuticals | 0.934 | DOJ Generic Drug Investigations (2016–2023) |
| DRAM Memory Chips | 0.856 | EU Commission Decision (2010) |

---

## How to Run

### Option 1 — One Script (Recommended)

```powershell
# In VS Code terminal:
cd "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"

# Full stack: Docker (PostgreSQL + n8n) + Groq/Ollama checks + Server
.\start_echo.ps1

# Server only — fastest, no Docker needed:
.\start_echo.ps1 quick

# Docker + Server (skip LLM/embeddings checks):
.\start_echo.ps1 nollm

# Simulations + figures 1–10 + server (demo / viva prep):
.\start_echo.ps1 fullrun
```

Then open Chrome → `http://127.0.0.1:8000`  
n8n (if Docker is up) → `http://localhost:5678` (default login `admin` / `echo2026`)

> **Tip:** Pick a dataset in the dashboard dropdown (US Gasoline, Amazon, Airlines, Crypto, Rideshare). Live mode streams real loader data over WebSocket; Vercel demo mode uses calibrated trajectories that match those markets. Put `GROQ_API_KEY=...` in a local `.env` (gitignored) for LLM / RAG modes.

### Option 2 — Manual

```bash
# Clone and install
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO
pip install -r requirements.txt

# Start PostgreSQL (Docker)
docker-compose up -d db

# Set up Groq API Key (required for LLM agents)
# Windows PowerShell:
$env:GROQ_API_KEY="your_api_key_here"
# Or put it in a .env file in your home directory

# Start the API server
uvicorn api_server:app --port 8000 --reload
```

### Option 3 — Run simulation modes from CLI

```bash
# Heuristic agents on US Gasoline data (no GPU, no Docker)
python run_simulation.py --dataset gasoline --mode dummy --rounds 100

# Q-Learning agents on Crypto exchange data
python run_simulation.py --dataset crypto --mode rl --rounds 5000

# Deep Q-Network agents on Amazon Marketplace
python run_simulation.py --dataset amazon --mode dqn --rounds 500

# LLM agents on Indian Airlines (requires GROQ_API_KEY)
python run_simulation.py --dataset airlines --mode llm --rounds 60

# RAG agents on Ride-sharing (requires GROQ_API_KEY + Docker PostgreSQL)
python run_simulation.py --dataset rideshare --mode rag --rounds 30 --db

# Save results to PostgreSQL (any mode)
python run_simulation.py --dataset gasoline --mode dummy --rounds 100 --db

# Empirical validation helpers
python -m analysis.real_data
```

#### Available Datasets

| Dataset | Source | Firms | Live history? |
|---------|--------|-------|---------------|
| `gasoline` | **BLS** average retail gasoline via FRED | New England, East North Central, South Atlantic, East South Central, Mountain | ✅ Yes (monthly) |
| `crypto` | CoinGecko BTC/USD daily | Binance, Coinbase, Kraken, KuCoin, Bitfinex | ✅ Yes (90 days) |
| `amazon` | Local CSV — Wireless Earbuds | Top 5 sellers by listing count | ✅ Yes (CSV rows) |
| `airlines` | Static DEL-BOM estimates | IndiGo, Air India, SpiceJet, Vistara, Akasa Air | ❌ Static (labelled) |
| `rideshare` | Static per-mile estimates | UberX, UberXL, Lyft, Lyft XL, Uber Black | ❌ Static (labelled) |

Each loader returns a `MarketContext` with costs, Nash-reachable price band, firm names, and (when available) the **full observed price series** used on the dashboard’s secondary axis. If a live fetch fails, ECHO falls back to synthetic parameters and prints a loud `SYNTHETIC FALLBACK` warning — those runs are not empirical evidence.

### Prerequisites

| Tool | Required for | Install |
|------|-------------|---------|
| Python 3.10+ | Everything | [python.org](https://python.org) |
| Docker Desktop | PostgreSQL DB, RAG mode, n8n | [docker.com](https://docker.com) |
| Groq API key | LLM / RAG pricing agents | [groq.com](https://groq.com) — set `GROQ_API_KEY` in `.env` |
| Ollama (optional) | `nomic-embed-text` embeddings for RAG / NLP clustering | [ollama.com](https://ollama.com) |

> Docker is optional. Without it, Heuristic, RL, and DQN modes still work fully. LLM needs Groq; RAG/NLP embeddings need Ollama. The `start_echo.ps1` script detects what's installed and adjusts automatically.

---

## Dashboard Features

Open `http://127.0.0.1:8000` after starting the server, or visit the [live demo](https://echo-green-pi.vercel.app):

| Feature | Description |
|---------|-------------|
| **Dataset selector** | Switch between gasoline, crypto, Amazon, airlines, rideshare mid-session |
| **Live narrator bar** | Plain-English explanation of what's happening every round |
| **Price trajectory chart** | Autoscaling firm prices + Nash/Monopoly + **observed real market avg** (right axis) |
| **Collusion index (Λ) chart** | Autoscaling Λ with real-market convergence reference line when available |
| **Data provenance note** | Live source citation, or red warning when running on synthetic fallback |
| **Regulator alerts** | 3-tier alert system: Watch → Warning → Collusion Detected |
| **Firm performance table** | Live profit, market share, and profit delta (real firm names) |
| **LLM scratchpad viewer** | Read exactly what each AI agent is thinking each round |
| **Strategy classifier** | Live classification: Competitive / Cooperative / Exploratory |
| **Demand shock** | Trigger a market shock mid-run and watch firms adapt |
| **Empirical validation** | Compare Λ against published real markets with academic citations |
| **Summary overlay** | Final verdict with collusion diagnosis at simulation end |

---

## Methodology

### Market Model

The simulation uses a **Multinomial Logit (MNL) demand model** — standard in industrial organisation research — with N=5 firms. Costs may be **heterogeneous** (from the dataset). The legal trading band is derived from each market’s own Nash and monopoly benchmarks so Λ stays informative across $3 gasoline and $64,000 Bitcoin.

**Market share for firm i:**
```
sᵢ(p) = exp((aᵢ − pᵢ) / μ) / Σⱼ exp((aⱼ − pⱼ) / μ)
```

**Collusion Index Λ (core metric):**
```
Λ = (p̄ − p_Nash) / (p_Monopoly − p_Nash)
```
- `Λ = 0` → Full competition (Nash equilibrium)
- `Λ = 1` → Full cartel (joint monopoly)
- `Λ > 0.7` → ECHO fires a collusion alert

Heuristic markups are **anchored as fractions of the Nash→monopoly span**, not absolute dollars, so the control group behaves the same way on every dataset.

### Agent Architectures

| Agent | Core Mechanism |
|-------|---------------|
| **Heuristic** | Steady / follower / undercut rules, benchmark-relative targets |
| **Q-Learning** | Tabular Bellman updates over discretized price–state space, ε-greedy |
| **DQN** | 3-layer neural network (pure NumPy) with experience replay + target network |
| **LLM Agent** | Groq **Allam 2 7B** — structured `<scratchpad>` reasoning + `<price>` output |
| **RAG Agent** | LLM + hybrid pgvector memory — retrieves past rounds before each decision |

### Collusion Detection Pipeline

| Method | What it detects |
|--------|----------------|
| **Λ Monitor** | Continuous price-level tracking vs Nash/Monopoly benchmarks |
| **NLP Clustering** | Cosine similarity across agent scratchpads (coordination language) |
| **Sentiment Analysis** | Cooperative / competitive / predatory intent scoring |
| **Strategy Classifier** | Random Forest on 9 engineered behavioral features (sklearn) |
| **Price Forecaster** | Time-series regression for early-warning price convergence |
| **Demand Shock** | Exogenous perturbation — measures coordinated cross-firm response |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│   Live Dashboard (HTML/CSS/JS + Chart.js)           │
│  Price Charts │ Λ Chart │ Narrator │ Shock Control  │
│      Demo mode (Vercel) │ Live WebSocket (local)    │
└────────────────────────┬────────────────────────────┘
                         │ WebSocket + REST
┌────────────────────────▼────────────────────────────┐
│             FastAPI Server (api_server.py)           │
│  /ws/simulate │ /api/status │ /api/shock/{firm_id}  │
└───────────┬─────────────────────────────┬───────────┘
            │ async webhooks              │
┌───────────▼─────────────┐  ┌────────────▼──────────────┐
│  n8n Automation Engine  │  │   Antitrust Regulator    │
│  (Port 5678)            │  │  Λ Monitor │ NLP Cluster │
│  Alerts & Summaries     │  │  Sentiment │ Forecaster  │
└─────────────────────────┘  └────────────┬─────────────┘
                                          │ observes
┌─────────────────────────────────────────▼───────────┐
│           Bertrand Market Engine                    │
│  MNL Demand → Shares → Profits → Λ                  │
└────────┬───────────────────────┬────────────────────┘
         │ prices                │ state
┌────────▼───────────────────────▼────────────────────┐
│              Agent Pool (N=5)                        │
│  LLM │ RAG │ Q-Learning │ DQN │ Heuristic           │
└────────┬───────────────┬────────────────────────────┘
         │               │
┌────────▼────────┐ ┌────▼───────────────────────────┐
│  RAG Memory     │ │  PostgreSQL 16 + pgvector       │
│  (pgvector)     │ │  Simulation logs + embeddings   │
└─────────────────┘ └────────────────────────────────┘
```

---

## Project Structure

```
antitrust_sim/
├── market/
│   ├── demand.py              # MNL demand model, Nash & Monopoly solvers
│   └── engine.py              # Bertrand game loop, round management
│
├── agents/
│   ├── base_agent.py          # Abstract agent interface (PricingAgent ABC)
│   ├── heuristic_agent.py     # Steady, Follower, Undercut strategies
│   ├── llm_agent.py           # LLM agent (Groq API, scratchpad parsing)
│   ├── rl_agent.py            # Q-Learning agent (tabular, ε-greedy)
│   ├── dqn_agent.py           # Deep Q-Network (neural net RL, pure NumPy)
│   └── rag_agent.py           # RAG-enhanced LLM (hybrid pgvector memory)
│
├── regulator/
│   ├── detector.py            # Λ monitoring, 3-tier alert system
│   ├── nlp_cluster.py         # Scratchpad embedding similarity analysis
│   ├── sentiment.py           # Intent analysis (cooperative/competitive)
│   └── perturbation.py        # Demand shock experiments
│
├── database/
│   ├── schema.sql             # PostgreSQL schema (6 tables + pgvector)
│   ├── db.py                  # Database logger (rounds, firms, scratchpads)
│   └── memory.py              # Hybrid RAG vector memory (pgvector + SQL)
│
├── analysis/
│   ├── plots.py               # Publication-ready figures (Figures 1–7)
│   ├── real_data.py           # Empirical validation (BLS gasoline via FRED, Amazon)
│   ├── strategy_classifier.py # Random Forest behavioral classifier
│   └── forecaster.py          # Time-series price forecasting
│
├── data_loaders/
│   ├── base.py                # MarketContext + price history + fallback provenance
│   ├── gasoline.py            # BLS regional gasoline via FRED (5 census divisions)
│   ├── crypto.py              # CoinGecko BTC/USD daily history (5 venues)
│   ├── amazon.py              # Local CSV — Wireless Earbuds seller prices
│   ├── airlines.py            # Indian domestic carriers (DEL-BOM, static)
│   └── rideshare.py           # Uber/Lyft surge parameters (static)
│
├── dashboard/
│   ├── index.html             # Landing page — research pitch + methodology
│   ├── app.html               # Live simulation dashboard
│   ├── style.css              # Morning-light editorial theme
│   ├── script.js              # Real-time charts, narrator, shock control
│   └── demo-data.js           # Pre-computed simulation data for Vercel
│
├── n8n/
│   └── collusion_alert_workflow.json # Alert pipeline (Normalize → severity router)
│
├── api_server.py              # FastAPI backend (WebSocket + REST + Webhooks)
├── run_simulation.py          # CLI entry point (all modes + datasets)
├── start_echo.ps1             # One-script full-stack startup (Windows)
├── docker-compose.yml         # PostgreSQL + pgvector + n8n containers
├── vercel.json                # Vercel static deployment config
├── requirements.txt           # Python dependencies
├── echo_learning_guide.md     # Tools, algorithms, viva reference
├── echo_project_guide.md      # Architecture, agents, detective system, Q&A
└── echo_complete_guide.md     # Short teammate / viva walkthrough
```

---

## Documentation

| Guide | Audience | Contents |
|-------|----------|----------|
| [echo_complete_guide.md](echo_complete_guide.md) | Teammates / quick viva | Problem → market → agents → detective in plain language |
| [echo_project_guide.md](echo_project_guide.md) | Project walkthrough | Architecture, 5 datasets, scale-invariant Λ, file map, Viva Q&A |
| [echo_learning_guide.md](echo_learning_guide.md) | Deep study | Tools, algorithms, cheat sheets, concept → code cross-reference |

---

## AI / ML Techniques — 14 Total

| # | Technique | Category | Module |
|---|-----------|----------|--------|
| 1 | Groq LLM (Allam 2 7B) | Generative AI | `agents/llm_agent.py` |
| 2 | Structured Prompt Engineering | NLP | `agents/llm_agent.py` |
| 3 | Tabular Q-Learning | Reinforcement Learning | `agents/rl_agent.py` |
| 4 | Deep Q-Network (DQN) | Deep Reinforcement Learning | `agents/dqn_agent.py` |
| 5 | RAG (Retrieval-Augmented Generation) | GenAI + IR | `agents/rag_agent.py` |
| 6 | Text Embeddings (nomic-embed-text) | Representation Learning | `database/memory.py` |
| 7 | Vector Similarity Search (pgvector) | Database AI | `database/memory.py` |
| 8 | Hybrid RAG (Semantic + SQL filtering) | Advanced IR | `database/memory.py` |
| 9 | NLP Semantic Clustering | NLP | `regulator/nlp_cluster.py` |
| 10 | Sentiment & Intent Analysis | NLP | `regulator/sentiment.py` |
| 11 | Anomaly Detection (Λ Monitor) | Statistical AI | `regulator/detector.py` |
| 12 | Causal Perturbation Testing | Experimental AI | `regulator/perturbation.py` |
| 13 | Random Forest Classifier (sklearn) | Supervised ML | `analysis/strategy_classifier.py` |
| 14 | Time-Series Price Forecasting | Predictive ML | `analysis/forecaster.py` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| LLM Runtime | Groq API (Allam 2 7B) for pricing; Ollama optional for embeddings |
| Database | PostgreSQL 16 + pgvector |
| ML Framework | scikit-learn (RF + LR) |
| Numerical | NumPy, SciPy |
| API Server | FastAPI + Uvicorn (ASGI, WebSocket, Async Webhooks) |
| Automation Pipeline | n8n (Normalize payload nodes + severity routing + reports) |
| Frontend | HTML/CSS/JS + Chart.js (autoscaling + `real_avg_series` overlay) |
| Deployment | Vercel (static) + local uvicorn |
| Infrastructure | Docker Compose (pgvector DB + n8n engine) |
| Data & Analysis | Pandas, Matplotlib, Seaborn, BLS/FRED, CoinGecko |

---

## ⚡ n8n Workflow Automation Pipeline

ECHO includes an **n8n automated monitoring pipeline** that acts as an enterprise regulatory alert bridge.

```
                  ┌─────────────────────────────────┐
                  │    ECHO FastAPI Server           │
                  │  (api_server.py Webhooks)       │
                  └────────────────┬────────────────┘
                                   │ HTTP POST (fire-and-forget)
                  ┌────────────────▼────────────────┐
                  │     n8n Workflow Engine         │
                  │     (http://localhost:5678)     │
                  └────────────────┬────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         │                                                   │
┌────────▼──────────────────────┐         ┌──────────────────▼──────────────────────┐
│ Alert Webhook                 │         │ Simulation Complete Webhook              │
│ /webhook/echo-alert           │         │ /webhook/echo-simulation-complete        │
└────────┬──────────────────────┘         └──────────────────┬──────────────────────┘
         │                                                   │
┌────────▼──────────────────────┐         ┌──────────────────▼──────────────────────┐
│ Normalize Alert Payload       │         │ Normalize Complete Payload                │
│ (flatten nested `$json.body`) │         │ (flatten nested `$json.body`)           │
└────────┬──────────────────────┘         └──────────────────┬──────────────────────┘
         │                                                   │
┌────────▼──────────────────────┐         ┌──────────────────▼──────────────────────┐
│ Severity Router               │         │ Format Simulation Report                   │
│ (Critical ≥0.7 / Warn ≥0.5)  │         │ (Mean/Peak Λ, alerts, mode, dataset)         │
└────────┬──────────────────────┘         └──────────────────┬──────────────────────┘
         │                                                   │
┌────────▼──────────────────────┐         ┌──────────────────▼──────────────────────┐
│ Format Alert → Score Card     │         │ Send Report                             │
│ (Watch / Warning / Critical)   │         │ (Slack/Email hook point)                │
└───────────────────────────────┘         └─────────────────────────────────────────┘
```

- **Docker Integration:** n8n runs as a persistent service inside `docker-compose.yml` on port `5678` with a dedicated data volume (`echo_n8n_data`).
- **Fire-and-Forget Webhooks:** `api_server.py` dispatches non-blocking async tasks (`asyncio.create_task`) when:
  1. A collusion alert is triggered (`/webhook/echo-alert`) — common on DQN runs once Λ climbs
  2. A simulation finishes (`/webhook/echo-simulation-complete`)
- **Payload Normalize:** Newer n8n webhook nodes nest POST JSON under `.body`. The workflow’s **Normalize** code nodes flatten fields so severity routers can read `$json.lambda` directly.
- **Workflow File:** Import (or re-import) `n8n/collusion_alert_workflow.json` into `http://localhost:5678`, then **Publish**. Without Publish, production webhooks return 404.

---

## Theoretical Foundation

| Component | Reference |
|-----------|-----------|
| Demand Model | Anderson, de Palma & Thisse (1992). *Discrete Choice Theory of Product Differentiation.* MIT Press. |
| Collusion Metric (Λ) | Calvano, Calzolari, Denicolo & Pastorello (2020). *Artificial Intelligence, Algorithmic Pricing, and Collusion.* AER, 110(10), 3267–3297. |
| LLM Agent Design | Fish et al. (2025). *Algorithmic Collusion by Large Language Models.* arXiv. |
| Q-Learning Baseline | Calvano et al. (2020). AER. |
| DQN Architecture | Mnih et al. (2015). *Human-level control through deep reinforcement learning.* Nature, 518, 529–533. |
| Gasoline Validation | Eckert (2013). *Retail Gasoline Price Cycles Across Spatially Dispersed Gasoline Stations.* J. Economic Surveys. |

---

## Development Roadmap

| Phase | Description | Status |
|-------|------------|--------|
| 1 | Market simulation engine (MNL demand, Nash/Monopoly solvers) | ✅ Complete |
| 2 | Docker + PostgreSQL infrastructure | ✅ Complete |
| 3 | LLM pricing agents (Groq API + scratchpad parsing) | ✅ Complete |
| 4 | RAG episodic memory (hybrid pgvector + SQL) | ✅ Complete |
| 5 | Collusion detection pipeline (6 methods) | ✅ Complete |
| 5.5 | Empirical validation (BLS/FRED gasoline, Amazon, Airlines, Uber, Pharma, DRAM) | ✅ Complete |
| 6 | Q-Learning RL baseline agents | ✅ Complete |
| 7 | Analysis & visualization (research figures) | ✅ Complete |
| 8 | FastAPI + live WebSocket dashboard | ✅ Complete |
| 9 | Deep Q-Network (DQN) agent | ✅ Complete |
| 10 | NLP sentiment + strategy classifier + price forecasting | ✅ Complete |
| 11 | Vercel deployment with interactive demo mode | ✅ Complete |
| 12 | Morning-light editorial redesign + live narrator bar | ✅ Complete |
| 13 | 6-market empirical validation panel | ✅ Complete |
| 14 | One-script full-stack startup (start_echo.ps1) | ✅ Complete |
| 15 | n8n automated regulatory alert pipeline (async webhooks + 11-node workflow) | ✅ Complete |
| 16 | Real-world dataset integration (BLS/FRED, CoinGecko, Amazon CSV, Airlines, Rideshare) | ✅ Complete |
| 17 | Scale-invariant calibration + real price-history overlays on dashboard | ✅ Complete |

---

## Author

**Aryan Raj** — [@ARYANRAJ1121](https://github.com/ARYANRAJ1121)

## License

[MIT](LICENSE)
