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

## Phase 16: Dataset loaders (complete)

Calibrate the Bertrand stage game from named markets rather than a single toy parameter set.

- [x] `MarketContext` and `MarketDataLoader` (`data_loaders/base.py`)
- [x] US gasoline — BLS via FRED, five census divisions (`data_loaders/gasoline.py`)
- [x] Crypto — CoinGecko BTC/USD across five venues (`data_loaders/crypto.py`)
- [x] Amazon — local CSV, wireless earbuds (`data_loaders/amazon.py`)
- [x] Indian airlines — static DEL–BOM parameters (`data_loaders/airlines.py`)
- [x] Ride-sharing — static Uber/Lyft-style surge parameters (`data_loaders/rideshare.py`)
- [x] `get_data_loader()` factory; `--dataset` on `run_simulation.py` (default: gasoline)
- [x] All `build_*` paths consume `market_ctx`; live fetch failure is flagged, not silent
- [x] Dashboard dataset selector; WebSocket forwards `dataset` to FastAPI
- [x] `dataset_name` on `simulations`; n8n templates include dataset context
- [x] `start_echo.ps1` fullrun uses `--dataset gasoline`
- [x] Figure titles include the dataset name
- [x] `scipy` in `requirements.txt`

Example: `python run_simulation.py --dataset crypto --mode dummy --rounds 50`

---

## Future work

These items are **out of scope for the submitted major project**. They form a research and engineering backlog if ECHO is extended toward a publication-grade laboratory. Heterogeneous **marginal costs** are already in the engine; remaining F2 items are listed for completeness.

---

### F1. Cross-model LLM evaluation

Compare tacit coordination under a **common market protocol** across hosted and local language models (Groq Allam 2 7B today; additional Groq or OpenAI-compatible endpoints; optional local Ollama chat).

- [ ] Pluggable LLM backend behind `LLMPricingAgent`
- [ ] Identical seeds, round count, and `MarketContext` per model family
- [ ] Report time-to-threshold, peak and terminal Λ, and scratchpad intent rates
- [ ] Optional mixed-architecture oligopoly (two model families in one market)

**Rationale.** Establish whether high Λ is an artefact of one 7B checkpoint or a broader property of language-model pricers.

---

### F2. Richer firm heterogeneity

- [x] Firm-specific marginal costs (`MarketContext.marginal_costs`)
- [ ] Firm-specific quality as an experimental factor
- [ ] Capacity constraints and rationing
- [ ] Exit when continuation value is negative
- [ ] Mixed agent classes in one run (for example DQN majors versus heuristic undercutters) as a first-class dashboard mode

**Research question.** Does asymmetry destabilise tacit coordination, or does it only reassign price leadership?

---

### F3. Multi-product demand

Extend multinomial logit demand from a single good to a small product portfolio with cross-elasticities and optional bundling, so coordination can be studied across categories rather than one fare or one SKU.

- [ ] Simultaneous pricing of several products per firm
- [ ] Cross-elasticity / nested logit (or equivalent)
- [ ] Bundling and loss-leader experiments
- [ ] Measure whether high Λ on one product spills into another

---

### F4. Information structure

Hold the stage game fixed and vary what agents observe.

| Protocol | Information set |
|----------|-----------------|
| Baseline (current) | Posted prices and profits only |
| Public announcements | Intended next-round prices |
| Private messages | Bilateral cheap talk |
| Shared scratchpads | LLM reasoning visible to rivals |

**Research question.** How do Λ and time-to-alert change as the information structure moves from tacit to explicit?

---

### F5. Non-stationary markets

- [ ] Seasonal or trending `market_size` / μ
- [ ] Cost or quality shocks that are not the regulator sting
- [ ] Mid-run entry of an additional firm
- [ ] Robustness of learned high-price equilibria under those perturbations

---

### F6. Policy counterfactuals

Instrument the engine with optional constraints and compare Λ and consumer-side outcomes (outside share, average price versus Nash):

- price ceilings
- delayed public transparency
- leniency / first-defector bonus
- mandatory textual justification (LLM modes)
- forced split of the agent pool

This remains a **laboratory** for CCI- and DOJ-style questions. Λ is an index, not a court finding.

---

### F7. Graph-based detection

Represent firms as nodes and contemporaneous price (or scratchpad) similarity as edges. Train a temporal graph model to classify market regimes and to rank likely price leaders; report accuracy against Λ-based labels and against the current Random Forest.

- [ ] Static and temporal graphs of the oligopoly
- [ ] Regime classification (competitive / watch / collusive)
- [ ] Leadership ranking versus `identify_cartel_roster()`
- [ ] Ablation versus LambdaMonitor + RF

---

### F8. Linked markets

Several Bertrand markets with overlapping firms and demand spillovers, to study whether coordination in one geography or product line transmits to another (motivated by multi-market algorithmic pricing, including RealPage-style settings).

---

### F9. Additional market telemetry

Periodic ingestion of further public series **beyond** the existing FRED, CoinGecko, and CSV loaders, with an explicit provenance flag. Overlays remain **calibration and comparison**; dashboard ticks are simulated Bertrand prices, not live exchange matches. Any retailer crawl must respect robots.txt and terms of service, or be omitted.

---

### F10. Explainability for non-specialist readers

- [ ] SHAP (or equivalent) attributions on the strategy classifier
- [ ] Structured narrative reports grounded in Nash, monopoly, Λ, and shock response
- [ ] Simple counterfactuals (if firm *i* had priced at Nash…)
- [ ] Keep LLM-as-judge **off** the official collusion metric

---

### F11. Dashboard hardening

Responsive layout, optional PWA, and tighter mobile chart UX. Secondary to the research extensions above.

---

### F12. Reproducibility, evaluation, and observability

- [ ] JSON/YAML experiment manifests and fixed seeds
- [ ] Welfare / consumer-surplus style supplements to Λ
- [ ] CI for unit tests on demand, band calibration, and roster logic
- [ ] Optional **LangSmith or Langfuse** on Groq generations (latency, parse success, cost). Λ remains the economic score.

---

### Indicative priority

| Priority | Item | Effort | Expected contribution |
|----------|------|--------|------------------------|
| High | F1 Cross-model LLM evaluation | Medium | External validity of LLM collusion |
| High | F6 Policy counterfactuals | Medium | Maps the lab to enforcement questions |
| Medium | F2 Remaining heterogeneity and mixed agents | Medium | Closer industry structure |
| Medium | F4 Information structure | Medium | Tacit versus explicit coordination |
| Medium | F5 Non-stationary demand | Low | Robustness of high-Λ equilibria |
| Medium | F10 Explainability | Medium | Readable evidence packs |
| Medium | F12 Reproducibility and LLM tracing | Medium | Credible experiments |
| Lower | F3 Multi-product demand | High | Broader IO realism |
| Lower | F7 Graph detection | High | Alternative detector |
| Lower | F8 Linked markets | High | Contagion of coordination |
| Lower | F9 Additional live feeds | Medium | Richer overlays |
| Lower | F11 Mobile dashboard | Low | Presentation polish |

---

*Last updated: September 2026*
