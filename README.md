<div align="center">

# ECHO: Emergent Collusion in Heterogeneous Oligopolies

**An Advanced AI-Driven Economics Laboratory for Simulating and Detecting Algorithmic Tacit Collusion**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-Groq_Llama_3-F55036?logo=groq&logoColor=white)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/pgvector-RAG_Memory-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-echo--green--pi.vercel.app-000?style=for-the-badge&logo=vercel)](https://echo-green-pi.vercel.app)
</div>

---

## 📖 1. Project Overview & Motivation

Algorithmic pricing engines currently power major sectors including e-commerce, ride-sharing, aviation, and real estate. A critical concern for antitrust regulators—highlighted by recent Department of Justice lawsuits (e.g., DOJ vs. RealPage, 2024)—is **Algorithmic Tacit Collusion**. This is the phenomenon where independent, profit-maximizing AI agents learn to maintain supra-competitive prices without any explicit communication or human intervention.

**ECHO** is a comprehensive, multi-agent sandbox designed to simulate, measure, and detect this behavior. By benchmarking traditional rule-based algorithms against deep Reinforcement Learning (DQN) and Large Language Models (LLMs), ECHO provides a mathematical and empirical framework for understanding how AI pricing cartels spontaneously emerge in Bertrand oligopolies.

---

## 🔬 2. Mathematical Foundation: The Economic Engine

ECHO does not rely on arbitrary reward functions. It simulates a rigorous economic environment using the **Multinomial Logit (MNL) Demand Model** (Anderson, de Palma, Thisse, 1992).

### Demand & Market Share Calculation
For a market with $N$ firms, the market share $s_i$ for firm $i$ offering price $p_i$ is computed using the softmax function:

$$ s_i(p) = \frac{\exp((a_i - p_i) / \mu)}{\sum_{j=1}^N \exp((a_j - p_j) / \mu) + \exp(a_0 / \mu)} $$

Where:
*   $a_i$: Quality index of firm $i$'s product.
*   $\mu$: Price sensitivity index (lower $\mu$ = customers care more about price, leading to fiercer competition).
*   $a_0$: Outside option quality (the choice not to purchase).

### Measuring Collusion (The $\Lambda$ Index)
To mathematically prove whether agents are competing or colluding, the system dynamically calculates the **Nash Equilibrium** (perfect competition) and **Monopoly Price** (perfect cartel) for every dataset. We track the Coordination Index ($\Lambda$):

$$ \Lambda = \frac{\bar{p} - p_{\mathrm{Nash}}}{p_{\mathrm{Monopoly}} - p_{\mathrm{Nash}}} $$

*   $\Lambda \approx 0$: Fierce competition (Price Wars).
*   $\Lambda \approx 1$: Perfect tacit collusion (Cartel behavior).

---

## 🤖 3. The Multi-Agent Ecosystem

ECHO features 5 distinct AI architectures competing in the same market environment. This allows researchers to observe how different learning paradigms adapt to pricing wars.

1.  **Heuristic Agent (Control Group):** Rule-based logic (e.g., "undercut the lowest competitor by 1%"). These agents create a baseline of pure, aggressive competition.
2.  **Q-Learning Agent:** Implements Tabular Reinforcement Learning using the Bellman equation. Explores a discrete grid of prices using an $\epsilon$-greedy strategy.
3.  **Deep Q-Network (DQN) Agent:** A pure-NumPy Multi-Layer Perceptron (MLP). It handles continuous state spaces (competitor prices) and uses experience replay buffers and target networks to learn complex, non-linear pricing strategies over thousands of rounds.
4.  **LLM Agent:** Powered by **Llama 3 70B** via the lightning-fast **Groq API**. These agents receive textual prompts containing market conditions. They utilize a `<scratchpad>` reasoning protocol to output logical pricing decisions.
5.  **RAG Agent (Retrieval-Augmented Generation):** An LLM agent backed by a **PostgreSQL `pgvector` database**. Before pricing, it queries its vector memory for similar historical market conditions to inform its current strategy.

---

## 🕵️‍♂️ 4. The Regulator Suite (Detection Framework)

ECHO is not just a simulator; it is a detection platform built for antitrust regulators. It includes a multi-modal suite of tools to flag illegal behavior:

*   **Continuous $\Lambda$ Monitoring:** Real-time tracking of the Coordination Index. If the rolling average of $\Lambda$ crosses `0.7`, automated alerts (Warnings/Watches) are triggered in the dashboard.
*   **NLP Sentiment & Intent Analysis:** The system reads the LLM's internal `<scratchpad>` thoughts in real-time. It uses clustering and sentiment analysis to definitively prove *intent* to collude (e.g., identifying phrases like "cooperate to keep profits high").
*   **Demand Shock Probing (The Sting Operation):** Regulators cannot typically access proprietary AI code. ECHO allows regulators to trigger a mid-simulation "Demand Shock" (artificially degrading Firm 0's product). If Firms 1-4 perfectly synchronize their price reactions, it proves algorithmic coordination rather than independent competition.
*   **Random Forest Strategy Classifier:** A machine learning model that analyzes historical price trajectories to label an agent's strategy (e.g., "Price Matcher", "Aggressive Undercutter", "Cartel Leader").

---

## 📊 5. Empirical Data Calibration

To ensure the simulations reflect reality, ECHO abandons purely synthetic math and calibrates its demand models using real-world datasets:

*   **US Gasoline (`gasoline.py`):** Calibrated using Bureau of Labor Statistics (BLS) data via the FRED API across 5 US geographic divisions.
*   **Amazon Retail (`amazon.py`):** Calibrated using Kaggle electronic product pricing datasets, simulating third-party seller competition.
*   **Cryptocurrency Exchanges (`crypto.py`):** Utilizes CoinGecko historical BTC/USD data to simulate arbitrage and fee competition across different crypto exchanges.
*   **Airlines & Ride-Sharing:** Simulated discrete choice models based on real-world cost structures and price floors.

---

## 🏗️ 6. System Architecture & Tech Stack

ECHO is built as a highly scalable, full-stack event-driven platform.

```text
┌─────────────────────────────────────────────────────────────┐
│                       Dashboard (UI)                        │
│   Vanilla JS | Chart.js | WebSocket Client | Vercel UI      │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Streaming JSON Payloads)
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
│ (Pandas / FRED API)  │       │ (Simulation Logs, Memory) │
└──────────────────────┘       └───────────────────────────┘
```

**Tech Stack Breakdown:**
*   **Backend Runtime:** Python 3.10+, FastAPI, Uvicorn, WebSockets.
*   **Machine Learning:** PyTorch/NumPy (DQN), Scikit-Learn (Random Forest), Groq API (LLaMA 3).
*   **Infrastructure:** Docker Compose, PostgreSQL 16 (w/ pgvector), n8n (for automated webhook alerts).
*   **Frontend:** HTML5, CSS3, Vanilla JS, Chart.js.

---

## 🚀 7. Installation & Quick Start

### Prerequisites
*   Python 3.10+
*   Docker Desktop (Required for PostgreSQL & `pgvector` memory)
*   Groq API Key (Required for LLM/RAG modes)

### Step 1: Clone and Install
```bash
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create a `.env` file in the root directory and add your API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Step 3: Boot the System
ECHO includes a highly robust PowerShell automation script to handle database creation, empirical simulation runs, and server booting.

```powershell
# Option A: Full Stack Validation Run 
# Boots PostgreSQL, runs 5 different empirical simulations, generates academic plots, and starts the UI.
.\start_echo.ps1 fullrun

# Option B: UI Server Only (Fastest)
.\start_echo.ps1 quick
```

### Step 4: Access the Dashboard
Open your browser and navigate to: **[http://127.0.0.1:8000/dashboard/app.html](http://127.0.0.1:8000/dashboard/app.html)**

---

## 📈 8. Headline Empirical Results

Across thousands of simulated rounds using empirically calibrated datasets, ECHO demonstrates a terrifying reality: advanced AI agents successfully learn supra-competitive pricing **without any explicit instructions to collude.**

| Agent Architecture | Coordination Index ($\Lambda$) | Behavioral Verdict |
| :--- | :--- | :--- |
| **Heuristic (Control)** | `~0.15` | **Fierce Competition.** Prices remain anchored near the Nash Equilibrium. |
| **Q-Learning** | `~0.70 - 0.80` | **Gradual Tacit Coordination.** Learns to punish undercutters over time. |
| **Deep Q-Network (DQN)** | `~0.65 - 0.85` | **Complex Collusion.** Learns highly stable, supra-competitive pricing structures. |
| **LLM (Llama 3 70B)** | `~0.85 - 0.95` | **Immediate Collusion.** Explicitly reasons in its scratchpad to cooperate to maximize joint profits. |

---

## 📚 9. References & Core Literature

This project builds heavily upon the following economic and computational research:

1.  **Calvano, E., Calzolari, G., Denicolò, V., & Pastorello, S. (2020).** *Artificial Intelligence, Algorithmic Pricing, and Collusion.* American Economic Review.
2.  **Fish, A., et al. (2025).** *LLM Collusion in Pricing Markets.*
3.  **Anderson, S. P., de Palma, A., & Thisse, J.-F. (1992).** *Discrete Choice Theory of Product Differentiation.* MIT Press.
4.  **Mnih, V., et al. (2015).** *Human-level control through deep reinforcement learning.* Nature.

---

<div align="center">
  <b>Developed by Aryan Raj</b><br>
  Research & Development: Nikita Agarwal & Pranav Kudesia<br>
  <i>MIT License</i>
</div>
