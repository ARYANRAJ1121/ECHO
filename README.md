<div align="center">

# ECHO

**Emergent Collusion in Heterogeneous Oligopolies**

A simulation framework for studying tacit coordination among autonomous AI pricing agents in repeated Bertrand competition.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3_8B-000000?logo=ollama)](https://ollama.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Overview

ECHO investigates whether large language model (LLM) agents, when deployed as independent pricing managers in a simulated oligopoly, develop **tacit coordination strategies** — a phenomenon of growing regulatory concern as algorithmic pricing becomes prevalent across industries.

The framework implements a repeated Bertrand pricing game where heterogeneous AI agents (LLM-based, reinforcement learning, and rule-based) compete by simultaneously setting prices. Market outcomes are evaluated through the Multinomial Logit demand model, and emergent pricing behaviors are analyzed against Nash equilibrium and joint monopoly benchmarks.

### Motivation

Algorithmic pricing systems are already deployed at scale (Amazon, Uber, airlines, rental markets). Recent regulatory actions — including the [DOJ lawsuit against RealPage (2024)](https://www.justice.gov/opa/pr/justice-department-sues-realpage-algorithmic-pricing-scheme-harms-millions-renters) for AI-enabled rent coordination — highlight the urgency of understanding how autonomous agents interact in competitive markets. ECHO provides a controlled experimental environment to study these dynamics.

---

## Key Results

| Agent Type | Collusion Index (λ) | Avg. Price | Interpretation |
|-----------|---------------------|------------|----------------|
| Heuristic (rule-based) | 0.06 | ~$1.53 | Competitive — near Nash equilibrium |
| LLM (Llama 3 8B) | 20.61 | ~$3.20 | Supra-competitive — significant price inflation |
| Q-Learning (RL) | Converges ↑ | Rises over rounds | Gradual coordination via reward optimization |
| DQN (Deep RL) | Converges ↑ | Rises over rounds | Neural network-based coordination via experience replay |

> **LLM agents priced at approximately 2× the Nash equilibrium level.** Scratchpad analysis revealed strategic reasoning patterns: agents monitored competitor pricing and adjusted upward, consistent with tacit coordination behavior described in the algorithmic pricing literature.

### Empirical Validation

| Real-World Market | λ Proxy | Source |
|------------------|---------|--------|
| US Gasoline (EIA) | 0.91 | FRED API — Weekly retail prices by PADD region |
| Amazon Electronics | 0.87 | Calibrated from Kaggle dataset (42K listings, 6 categories) |

---

## Research Contributions

1. **LLM Tacit Coordination** — Demonstrating that LLM-based pricing agents develop supra-competitive pricing without explicit coordination instructions
2. **RAG Memory Ablation** — Investigating whether retrieval-augmented episodic memory (hybrid RAG with semantic + structural filtering) accelerates or dampens emergent coordination
3. **Heterogeneous Agent Comparison** — Controlled comparison of LLM, DQN, Q-Learning RL, and rule-based agents under identical market conditions
4. **Multi-Method Detection Pipeline** — Five independent detection methods: λ-index monitoring, NLP similarity, sentiment analysis, ML strategy classification, and demand shock perturbation
5. **Scratchpad Reasoning Analysis** — Extracting and analyzing agent decision rationale via structured prompting to identify coordination signals
6. **Live Monitoring Dashboard** — Real-time WebSocket-based dashboard for observing emergent collusion with demand shock intervention
7. **Deep RL Comparison** — DQN agent with experience replay and target network, demonstrating that collusion is architecture-independent
8. **Predictive Price Forecasting** — Time-series regression model for early-warning detection of price convergence

---

## Methodology

### Market Model

The simulation uses a **Multinomial Logit (MNL) demand model** with N symmetric firms competing in a differentiated-product Bertrand game.

**Demand (market share for firm i):**

```
sᵢ(p) = exp((aᵢ - pᵢ) / μ) / Σⱼ exp((aⱼ - pⱼ) / μ)
```

**Collusion Index (λ):**

```
λ = (p̄ - p_Nash) / (p_Monopoly - p_Nash)
```

Where `λ = 0` corresponds to the Nash equilibrium (full competition) and `λ = 1` corresponds to the joint monopoly outcome (full coordination). Values above 1 indicate prices exceeding the theoretical joint profit maximum.

### Agent Architecture

| Agent | Description | Decision Mechanism |
|-------|------------|-------------------|
| **LLM Agent** | Llama 3 8B via Ollama | Structured prompting with `<scratchpad>` reasoning + `<price>` output |
| **RAG Agent** | LLM + Hybrid RAG memory | Episodic memory retrieval (semantic + SQL filtering) before pricing |
| **RL Agent** | Tabular Q-Learning | Bellman equation over discretized price–state space, ε-greedy exploration |
| **DQN Agent** | Deep Q-Network | 3-layer neural network with experience replay + target network (numpy) |
| **Heuristic** | Rule-based baselines | Fixed markup, market-following, undercutting strategies |

### Detection Methods

| Method | Signal | Mechanism |
|--------|--------|-----------|
| λ Monitor | Price levels | Continuous tracking against Nash/Monopoly benchmarks with 3-tier alerts |
| NLP Clustering | Reasoning similarity | Embedding-based cosine similarity across agent scratchpads |
| Sentiment Analysis | Intent classification | Cooperative/competitive/predatory intent scoring with drift detection |
| Strategy Classifier | Behavioral labeling | Random Forest (sklearn) classifying agent behavior from 9 engineered features |
| Demand Shocks | Coordinated response | Exogenous perturbation to one firm; measure cross-firm reaction |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│   Live Dashboard (HTML/JS + Chart.js + WebSocket)   │
│  Price Charts │ λ Gauge │ Scratchpads │ Shock Ctrl  │
└────────────────────────┬────────────────────────────┘
                         │ WebSocket + REST
┌────────────────────────▼────────────────────────────┐
│             FastAPI Server (api_server.py)           │
│  /ws/simulate │ /api/status │ /api/shock/{firm_id}  │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│             Antitrust Regulator                      │
│  λ Monitor  │  NLP Similarity  │  Demand Shocks     │
└────────────────────────┬────────────────────────────┘
                         │ observes
┌────────────────────────▼────────────────────────────┐
│           Bertrand Market Engine                     │
│  MNL Demand → Shares → Profits → λ                  │
└────────┬───────────────────────┬─────────────────────┘
         │ prices                │ observations
┌────────▼───────────────────────▼─────────────────────┐
│              Agent Pool (N=5)                        │
│  LLM │ RAG │ RL (Q-Learn) │ DQN (Deep RL) │ Heur.  │
└────────┬───────────────┬─────────────────────────────┘
         │               │
┌────────▼────────┐ ┌────▼──────────────────────┐
│  RAG Memory     │ │  PostgreSQL 16            │
│  (pgvector)     │ │  + pgvector + embeddings  │
└─────────────────┘ └───────────────────────────┘
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
│   ├── llm_agent.py           # LLM agent (Ollama API, scratchpad parsing)
│   ├── rl_agent.py            # Q-Learning agent (tabular, ε-greedy)
│   ├── dqn_agent.py           # Deep Q-Network agent (neural net RL, numpy)
│   └── rag_agent.py           # RAG-enhanced LLM agent (hybrid memory)
│
├── regulator/
│   ├── detector.py            # λ monitoring and 3-tier alerts
│   ├── nlp_cluster.py         # Scratchpad embedding similarity analysis
│   ├── sentiment.py           # NLP intent analysis (cooperative/competitive/predatory)
│   └── perturbation.py        # Demand shock perturbation experiments
│
├── database/
│   ├── schema.sql             # PostgreSQL schema (6 tables + pgvector)
│   ├── db.py                  # Database logger (rounds, firms, scratchpads)
│   └── memory.py              # Hybrid RAG vector memory (pgvector + SQL)
│
├── analysis/
│   ├── plots.py               # Publication-ready figures (Figures 1-7)
│   ├── real_data.py           # Empirical validation (EIA gasoline, Amazon)
│   ├── strategy_classifier.py # Random Forest agent behavior classifier (sklearn)
│   └── forecaster.py          # Time-series price forecasting (Linear Regression)
│
├── dashboard/
│   ├── index.html             # Live dashboard UI (glassmorphism design)
│   ├── style.css              # Premium dark theme with micro-animations
│   └── script.js              # Real-time charts, scratchpad viewer, shock ctrl
│
├── api_server.py              # FastAPI backend (WebSocket + REST API)
├── run_simulation.py          # CLI entry point (all modes)
├── docker-compose.yml         # PostgreSQL + pgvector container
├── requirements.txt           # Python dependencies
└── todo.md                    # Development roadmap
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) with Llama 3 8B — *required for LLM/RAG modes only*
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — *required for database persistence and RAG mode*

### Installation

```bash
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO
pip install -r requirements.txt
```

### Quick Start

```bash
# ─── Heuristic agents (no GPU, no Docker required) ───
python run_simulation.py --mode dummy --rounds 50

# ─── Q-Learning RL agents (no GPU required) ───
python run_simulation.py --mode rl --rounds 10000

# ─── LLM agents (requires Ollama running) ───
ollama serve                                            # Terminal 1
python run_simulation.py --mode llm --rounds 10         # Terminal 2

# ─── RAG agents (requires Ollama + Docker PostgreSQL) ───
docker compose up -d db                                 # Start PostgreSQL
python run_simulation.py --mode rag --rounds 10 --db    # RAG + DB

# ─── With database persistence ───
docker compose up -d db
python run_simulation.py --mode dummy --rounds 50 --db

# ─── Empirical validation ───
python run_simulation.py --mode dummy --rounds 50 --validate
```

### Live Dashboard

```bash
# Start the API server
python api_server.py

# Open in browser
# http://localhost:8000
```

The dashboard provides:
- **Real-time price trajectory** and **λ trajectory** charts
- **Regulator gauge** with color-coded collusion severity
- **Firm performance table** with live profit deltas
- **Scratchpad viewer** — read LLM agent reasoning in real-time
- **Demand shock control** — trigger shocks mid-simulation and observe reactions
- **Summary overlay** with collusion verdict at simulation end

Supports Heuristic, Q-Learning, and LLM agent modes.

---

## Theoretical Foundation

| Component | Reference |
|-----------|-----------|
| Demand Model | Anderson, de Palma & Thisse (1992). *Discrete Choice Theory of Product Differentiation.* MIT Press. |
| Collusion Metric | Calvano, Calzolari, Denicolo & Pastorello (2020). *Artificial Intelligence, Algorithmic Pricing, and Collusion.* AER, 110(10), 3267–3297. |
| LLM Agent Design | Fish et al. (2025). *Algorithmic Collusion by Large Language Models.* arXiv preprint. |
| Q-Learning Agents | Calvano et al. (2020). *Artificial Intelligence, Algorithmic Pricing, and Collusion.* AER. |

---

## AI/ML Techniques Inventory

ECHO uses **14 distinct AI/ML techniques** across the codebase:

| # | Technique | Category | Module |
|---|-----------|----------|--------|
| 1 | Llama 3 (LLM) | Generative AI | `agents/llm_agent.py` |
| 2 | Prompt Engineering | NLP | `agents/llm_agent.py` |
| 3 | Tabular Q-Learning | Reinforcement Learning | `agents/rl_agent.py` |
| 4 | Deep Q-Network (DQN) | Deep Reinforcement Learning | `agents/dqn_agent.py` |
| 5 | RAG (Retrieval-Augmented Generation) | Information Retrieval + GenAI | `agents/rag_agent.py` |
| 6 | Text Embeddings (nomic-embed-text) | Representation Learning | `database/memory.py` |
| 7 | Vector Similarity Search (pgvector) | Database AI | `database/memory.py` |
| 8 | Hybrid RAG (Semantic + SQL) | Advanced IR | `database/memory.py` |
| 9 | NLP Semantic Clustering | NLP | `regulator/nlp_cluster.py` |
| 10 | Sentiment & Intent Analysis | NLP | `regulator/sentiment.py` |
| 11 | Anomaly Detection (λ Monitor) | Statistical AI | `regulator/detector.py` |
| 12 | Causal Perturbation Testing | Experimental AI | `regulator/perturbation.py` |
| 13 | Random Forest Classifier | Supervised ML (sklearn) | `analysis/strategy_classifier.py` |
| 14 | Time-Series Forecasting | Predictive ML | `analysis/forecaster.py` |

---

## Development Roadmap

See [`todo.md`](todo.md) for detailed task breakdowns.

| Phase | Description | Status |
|-------|------------|--------|
| 1 | Market simulation engine (MNL demand, Nash/Monopoly solvers) | ✅ Complete |
| 2 | Docker + PostgreSQL infrastructure | ✅ Complete |
| 3 | LLM pricing agents (Ollama + scratchpad parsing) | ✅ Complete |
| 4 | RAG episodic memory (hybrid pgvector + SQL) | ✅ Complete |
| 5 | Collusion detection pipeline (3 methods) | ✅ Complete |
| 5.5 | Empirical validation (EIA gasoline, Amazon) | ✅ Complete |
| 6 | Q-Learning RL baseline agents | ✅ Complete |
| 7 | Analysis & visualization (6 research figures) | ✅ Complete |
| 8 | FastAPI + live dashboard | ✅ Complete |
| 9 | Deep Q-Network (DQN) agent | ✅ Complete |
| 10 | NLP sentiment analysis + strategy classifier + price forecasting | ✅ Complete |

---

## Author

**Aryan Raj**

## License

[MIT](LICENSE)
