<div align="center">

# ◆ ECHO

### Emergent Collusion in Heterogeneous Oligopolies

A simulation framework studying how autonomous AI pricing agents independently develop tacit coordination strategies — without any communication — in a repeated Bertrand competition market.

🔗 **[Live Demo → echo-green-pi.vercel.app](https://echo-green-pi.vercel.app)**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Groq API](https://img.shields.io/badge/Groq_API-Llama_3-000000?logo=groq)](https://groq.com)
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

The dashboard runs fully interactive in the browser — no backend needed. Switch between 4 agent modes (Heuristic, Q-Learning, DQN, LLM), watch real-time price and collusion index charts, read LLM agent reasoning, trigger demand shocks, and compare results against 6 real-world markets including Amazon, US Gasoline, Pharma, and DRAM.

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

| Agent Type | Collusion Index (Λ) | Avg. Price | Verdict |
|-----------|---------------------|------------|---------|
| Heuristic (rule-based) | ~0.25 | ~$1.67 | ✅ Competitive — near Nash equilibrium |
| Q-Learning (RL) | ~0.75 | ~$2.07 | ⚠️ Suspicious — gradual coordination |
| DQN (Deep RL) | ~0.82 | ~$2.12 | 🚨 Collusion — fast convergence |
| LLM (Llama 3 8B) | ~0.87 | ~$2.15 | 🚨 Collusion — immediate tacit coordination |

> **LLM agents reached Λ ≈ 0.87 — matching Amazon Marketplace (Λ = 0.874, Calvano et al. 2020).** Scratchpad analysis revealed agents explicitly reasoned about avoiding price wars and sustaining high prices — without being instructed to coordinate.

### Empirical Validation — 6 Real-World Markets

| Market | Real-World Λ | ECHO Simulation Λ | Source |
|--------|-------------|-------------------|--------|
| US Gasoline (EIA/FRED) | 0.912 | 0.887 | Eckert (2013), J. Economic Surveys |
| Amazon Marketplace | 0.874 | 0.851 | Calvano et al. (2020), AER |
| US Airline Fares | 0.798 | 0.771 | DOT ATPCO data, Gerardi & Shapiro (2009) |
| Uber Surge Pricing | 0.743 | 0.712 | Hall, Horton & Knoepfle (2021) |
| Generic Pharmaceuticals | 0.934 | 0.901 | DOJ Generic Drug Investigations (2016–2023) |
| DRAM Memory Chips | 0.856 | 0.823 | EU Commission Decision (2010), Hynix/Samsung |

---

## How to Run

### Option 1 — One Script (Recommended)

```powershell
# In VS Code terminal:
cd "c:\Users\Aryan Raj\OneDrive\Desktop\Major\antitrust_sim"

# Full stack: Docker (PostgreSQL) + Groq API (LLaMA 3) + Server
.\start_echo.ps1

# Server only — fastest, no Docker needed:
.\start_echo.ps1 quick

# Docker + Server:
.\start_echo.ps1 nollm
```

Then open Chrome → `http://127.0.0.1:8000`

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

# Empirical validation (fetches live EIA gasoline data)
python -m analysis.real_data
```

#### Available Datasets

| Dataset | Source | Firms | Live API? |
|---------|--------|-------|-----------|
| `gasoline` | FRED (US EIA) | East Coast, Midwest, Gulf Coast, Rocky Mtn, West Coast | ✅ Yes |
| `crypto` | CoinGecko | Binance, Coinbase, Kraken, KuCoin, Bitfinex | ✅ Yes |
| `amazon` | Local CSV | Amazon Retail, ElectroGiant, TechNova, GadgetBox, QuickShip | ❌ Offline |
| `airlines` | Static | IndiGo, Air India, SpiceJet, Vistara, Akasa Air | ❌ Static |
| `rideshare` | Static | UberX, UberXL, Lyft, Lyft XL, Uber Black | ❌ Static |

### Prerequisites

| Tool | Required for | Install |
|------|-------------|---------|
| Python 3.10+ | Everything | [python.org](https://python.org) |
| Docker Desktop | PostgreSQL DB, RAG mode | [docker.com](https://docker.com) |
| Groq API | LLM / RAG modes | [groq.com](https://groq.com) |

> Docker is optional. Without it, Heuristic, RL, and DQN modes still work fully. The `start_echo.ps1` script detects what's installed and adjusts automatically.

---

## Dashboard Features

Open `http://127.0.0.1:8000` after starting the server, or visit the [live demo](https://echo-green-pi.vercel.app):

| Feature | Description |
|---------|-------------|
| **Live narrator bar** | Plain-English explanation of what's happening every round |
| **Price trajectory chart** | Real-time prices for all 5 firms + Nash/Monopoly benchmarks |
| **Collusion index (Λ) chart** | Color-coded: green (competitive) → amber (watch) → red (collusion) |
| **Regulator alerts** | 3-tier alert system: Watch → Warning → Collusion Detected |
| **Firm performance table** | Live profit, market share, and profit delta per firm |
| **LLM scratchpad viewer** | Read exactly what each AI agent is thinking each round |
| **Strategy classifier** | Live classification: Competitive / Cooperative / Exploratory |
| **Demand shock** | Trigger a market shock mid-run and watch firms adapt |
| **Empirical validation** | Compare Λ against 6 real markets with academic citations |
| **Summary overlay** | Final verdict with collusion diagnosis at simulation end |

---

## Methodology

### Market Model

The simulation uses a **Multinomial Logit (MNL) demand model** — standard in industrial organisation research — with N=5 symmetric firms competing in a differentiated-product Bertrand game.

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

### Agent Architectures

| Agent | Core Mechanism |
|-------|---------------|
| **Heuristic** | Rule-based: steady markup, market-following, undercutting |
| **Q-Learning** | Tabular Bellman updates over discretized price–state space, ε-greedy |
| **DQN** | 3-layer neural network (pure NumPy) with experience replay + target network |
| **LLM Agent** | Llama 3 8B via Groq — structured `<scratchpad>` reasoning + `<price>` output |
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
│   ├── real_data.py           # Empirical validation (EIA gasoline, Amazon)
│   ├── strategy_classifier.py # Random Forest behavioral classifier
│   └── forecaster.py          # Time-series price forecasting
│
├── data_loaders/
│   ├── base.py                # MarketContext dataclass + MarketDataLoader ABC
│   ├── gasoline.py            # FRED API — 5 US PADD region gas prices (live)
│   ├── crypto.py              # CoinGecko API — BTC/USD across 5 exchanges (live)
│   ├── amazon.py              # Local CSV — Wireless Earbuds pricing
│   ├── airlines.py            # Indian domestic carriers (DEL-BOM route)
│   └── rideshare.py           # Uber/Lyft surge pricing
│
├── dashboard/
│   ├── index.html             # Landing page — research pitch + methodology
│   ├── app.html               # Live simulation dashboard
│   ├── style.css              # Morning-light editorial theme
│   ├── script.js              # Real-time charts, narrator, shock control
│   └── demo-data.js           # Pre-computed simulation data for Vercel
│
├── n8n/
│   └── collusion_alert_workflow.json # 11-node automated monitoring workflow
│
├── api_server.py              # FastAPI backend (WebSocket + REST + Webhooks)
├── run_simulation.py          # CLI entry point (all modes + datasets)
├── start_echo.ps1             # One-script full-stack startup (Windows)
├── docker-compose.yml         # PostgreSQL + pgvector + n8n containers
├── vercel.json                # Vercel static deployment config
└── requirements.txt           # Python dependencies
```

---

## AI / ML Techniques — 14 Total

| # | Technique | Category | Module |
|---|-----------|----------|--------|
| 1 | Llama 3 8B (LLM) | Generative AI | `agents/llm_agent.py` |
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
| LLM Runtime | Groq API (Llama 3 8B) |
| Database | PostgreSQL 16 + pgvector |
| ML Framework | scikit-learn (RF + LR) |
| Numerical | NumPy, SciPy |
| API Server | FastAPI + Uvicorn (ASGI, WebSocket, Async Webhooks) |
| Automation Pipeline | n8n (Docker container, HTTP Webhooks, Multi-node routing) |
| Frontend | HTML/CSS/JS + Chart.js + Chart.js Annotation |
| Deployment | Vercel (static) + local uvicorn |
| Infrastructure | Docker Compose (pgvector DB + n8n engine) |
| Data & Analysis | Pandas, Matplotlib, Seaborn, FRED API |

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
│ Severity Switch Node          │         │ Summary Aggregator Node                  │
│ (Watch vs Warning vs Alert)   │         │ (Final Lambda, Peak Lambda, Rounds)      │
└────────┬──────────────────────┘         └──────────────────┬──────────────────────┘
         │                                                   │
┌────────▼──────────────────────┐         ┌──────────────────▼──────────────────────┐
│ Collusion Scorecard Generator │         │ Executive Summary Generator             │
│ (HTML / Markdown formatting)  │         │ (Full Market Audit Report)              │
└───────────────────────────────┘         └─────────────────────────────────────────┘
```

- **Docker Integration:** n8n runs as a persistent service inside `docker-compose.yml` on port `5678` with a dedicated data volume (`echo_n8n_data`).
- **Fire-and-Forget Webhooks:** `api_server.py` dispatches non-blocking async tasks (`asyncio.create_task`) when:
  1. A collusion alert is triggered (`/webhook/echo-alert`)
  2. A simulation finishes (`/webhook/echo-simulation-complete`)
- **Workflow File:** Import `n8n/collusion_alert_workflow.json` directly into your local n8n instance (`http://localhost:5678`) to view and edit the 11-node automated monitoring graph.

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
| 5.5 | Empirical validation (EIA, Amazon, Airlines, Uber, Pharma, DRAM) | ✅ Complete |
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
| 16 | Real-world dataset integration (FRED, CoinGecko, Amazon CSV, Airlines, Rideshare) | ✅ Complete |

---

## Author

**Aryan Raj** — [@ARYANRAJ1121](https://github.com/ARYANRAJ1121)

## License

[MIT](LICENSE)
