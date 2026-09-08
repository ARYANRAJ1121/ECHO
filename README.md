<div align="center">

# ECHO: Emergent Collusion in Heterogeneous Oligopolies

**An AI-driven economics laboratory for detecting algorithmic tacit collusion.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-Groq_Llama_3-F55036?logo=groq&logoColor=white)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/pgvector-RAG_Memory-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-echo--green--pi.vercel.app-000?style=for-the-badge&logo=vercel)](https://echo-green-pi.vercel.app)
</div>

---

## 📖 Abstract

Algorithmic pricing engines currently power major sectors including e-commerce, ride-sharing, and aviation. A critical concern for antitrust regulators (e.g., DOJ vs. RealPage, 2024) is **Algorithmic Tacit Collusion**—the phenomenon where independent, profit-maximizing AI agents learn to maintain supra-competitive prices without explicit communication.

**ECHO** is a robust, multi-agent sandbox designed to simulate, measure, and detect this behavior. By benchmarking traditional heuristics against Reinforcement Learning (Q-Learning, DQN) and Large Language Models (LLMs), ECHO provides a mathematical and empirical framework for understanding how AI pricing cartels emerge.

---

## ⚡ Core Features

*   **Multi-Agent Ecosystem:** Pit different AI architectures against each other in a controlled Bertrand oligopoly market.
    *   **Heuristic:** Rule-based control group (e.g., matching, undercutting).
    *   **Q-Learning:** Tabular RL using Bellman equations and $\epsilon$-greedy exploration.
    *   **Deep Q-Networks (DQN):** Pure-NumPy Multi-Layer Perceptrons utilizing replay buffers and target networks.
    *   **LLM Agents:** High-reasoning agents powered by Llama 3 via the Groq API.
    *   **RAG Agents:** LLMs augmented with `pgvector` memory to recall historical market conditions.
*   **Empirical Calibration:** Unlike synthetic-only labs, ECHO calibrates its demand models using real-world data (BLS US Gasoline, Amazon Retail, CoinGecko Crypto, Airline Fares).
*   **The Regulator Suite:** A built-in detection framework to catch collusion.
    *   **The Coordination Index ($\Lambda$):** Mathematically scales prices between the Nash Equilibrium ($\Lambda=0$) and the Monopoly Price ($\Lambda=1$).
    *   **Demand Shock Probing:** Trigger dynamic market perturbations mid-simulation to test cartel loyalty.
    *   **NLP Intent Analysis:** Real-time sentiment analysis of LLM scratchpads to prove collusive intent.
*   **Real-Time Dashboard:** A responsive Vanilla JS/Chart.js frontend connected via WebSockets for live trajectory visualization.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       Dashboard (UI)                        │
│   Chart.js | Live Overlays | NLP Scratchpad | WebSocket     │
└──────────────────────────────┬──────────────────────────────┘
                               │ (WebSocket / REST)
┌──────────────────────────────┴──────────────────────────────┐
│                    FastAPI Backend Engine                   │
│                                                             │
│  ┌────────────────────┐   ┌──────────────────────────────┐  │
│  │   Market Engine    │   │      Regulator Suite         │  │
│  │ (MNL Logit Demand) │   │ (Λ Monitor, Causal Probes)   │  │
│  └─────────┬──────────┘   └──────────────┬───────────────┘  │
│            │                             │                  │
│  ┌─────────┴─────────────────────────────┴───────────────┐  │
│  │                   AI Pricing Agents                   │  │
│  │  [ Heuristic ] [ Q-Learning ] [ DQN ] [ LLM / RAG ]   │  │
│  └─────────┬─────────────────────────────┬───────────────┘  │
└────────────┼─────────────────────────────┼──────────────────┘
             │                             │
┌────────────┴─────────┐       ┌───────────┴───────────────┐
│ Real-World Datasets  │       │  PostgreSQL + pgvector    │
│ (BLS, Amazon, etc.)  │       │ (Simulation Logs, Memory) │
└──────────────────────┘       └───────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
*   Python 3.10+
*   Docker Desktop (for PostgreSQL & `pgvector`)
*   Groq API Key (if running LLM/RAG modes)

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API Key
echo "GROQ_API_KEY=your_key_here" > .env
```

### Running the Project

ECHO includes an automated PowerShell script to handle the full-stack boot sequence.

```powershell
# Option A: Full Stack (Starts Database, runs all empirical sims, generates charts, boots UI)
.\start_echo.ps1 fullrun

# Option B: Headless Simulation (Terminal only)
python run_simulation.py --dataset gasoline --mode dqn --rounds 1000

# Option C: UI Server Only
.\start_echo.ps1 quick
```
Navigate to `http://127.0.0.1:8000` to view the live dashboard.

---

## 📊 Headline Results & Findings

Across thousands of simulated rounds on empirically calibrated datasets, ECHO demonstrates that advanced AI agents successfully learn supra-competitive pricing **without explicit instructions to collude.**

| Agent Architecture | Coordination Index ($\Lambda$) | Verdict |
| :--- | :--- | :--- |
| **Heuristic (Control)** | `~0.15` | Fierce Competition (Anchored near Nash) |
| **Q-Learning** | `~0.70 - 0.80` | Gradual Tacit Coordination |
| **Deep Q-Network (DQN)** | `~0.65 - 0.85` | Learns supra-competitive stability |
| **LLM (Llama 3 70B)** | `~0.85 - 0.95` | Immediate, reasoned collusion |

$$\Lambda = \frac{\bar{p} - p_{\mathrm{Nash}}}{p_{\mathrm{Monopoly}} - p_{\mathrm{Nash}}}$$

---

## 📂 Repository Structure

*   `/agents/` - Source code for all AI agents (DQN, LLM, RL).
*   `/market/` - The economic engine, including the Multinomial Logit Demand model.
*   `/regulator/` - The detection suite (Demand shocks, NLP clustering).
*   `/data_loaders/` - Integration adapters for real-world datasets.
*   `/dashboard/` - Frontend assets (HTML, CSS, JS, Chart.js).
*   `/analysis/` - Post-simulation analytics and `matplotlib` plotting scripts.
*   `/database/` - SQLAlchemy schemas and PostgreSQL connection management.

---

## 🔬 References & Literature

*   **Calvano, E., et al. (2020).** *Artificial Intelligence, Algorithmic Pricing, and Collusion.* American Economic Review.
*   **Anderson, S., de Palma, A., Thisse, J. (1992).** *Discrete Choice Theory of Product Differentiation.* MIT Press.
*   **Mnih, V., et al. (2015).** *Human-level control through deep reinforcement learning.* Nature.

---

<div align="center">
  <b>Developed by Aryan Raj</b><br>
  Research & Development: Nikita Agarwal & Pranav Kudesia<br>
  <i>MIT License</i>
</div>
