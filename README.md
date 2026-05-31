<div align="center">

# ECHO

**Emergent Collusion in Heterogeneous Oligopolies**

A simulation framework for studying tacit coordination among autonomous AI pricing agents in repeated Bertrand competition.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3_8B-000000?logo=ollama)](https://ollama.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Overview

ECHO investigates whether large language model (LLM) agents, when deployed as independent pricing managers in a simulated oligopoly, develop **tacit coordination strategies** — a phenomenon of growing regulatory concern as algorithmic pricing becomes prevalent across industries.

The framework implements a repeated Bertrand pricing game where heterogeneous AI agents (LLM-based, reinforcement learning, and rule-based) compete by simultaneously setting prices. Market outcomes are evaluated through the Multinomial Logit demand model, and emergent pricing behaviors are analyzed against Nash equilibrium and joint monopoly benchmarks.

### Motivation

Algorithmic pricing systems are already deployed at scale (Amazon, Uber, airlines, rental markets). Recent regulatory actions — including the [DOJ lawsuit against RealPage (2024)](https://www.justice.gov/opa/pr/justice-department-sues-realpage-algorithmic-pricing-scheme-harms-millions-renters) for AI-enabled rent coordination — highlight the urgency of understanding how autonomous agents interact in competitive markets. ECHO provides a controlled experimental environment to study these dynamics.

---

## Key Results (Preliminary)

| Agent Type | Collusion Index (λ) | Avg. Price | Interpretation |
|-----------|---------------------|------------|----------------|
| Heuristic (rule-based) | 0.06 | 1.525 | Competitive — near Nash equilibrium |
| LLM (Llama 3 8B) | 20.61 | 3.200 | Supra-competitive — significant price inflation |

> In preliminary experiments (3 rounds, 5 agents), LLM agents priced at approximately **2× the Nash equilibrium** level. Scratchpad analysis revealed strategic reasoning patterns: agents monitored competitor pricing and adjusted upward, consistent with tacit coordination behavior described in the algorithmic pricing literature.

---

## Research Contributions

1. **LLM Tacit Coordination** — Demonstrating that LLM-based pricing agents develop supra-competitive pricing without explicit coordination instructions
2. **RAG Memory Ablation** — Investigating whether retrieval-augmented episodic memory accelerates or dampens emergent coordination (novel contribution)
3. **Heterogeneous Agent Comparison** — Controlled comparison of LLM, Q-Learning RL, and rule-based agents under identical market conditions
4. **Multi-Method Detection Pipeline** — Three independent detection methods: λ-index monitoring, scratchpad NLP similarity analysis, and demand shock perturbation testing
5. **Scratchpad Reasoning Analysis** — Extracting and analyzing agent decision rationale via structured prompting to identify coordination signals

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
| **RL Agent** | Tabular Q-Learning | Bellman equation over discretized price–state space |
| **Heuristic** | Rule-based baselines | Fixed markup, market-following, undercutting strategies |

### Detection Methods

| Method | Signal | Mechanism |
|--------|--------|-----------|
| λ Monitor | Price levels | Continuous tracking against Nash/Monopoly benchmarks |
| NLP Clustering | Reasoning similarity | Embedding-based cosine similarity across agent scratchpads |
| Demand Shocks | Coordinated response | Exogenous perturbation to one firm; measure cross-firm reaction |

---

## Architecture

```
┌─────────────────────────────────────────┐
│          Antitrust Regulator            │
│  λ Monitor │ NLP Analysis │ Shocks     │
└──────────────────┬──────────────────────┘
                   │ observes
┌──────────────────▼──────────────────────┐
│          Bertrand Market Engine          │
│  MNL Demand → Shares → Profits → λ     │
└────────┬───────────────────┬────────────┘
         │ prices            │ observations
┌────────▼───────────────────▼────────────┐
│            Agent Pool (N=5)             │
│  LLM (Llama 3) │ RL (Q-Learn) │ Rules  │
└────────┬───────────────────┬────────────┘
         │                   │
┌────────▼────────┐ ┌───────▼─────────────┐
│  RAG Memory     │ │  PostgreSQL 16      │
│  (pgvector)     │ │  + pgvector         │
└─────────────────┘ └─────────────────────┘
```

---

## Project Structure

```
echo/
├── market/
│   ├── demand.py              # MNL demand model, Nash & Monopoly solvers
│   └── engine.py              # Bertrand game loop, round management
│
├── agents/
│   ├── base_agent.py          # Abstract agent interface (PricingAgent ABC)
│   ├── heuristic_agent.py     # Steady, Follower, Undercut strategies
│   ├── llm_agent.py           # LLM agent (Ollama API, scratchpad parsing)
│   ├── rl_agent.py            # Q-Learning agent (planned)
│   └── rag_agent.py           # RAG-enhanced LLM agent (planned)
│
├── regulator/                 # Detection pipeline (planned)
│   ├── detector.py            # λ monitoring and alerts
│   ├── nlp_cluster.py         # Scratchpad embedding similarity
│   └── perturbation.py        # Demand shock experiments
│
├── database/
│   ├── schema.sql             # PostgreSQL schema (6 tables)
│   └── db.py                  # Database logger
│
├── analysis/                  # Visualization and statistics (planned)
├── api/                       # FastAPI backend (planned)
├── dashboard/                 # Streamlit dashboard (planned)
│
├── run_simulation.py          # CLI entry point
├── docker-compose.yml         # PostgreSQL + pgvector container
└── todo.md                    # Development roadmap
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) with Llama 3 8B (`ollama pull llama3`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL)

### Installation

```bash
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO
pip install numpy scipy requests psycopg2-binary
```

### Usage

```bash
# Heuristic agents (no GPU required)
python run_simulation.py --mode dummy --rounds 50

# LLM agents (requires Ollama running)
ollama serve                                          # Terminal 1
python run_simulation.py --mode llm --rounds 10       # Terminal 2

# With database persistence (requires Docker)
docker compose up -d db
python run_simulation.py --mode dummy --rounds 50 --db
```

---

## Theoretical Foundation

| Component | Reference |
|-----------|-----------|
| Demand Model | Anderson, de Palma & Thisse (1992). *Discrete Choice Theory of Product Differentiation.* MIT Press. |
| Collusion Metric | Calvano, Calzolari, Denicolo & Pastorello (2020). *Artificial Intelligence, Algorithmic Pricing, and Collusion.* AER, 110(10), 3267–3297. |
| LLM Agent Design | Fish et al. (2025). *Algorithmic Collusion by Large Language Models.* arXiv preprint. |

---

## Development Roadmap

See [`todo.md`](todo.md) for detailed task breakdowns.

| Phase | Description | Status |
|-------|------------|--------|
| 1 | Market simulation engine | ✅ Complete |
| 2 | Docker + PostgreSQL infrastructure | ✅ Complete |
| 3 | LLM pricing agents (Ollama) | ✅ Complete |
| 4 | RAG episodic memory + A/B testing | In Progress |
| 5 | Collusion detection pipeline (3 methods) | Planned |
| 6 | Q-Learning RL baseline agents | Planned |
| 7 | Analysis and visualization | Planned |
| 8 | FastAPI + Streamlit dashboard | Planned |

---

## Author

**Aryan Raj**

## License

[MIT](LICENSE)
