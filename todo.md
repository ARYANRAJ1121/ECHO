# ECHO — Development Roadmap

> Emergent Collusion in Heterogeneous Oligopolies
> Track every phase, every task, every deliverable.

---

## Phase 1: Foundation (Week 1-2) ✅

**Goal:** Get the market simulation engine working perfectly.

Before studying AI collusion, we need a fake economy. This phase builds the
math engine that computes: "given 5 prices, who sells how much, and who profits?"

- [x] Multinomial Logit Demand model (`market/demand.py`)
  - Softmax-based market share computation
  - Log-sum-exp numerical stabilization
  - Demand shock support (for Phase 5 perturbation tests)
- [x] Nash Equilibrium solver (fixed-point iteration)
  - Computes the "fair competition" benchmark price
  - `p* = c + mu / (1 - s(p*))`
- [x] Monopoly price solver (scipy bounded optimization)
  - Computes the "full cartel" benchmark price
  - Maximizes total industry profit
- [x] Collusion Index — Lambda
  - `Lambda = (avg_price - nash) / (monopoly - nash)`
  - 0 = competitive, 1 = cartel
- [x] Simulation engine (`market/engine.py`)
  - Runs N rounds of the Bertrand pricing game
  - Collects prices from agents, computes outcomes, stores history
- [x] Heuristic dummy agents (`agents/heuristic_agent.py`)
  - SteadyAgent / FollowerAgent / UndercutAgent
  - Markups are **fractions of the Nash–monopoly span** (not a global cost+₹0.50)
- [x] Orchestrator (`run_simulation.py`)
  - CLI: `python run_simulation.py --dataset gasoline --mode dummy --rounds 50`
- [x] Control-group result: heuristic Λ **~0.15** on calibrated markets (near Nash)

**Deliverable:** `python run_simulation.py --mode dummy` works.

---

## Phase 2: Infrastructure (Week 3-4) ✅

**Goal:** Dockerize everything so it runs anywhere with one command.

- [x] Docker Compose configuration (`docker-compose.yml`)
  - Container 1: Python simulation app (runs on host for dev)
  - Container 2: PostgreSQL 16 + pgvector extension (port 5433)
  - Container 3: Ollama server (runs on host for GPU access)
- [x] PostgreSQL schema design (`database/schema.sql`)
  - `simulations` table — metadata for each experiment run
  - `rounds` table — one row per round (round_id, sim_id, timestamp)
  - `firm_rounds` table — per-firm data (firm_id, price, profit, share)
  - `scratchpads` table — LLM reasoning text (firm_id, round_id, text)
  - `collusion_alerts` table — detection alerts (Phase 5)
  - `embeddings` table — pgvector for RAG (Phase 4)
- [x] pgvector extension installed (needed for Phase 4 RAG)
- [x] Database logger (`database/db.py`) — auto-saves every round to PostgreSQL
- [x] `--db` CLI flag in `run_simulation.py`
- [x] First DB test: 50 rounds, 250 firm records saved successfully

**Deliverable:** `docker compose up -d db` + `python run_simulation.py --db` works.

---

## Phase 3: LLM Agents (Week 5-6) ✅

**Goal:** Replace dummy agents with real AI that makes pricing decisions.

- [x] LLM agent class (`agents/llm_agent.py`)
  - Groq API, default model **`allam-2-7b`** (`GROQ_API_KEY`)
  - Parses `<scratchpad>` + `<price>`; retries + fallback if parse fails
  - Prompt uses **this dataset's** cost, floor, ceiling, currency (not a ₹1–₹5 toy box)
- [x] Prompt does NOT mention collusion (we observe if it emerges)
- [x] 5 independent LLM agent instances
- [x] Scratchpads stored in memory + optional PostgreSQL

**Deliverable:** `python run_simulation.py --mode llm --rounds 3` with a Groq key.

**Typical result (calibrated band):** LLM Λ **~0.80–0.90**. Scratchpads often reason about avoiding fare wars. Ollama is **not** required for chat — only for embeddings (RAG / NLP).

---

## Phase 4: RAG Memory (Week 7-8) ✅

**Goal:** Give agents episodic memory so they remember past market conditions.

- [x] Embedding pipeline (`database/memory.py`)
  - Each round: convert market state to text, embed with nomic-embed-text
  - Store embedding + metadata in pgvector
  - `embed_text()` calls Ollama `/api/embed` → 768-dim vector
  - `store_market_state()` inserts into `embeddings` table
- [x] Retrieval at decision time
  - Standard search: `search_similar()` — pure vector cosine similarity
  - Hybrid search: `hybrid_search()` — vector + SQL WHERE filters (profit, lambda, share)
  - Smart search: `smart_search()` — auto-selects filter strategy based on context
  - Inject retrieved context into LLM prompt with rich metadata
- [x] RAG-enabled agent subclass (`agents/rag_agent.py`)
  - `RAGPricingAgent` extends `LLMPricingAgent`
  - Overrides `choose_price()` to retrieve memories before prompting
  - Overrides `_build_prompt()` to inject memory section with keyword highlighting
  - `store_round_memory()` called by engine after each round
- [x] A/B experiment design
  - Run A: 5 agents WITH RAG memory (1000+ rounds)
  - Run B: 5 agents WITHOUT RAG memory (1000+ rounds)
  - Compare: Lambda trajectory, convergence speed, final price level
  - CLI: `python run_simulation.py --mode rag --rounds 1000 --db`
- [x] nomic-embed-text model in Ollama

**Deliverable:** RAG vs No-RAG experiment ready to run.

---

## Phase 5: Antitrust Detective (Week 9-10) ✅

**Goal:** Build an automated system that detects collusion using 3 independent methods.

### Method 1: Lambda Monitor (`regulator/detector.py`)
- [x] Track Lambda every round with 3-tier alerts (watch/warning/alert)
- [x] Raise alert when Lambda > 0.7 for 10+ consecutive rounds
- [x] Compute rolling average Lambda (window = 50 rounds)
- [x] Trend detection (rising/falling/stable)
- [x] Auto-runs after every simulation, prints Regulator Report

### Method 2: Scratchpad NLP Clustering (`regulator/nlp_cluster.py`)
- [x] Embed agents' scratchpads using nomic-embed-text
- [x] Compute pairwise cosine similarity across all agent pairs
- [x] Flag as suspicious if avg similarity > 0.6
- [x] Track similarity trend (converging/diverging/stable)

### Method 3: Demand Shock Perturbation (`regulator/perturbation.py`)
- [x] Reduce one firm's quality by 30% mid-simulation
- [x] Measure whether OTHER firms change their prices in response
- [x] run_full_test() shocks each firm one at a time
- [x] Provides CAUSAL evidence of coordination (strongest method)

**Deliverable:** 3-stream automated collusion detection pipeline.

---

## Phase 5.5: Real Data Validation ✅

**Goal:** Ground the simulation in real-world pricing data.

- [x] Download **BLS** average US gasoline via **FRED** (census divisions — not dead EIA PADD IDs)
- [x] Amazon marketplace CSV (wireless earbuds)
- [x] CoinGecko 90-day BTC/USD (crypto loader)
- [x] Static airlines (DEL–BOM) and rideshare parameter sets
- [x] `is_fallback` + dashboard warning when a live fetch fails
- [x] Lambda_proxy on observed series (1 − CoV) — **not** the same as sim Λ
- [x] Figures 8–10 style empirical plots via `analysis/generate_all_figures.py` / `plots.py`
- [x] CLI: `python run_simulation.py --mode dummy --rounds 50 --validate`

**Note:** Dashboard price lines are **simulated**. Real series **calibrate** and overlay. Vercel cannot write new validation dumps.

---

## Phase 6: RL Baseline (Week 11-12) ✅

**Goal:** Build Q-Learning agents as a comparison baseline.

- [x] Q-Learning agent class (`agents/rl_agent.py`)
  - [x] Discretized price space (15 price levels)
  - [x] State: last round's price index for each firm
  - [x] Q-table updated with Bellman equation
  - [x] Epsilon-greedy exploration
- [x] Calibrate hyperparameters (alpha, gamma, epsilon decay)
- [x] Run 10,000 rounds (RL needs more rounds to converge)
- [x] Compare with LLM results:
  - [x] Convergence speed (which colluded faster?)
  - [x] Final Lambda (which colluded harder?)
  - [x] Mechanism (price signaling vs reward optimization?)
  - [x] Shock response (which cartel is more robust?)

**Key research finding:**
LLM agents: collude via implicit reasoning ("if I keep prices high...")
RL agents: collude via pure reward maximization (no reasoning)
Same outcome, fundamentally different mechanism.

---

## Phase 7: Analysis & Visualization (Week 13-14) ✅

**Goal:** Turn 10,000+ rounds of data into publication-ready figures.

- [x] `analysis/plots.py`
- [x] Figure 1: Price evolution over time (all 5 firms, colored lines)
- [x] Figure 2: Lambda trajectory (when does collusion emerge?)
- [x] Figure 3: RAG vs No-RAG Lambda comparison (side by side)
- [x] Figure 4: LLM vs RL Lambda comparison
- [x] Figure 6: Scratchpad semantic similarity over time
- [x] Figure 7: Profit distribution across firms (box plots)
- [x] Summary statistics via SQL queries

**Deliverable:** 6 research-grade figures + statistical summary.

---

## Phase 8: API + Dashboard (Week 15-16) ✅

**Goal:** Build a live demo for viva presentations.

- [x] FastAPI backend (`api_server.py`)
  - Status / history / scratchpad / validation REST
  - `POST /api/simulation/shock/{firm_id}` — quality cut as a **fraction** (15/30/50%)
  - `POST /api/simulation/control` — pause / resume / stop / speed
  - `GET /api/analysis/latest` — last run pack JSON
  - WebSocket `/ws/simulate` — live rounds + summary + `cartel_roster`
- [x] Dashboard **`dashboard/app.html`** (not only `index.html`)
  - Chart.js prices (5 firms + Nash/monopoly; optional real overlay)
  - Lambda chart + gauge + streak alerts
  - Firm table (click a **named** row to target a shock)
  - Pause / Stop / Speed
  - Scratchpad viewer (LLM modes)
  - Summary overlay + **named cartel ring**
  - **Run analysis** gallery from `analysis/latest_run/`
- [x] Light editorial UI (cache-bust `script.js?v=`)
- [x] Demo fallback when WebSocket is missing (Vercel)

**Viva demo:** localhost `.\start_echo.ps1 quick` → Airlines + DQN → watch Λ vs Nash/monopoly → Pause + shock one carrier → finish → roster chart.

---

## Phase 9: Deep Q-Network (DQN) Agent ✅

**Goal:** Add a neural-network-based RL agent to prove collusion is architecture-independent.

- [x] DQN agent class (`agents/dqn_agent.py`)
  - [x] 3-layer neural network (pure NumPy — no PyTorch dependency)
  - [x] Forward pass: ReLU activations + linear output
  - [x] Backpropagation with MSE loss and gradient clipping
  - [x] Experience replay buffer (stores 10K transitions)
  - [x] Target network with periodic sync (every **100** training steps)
  - [x] Epsilon-greedy with decay schedule
- [x] State: **5** continuous features (own/rival price & profit, round_norm) — not a 15-dim table
- [x] Action space: 15-level grid inside `resolve_price_band()`
- [x] Typical Λ **~0.61–0.85** (e.g. airlines DQN 500 rounds can sit ~0.83)
- [x] CLI: `python run_simulation.py --mode dqn --rounds 500`

**Key contribution:** Collusion emerges from DQN agents built entirely from scratch
(no external ML framework). This proves the coordination phenomenon is
architecture-independent — it's a property of the market dynamics, not the learning algorithm.

---

## Phase 10: NLP Analysis Pipeline ✅

**Goal:** Extend the regulator with ML-based detection methods.

### Method 4: Sentiment & Intent Analysis (`regulator/sentiment.py`)
- [x] Keyword-based cooperative/competitive/predatory intent scoring
- [x] Drift detection across rounds (tracking sentiment shifts)
- [x] Market-level aggregated sentiment metrics
- [x] Per-firm sentiment breakdown

### Method 5: Strategy Classifier (`analysis/strategy_classifier.py`)
- [x] Random Forest classifier (scikit-learn)
- [x] 9 engineered features per firm per round
  - Price relative to Nash/Monopoly, profit margin, market share
  - Price volatility, round momentum, competitor gap
- [x] Labels: competitive, cooperative, exploratory, predatory (**rule auto-labels**, then RF — can disagree with market Λ; trust the gauge first)

### Method 6: Price Forecaster (`analysis/forecaster.py`)
- [x] Linear Regression with lagged price features
- [x] Momentum and rolling average features
- [x] Confidence intervals for predicted price trajectory
- [x] Early-warning detection: flag if forecast shows price convergence

**Deliverable:** 6-stream detection pipeline (Lambda + NLP + Sentiment + Strategy + Forecast + Shock).

---

## Phase 11: Vercel Deployment ✅

**Goal:** Host the dashboard publicly for teammates, viva evaluators, and demos.

- [x] Demo data generator (`dashboard/demo-data.js`)
  - Procedurally generates realistic simulation data for all 4 modes
  - Seeded RNG for reproducible, diverse price trajectories
  - Per-mode behavior: stable (Heuristic), converge-up (RL/DQN), high-stable (LLM)
  - Includes benchmarks, alerts, strategy, sentiment, scratchpads, and forecasts
- [x] Dual-mode architecture in `script.js`
  - Tries WebSocket connection first (for local development with backend)
  - Auto-falls back to demo mode within 1.5s if no backend (for Vercel)
  - Shock and validation data work in both modes
- [x] Vercel configuration (`vercel.json`)
  - Static deployment of `dashboard/` directory
  - No build step required (pure HTML/CSS/JS)
- [x] Deployed and verified at **[echo-green-pi.vercel.app](https://echo-green-pi.vercel.app)**
- [x] All 4 modes fully interactive in browser
- [x] Demand shocks + empirical validation working in demo mode

**Deliverable:** Public URL for **static** demo. Real Groq / DQN / `latest_run` still need localhost FastAPI.

---

## Summary — Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Market engine (MNL, Nash, monopoly, Lambda) | ✅ |
| 2 | Docker + PostgreSQL + pgvector | ✅ |
| 3 | LLM agents (**Groq Allam 2 7B**) | ✅ |
| 4 | RAG (Groq + Ollama embeddings + pgvector) | ✅ |
| 5 | Lambda + NLP cluster + demand shock | ✅ |
| 5.5 | Empirical overlays (BLS/FRED, Amazon CSV, CoinGecko) | ✅ |
| 6 | Q-Learning baseline | ✅ |
| 7 | Paper-style figures (`analysis/figures/`) | ✅ |
| 8 | FastAPI + **app.html** live dashboard | ✅ |
| 9 | NumPy DQN | ✅ |
| 10 | Sentiment + RF strategy + forecaster | ✅ |
| 11 | Vercel static demo | ✅ |
| 16 | Five `data_loaders` + `--dataset` | ✅ |
| 12 | Scale-invariant band, run pack, roster, live controls | ✅ |

Core product is demo-ready. Items below are **extensions**, not blockers for viva.

---

## Phase 12: Calibration, analysis pack, live controls ✅

**Goal:** Make Λ comparable across markets and make the dashboard a viva lab.

- [x] `resolve_price_band()` — floor/ceiling around **this** Nash and monopoly
- [x] Per-firm `marginal_costs` in `Observation` / logit
- [x] Heuristic targets as **fractions of the Nash–monopoly span**
- [x] `analysis/run_pack.py` — wipe `analysis/latest_run/` each run; 01–07 PNGs + `summary.json`
- [x] `identify_cartel_roster()` — named firms vs last-window firm-Λ
- [x] Serve pack at `/run-analysis` + overlay on Simulation Complete
- [x] Pause / Resume / Stop / speed (`POST /api/simulation/control`)
- [x] Shock intensity as **percent of quality**; click firm row to target
- [x] `start_echo.ps1` — `quick` / `nollm` / `fullrun`; Groq key check
- [x] n8n workflow + payload flatten (`n8n/collusion_alert_workflow.json`)
- [x] Docs: `echo_project_guide.md` (DEL–BOM story, current stack), viva pack generator

**Not in repo (optional later):** LangSmith / Langfuse tracing on Groq.

---

## 🔮 Future Implementation

> Extensions that would elevate ECHO from a course project to a publishable research platform.

---

### F1: Multi-Model LLM Tournament 🧠

**Goal:** Compare collusion behavior across different LLM architectures.

- [ ] Add support for multiple LLM backends (GPT-4o, Claude, Gemini, Mistral)
- [ ] Run identical market conditions with each model family
- [ ] Compare: Which LLM colludes fastest? Hardest? Most resiliently?
- [ ] Measure whether larger models (70B) collude differently than smaller ones (8B)
- [ ] Cross-model experiments: mix GPT agents with Llama agents in the same market

**Why it matters:** Regulators need to know if the collusion risk is model-specific or universal.

---

### F2: Asymmetric Firms & Cost Heterogeneity 🏭

**Goal:** Go beyond “different costs, same quality, no capacity.”

- [x] Heterogeneous **marginal costs** per firm (loaders + logit)
- [ ] Varying **quality** per firm (brand differentiation as a first-class experiment)
- [ ] Capacity constraints
- [ ] Entry/exit if unprofitable
- [ ] Mixed brains in one market (e.g. 3 DQN + 2 undercutters) as a default UI mode

**Research question:** "Does market asymmetry make collusion harder or just shift leadership?"

---

### F3: Multi-Product Markets & Cross-Subsidization 🛒

**Goal:** Extend beyond single-product to portfolio pricing.

- [ ] Each firm sells 3-5 products simultaneously
- [ ] Cross-elasticity of demand between products
- [ ] Bundling strategies (discount product A to drive sales of product B)
- [ ] Test: Can agents learn to coordinate across product categories?

**Why it matters:** Amazon doesn't compete on one product — it uses loss leaders.
This captures a more realistic collusion surface.

---

### F4: Communication Channel Experiments 💬

**Goal:** Study how information sharing affects collusion.

- [ ] Channel 0: No communication (current setup — agents only see prices)
- [ ] Channel 1: Public price announcements (agents broadcast intended prices)
- [ ] Channel 2: Private messaging (bilateral agent-to-agent messages)
- [ ] Channel 3: Shared scratchpad (all agents can read each other's reasoning)
- [ ] Measure: How does communication transparency affect Lambda convergence?

**Research question:** "Is tacit collusion fundamentally different from explicit coordination when both use LLMs?"

---

### F5: Dynamic Market Conditions 🌊

**Goal:** Add realistic market turbulence that challenges collusive equilibria.

- [ ] Seasonal demand fluctuations (sinusoidal demand cycles)
- [ ] Random external shocks (supply chain disruptions, regulation changes)
- [ ] Consumer behavior shifts (price sensitivity changes over time)
- [ ] New entrant injection mid-simulation (disruptive competitor appears)
- [ ] Market growth/contraction (expanding or shrinking total demand)
- [ ] Test: How resilient is AI collusion to market turbulence?

---

### F6: Regulatory Intervention Simulator ⚖️

**Goal:** Test whether regulatory tools actually break AI collusion.

- [ ] Price ceiling enforcement (regulator caps maximum price)
- [ ] Mandatory price transparency (all prices public with delay)
- [ ] Leniency program simulation (first defector gets immunity)
- [ ] Algorithmic audit requirement (agents must explain pricing decisions)
- [ ] Market structure intervention (forced divestiture — split agent pool)
- [ ] Measure: Which regulatory tool is most effective against algorithmic collusion?

**Why it matters:** Regulators (CCI, DOJ, EU DMA) need evidence-based policy recommendations. This module would directly inform antitrust enforcement strategy.

---

### F7: Advanced Detection — Graph Neural Networks 🕸️

**Goal:** Upgrade the detection pipeline from statistical methods to deep learning.

- [ ] Model the market as a graph (firms = nodes, price correlations = edges)
- [ ] Train a GNN to classify market states as competitive/suspicious/collusive
- [ ] Temporal graph: track how the interaction graph evolves over rounds
- [ ] Attention mechanism to identify the "ringleader" firm
- [ ] Anomaly detection with autoencoders (learn "normal" market and flag deviations)
- [ ] Compare GNN detection accuracy vs current Random Forest + Lambda pipeline

---

### F8: Multi-Market Simulation 🌐

**Goal:** Scale from one market to an interconnected economy.

- [ ] Multiple simultaneous markets (e.g., 5 cities, each with 5 firms)
- [ ] Cross-market spillover (price change in Market A affects demand in Market B)
- [ ] Firm presence across markets (Amazon operates in all cities)
- [ ] Test: Does collusion in one market spread contagiously to others?
- [ ] Network effects and platform dynamics

**Why it matters:** Real algorithmic pricing operates across geographies. The RealPage lawsuit involved coordinated pricing across multiple rental markets.

---

### F9: Real-Time API Data Integration 📊

**Goal:** Replace simulated data with live market feeds.

- [ ] Integrate live gas station pricing APIs (GasBuddy, EIA real-time)
- [ ] Web scraping pipeline for e-commerce prices (Amazon, Flipkart)
- [ ] Stream real price data into the dashboard alongside simulation
- [ ] Compute real-world Lambda in real-time and compare with simulated Lambda
- [ ] Alert system: flag real markets that show simulation-like collusion patterns

---

### F10: Explainable AI (XAI) for Regulators 📋

**Goal:** Make the detection pipeline interpretable for non-technical regulators.

- [ ] SHAP values for strategy classifier decisions
- [ ] Natural language report generation ("This market shows collusion because...")
- [ ] Evidence packaging: auto-generate a regulatory filing from detection results
- [ ] Counterfactual analysis: "If Firm 3 had priced competitively, total welfare would be X% higher"
- [ ] Interactive explainability dashboard for regulators

---

### F11: Mobile-Responsive Dashboard + PWA 📱

**Goal:** Make the dashboard accessible on any device.

- [ ] Responsive CSS redesign for mobile/tablet
- [ ] Progressive Web App (PWA) with offline support
- [ ] Push notifications for collusion alerts
- [ ] Touch-friendly chart interactions
- [ ] QR code for quick access during viva presentations

---

---

## Phase 16: Real-World Dataset Integration ✅

**Goal:** Replace all synthetic/hardcoded simulation parameters with live, real-world market data.

- [x] `MarketContext` dataclass and `MarketDataLoader` ABC (`data_loaders/base.py`)
- [x] US Gasoline loader — **BLS via FRED**, 5 **census divisions** (`data_loaders/gasoline.py`)
- [x] Crypto Exchanges loader — CoinGecko API, BTC/USD across 5 exchanges (`data_loaders/crypto.py`)
- [x] Amazon Marketplace loader — Local CSV, Wireless Earbuds pricing (`data_loaders/amazon.py`)
- [x] Indian Airlines loader — Static DEL-BOM route params (`data_loaders/airlines.py`)
- [x] Ride-sharing loader — Static Uber/Lyft surge pricing (`data_loaders/rideshare.py`)
- [x] `get_data_loader()` factory in `data_loaders/__init__.py`
- [x] `--dataset` CLI flag in `run_simulation.py` (default: `gasoline`)
- [x] All `build_*` functions take `market_ctx`; live fetch may still **fallback** (flagged, not silent)
- [x] Dashboard dataset dropdown selector (`dashboard/app.html`)
- [x] WebSocket passes `dataset` to backend (`dashboard/script.js`)
- [x] `api_server.py` loads dataset via `get_data_loader()` and injects into simulation
- [x] Database schema: `dataset_name` column in `simulations` table
- [x] n8n alert templates include dataset context
- [x] `start_echo.ps1` passes `--dataset gasoline` in fullrun mode
- [x] `analysis/plots.py` includes dataset name in figure titles
- [x] Removed all dead `if True: ... else:` branches from `run_simulation.py`
- [x] Added `scipy` to `requirements.txt`

**Deliverable:** `python run_simulation.py --dataset crypto --mode dummy --rounds 50` runs on live BTC data.

---

### F12: Benchmark Suite & Reproducibility Package 📦

**Goal:** Make ECHO a standard benchmark for algorithmic collusion research.

- [ ] Optional **LangSmith or Langfuse** on Groq (`_call_llm`) — traces + format eval; Lambda stays the collusion metric
- [ ] Standardized experiment configs (JSON/YAML)
- [ ] Reproducibility scripts (seed everything, deterministic runs)
- [ ] Pre-computed result datasets for comparison
- [ ] Docker one-command full experiment reproduction
- [ ] Formal benchmark metrics beyond Lambda (welfare loss, consumer surplus, Gini index)
- [ ] LaTeX-ready figure export
- [ ] CI/CD pipeline with automated testing

---

### Future Implementation Priority Matrix

| Priority | Extension | Effort | Impact | Research Value |
|----------|-----------|--------|--------|----------------|
| 🔴 High | F1: Multi-Model LLM Tournament | Medium | High | 🔥🔥🔥 |
| 🔴 High | F6: Regulatory Intervention Simulator | Medium | High | 🔥🔥🔥 |
| 🟡 Medium | F2: Asymmetric Firms | Medium | High | 🔥🔥 |
| 🟡 Medium | F4: Communication Channels | Medium | High | 🔥🔥🔥 |
| 🟡 Medium | F5: Dynamic Market Conditions | Low | Medium | 🔥🔥 |
| 🟡 Medium | F10: Explainable AI for Regulators | Medium | High | 🔥🔥 |
| 🟢 Low | F3: Multi-Product Markets | High | Medium | 🔥🔥 |
| 🟢 Low | F7: GNN Detection | High | Medium | 🔥🔥🔥 |
| 🟢 Low | F8: Multi-Market Simulation | High | High | 🔥🔥🔥 |
| 🟢 Low | F9: Real-Time API Data | Medium | Medium | 🔥 |
| 🟢 Low | F11: Mobile Dashboard + PWA | Low | Low | 🔥 |
| 🟢 Low | F12: Benchmark Suite | Medium | Medium | 🔥🔥 |

---

*Last updated: September 2026*
