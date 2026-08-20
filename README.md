<div align="center">

# ECHO

**Emergent Collusion in Heterogeneous Oligopolies**

Multi-agent pricing lab where DQN, Q-Learning, and LLM agents compete in a Bertrand market — and spontaneously learn to coordinate without communication.

<br/>

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-echo--green--pi.vercel.app-000?style=for-the-badge&logo=vercel)](https://echo-green-pi.vercel.app)
[![Launch App](https://img.shields.io/badge/Open_Dashboard-127.0.0.1:8000-0ea5e9?style=for-the-badge)](http://127.0.0.1:8000)

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/LLM-Groq_Allam_2-000)](https://groq.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-WebSocket-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/pgvector-RAG_memory-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![RL](https://img.shields.io/badge/RL-Q--Learning_%7C_DQN-F7931E)](https://github.com/ARYANRAJ1121/ECHO)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Why this exists

Algorithmic pricing already runs Amazon, airlines, and ride-hail. Regulators (including the [DOJ vs RealPage, 2024](https://www.justice.gov/opa/pr/justice-department-sues-realpage-algorithmic-pricing-scheme-harms-millions-renters)) are asking a hard question:

> Can independent profit-maximizing AIs learn to keep prices high — without ever talking to each other?

ECHO is a controlled lab for that question: **simulate → measure Λ → detect → alert**.

---

## Quick start

```powershell
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO
pip install -r requirements.txt

# fastest — dashboard only
.\start_echo.ps1 quick

# full stack (Postgres + n8n + server)
.\start_echo.ps1
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** · or skip install and use the **[live demo](https://echo-green-pi.vercel.app)**.

| Mode | Command | Needs |
|------|---------|-------|
| Heuristic / RL / DQN | `python run_simulation.py --dataset gasoline --mode dqn --rounds 500` | Python |
| LLM | `--mode llm` | `GROQ_API_KEY` in `.env` |
| RAG | `--mode rag --db` | Groq + Docker Postgres + Ollama embeddings |

---

## Headline results

Scale-invariant Λ — same `[0, 1]` band on \$3 gasoline and ~\$64k BTC:

| Agent | Λ | Read |
|-------|---:|------|
| Heuristic (control) | **~0.15** | Competitive — stays near Nash |
| Q-Learning | ~0.70–0.80 | Gradual coordination |
| DQN | **~0.61–0.85** | Learns supra-competitive prices |
| Groq Allam 2 7B | **~0.80–0.90** | Immediate tacit coordination |

$$\Lambda = \frac{\bar{p} - p_{\mathrm{Nash}}}{p_{\mathrm{Monopoly}} - p_{\mathrm{Nash}}}$$

Heuristics are anchored as fractions of each market’s Nash→monopoly span. Learning agents climb into the published real-world Λ band (~0.7–0.9) with **zero instruction to collude**.

**Live market proxies** (from loaders): BLS gasoline ≈ **0.90** · Amazon earbuds ≈ **0.87** · Crypto venues ≈ **0.99**

---

## System at a glance

```text
Dashboard (Chart.js) ──WebSocket──▶ FastAPI
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
              Market Engine      Regulator Suite      n8n Alerts
              MNL · Λ · shocks   NLP · RF · forecast  webhooks :5678
                    ▲
         Agents: Heuristic · Q-Learning · DQN · LLM · RAG
                    │
         Data: BLS/FRED · CoinGecko · Amazon CSV · Airlines · Rideshare
                    │
         Store: PostgreSQL 16 + pgvector (logs + RAG memory)
```

### Agents

| | Mechanism |
|--|-----------|
| **Heuristic** | Steady / follower / undercut — control group |
| **Q-Learning** | Tabular Bellman, ε-greedy over price grid |
| **DQN** | Pure-NumPy MLP, replay buffer, target net |
| **LLM** | Groq Allam 2 — `<scratchpad>` + `<price>` |
| **RAG** | LLM + hybrid pgvector retrieval before each bid |

### Detection (6 methods)

Λ streak monitor · scratchpad embedding similarity · intent sentiment · Random Forest strategy labels · price forecaster · demand-shock causal probe

---

## Real markets

| Dataset | Source | History |
|---------|--------|---------|
| `gasoline` | BLS via FRED (5 US divisions) | Monthly series |
| `crypto` | CoinGecko BTC/USD | 90-day daily |
| `amazon` | Local Wireless Earbuds CSV | Per-seller prices |
| `airlines` | DEL–BOM fare/cost estimates | Static (labelled) |
| `rideshare` | Uber/Lyft per-mile estimates | Static (labelled) |

Each loader builds a `MarketContext` (costs, firm names, Nash band, optional `price_series`). Failed live fetches surface a hard **SYNTHETIC FALLBACK** — not claimed as empirical.

---

## Dashboard

Interactive local / Vercel UI:

- Autoscaling **price** + **Λ** charts with **observed market overlay** (secondary axis)
- Live narrator, firm table, regulator alerts, scratchpad viewer
- Demand shock mid-run · empirical Λ comparison panel · end-of-run verdict

---

## Stack

| Layer | Choice |
|-------|--------|
| Runtime | Python 3.10+, FastAPI, Uvicorn, WebSockets |
| Models | Groq Allam 2 · Q-Learning · NumPy DQN · Hybrid RAG |
| Embeddings | Ollama `nomic-embed-text` (optional) |
| Data | BLS/FRED, CoinGecko, Pandas |
| Infra | Docker Compose · Postgres/pgvector · n8n |
| UI | HTML/CSS/JS · Chart.js · Vercel demo |

---

## Repo map

```text
market/          MNL demand, Nash/monopoly, game loop
agents/          Heuristic, RL, DQN, LLM (Groq), RAG
regulator/       Λ monitor, NLP cluster, sentiment, shocks
data_loaders/    MarketContext + 5 market adapters
database/        schema, logger, pgvector memory
analysis/        figures, RF classifier, forecaster, real_data
dashboard/       landing + live app + demo trajectories
n8n/             collusion alert workflow
api_server.py    WebSocket stream + REST + webhooks
run_simulation.py · start_echo.ps1 · docker-compose.yml
```

---

## References

Calvano et al. (2020) *AER* · Fish et al. (2025) LLM collusion · Mnih et al. (2015) DQN · Anderson et al. (1992) discrete choice · Eckert (2013) gasoline

---

<div align="center">

**Aryan Raj** · [@ARYANRAJ1121](https://github.com/ARYANRAJ1121)

[MIT License](LICENSE) · [Live demo](https://echo-green-pi.vercel.app)

</div>
