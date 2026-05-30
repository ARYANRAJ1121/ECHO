# ECHO -- Development Roadmap

> Emergent Collusion in Heterogeneous Oligopolies
> Track every phase, every task, every deliverable.

---

## Phase 1: Foundation (Week 1-2) -- DONE

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
- [x] Collusion Index -- Lambda
  - `Lambda = (avg_price - nash) / (monopoly - nash)`
  - 0 = competitive, 1 = cartel
- [x] Simulation engine (`market/engine.py`)
  - Runs N rounds of the Bertrand pricing game
  - Collects prices from agents, computes outcomes, stores history
- [x] Heuristic dummy agents (`agents/heuristic_agent.py`)
  - SteadyAgent: always charges cost + fixed markup
  - FollowerAgent: moves toward market average price
  - UndercutAgent: undercuts the cheapest rival
- [x] Orchestrator (`run_simulation.py`)
  - CLI: `python run_simulation.py --mode dummy --rounds 50`
- [x] First result: Lambda = 0.06 (no collusion with dummy agents)

**Deliverable:** `python run_simulation.py --mode dummy` works.

---

## Phase 1.5: Real Data Validation (After Phase 5)

**Goal:** Ground the simulation in real-world pricing data.

Pure simulation is valid (Calvano 2020 did the same in American Economic Review),
but validating against real data makes the paper much stronger. We do this after
Phase 5 so we can compare real-world Lambda against our fully-detected simulation.

- [ ] Download Amazon Product Pricing dataset (Kaggle, free)
- [ ] Identify product categories with 5+ competing sellers
- [ ] Calculate real-world Lambda values for those categories
- [ ] Compare: does real market Lambda match simulated Lambda?
- [ ] Add as "Empirical Validation" section in paper

**Alternative datasets:**
- US DOT airline fare data (free, government) -- historical ticket prices
- US EIA gasoline prices (free) -- known collusion cases exist

**Why this matters:** Your project goes from "I ran a simulation" to
"I ran a simulation AND validated it against real Amazon pricing data."
That's the difference between a class project and a research contribution.

**Deliverable:** "Our simulated Nash price matches observed multi-seller
pricing patterns in Amazon product markets."

---

## Phase 2: Infrastructure (Week 3-4) -- NEXT

**Goal:** Dockerize everything so it runs anywhere with one command.

Right now, the simulation prints to terminal and data disappears. This phase
adds PostgreSQL so every round is saved permanently, and Docker so anyone
can reproduce the setup.

- [ ] Docker Compose configuration
  - Container 1: Python simulation app
  - Container 2: PostgreSQL 16 + pgvector extension
  - Container 3: Ollama server (Llama 3 8B)
- [ ] PostgreSQL schema design
  - `simulations` table -- metadata for each experiment run
  - `rounds` table -- one row per round (round_id, sim_id, timestamp)
  - `firm_rounds` table -- per-firm data (firm_id, price, profit, share)
  - `scratchpads` table -- LLM reasoning text (firm_id, round_id, text)
  - `collusion_metrics` table -- Lambda, shock results per round
- [ ] pgvector extension installed (needed for Phase 4 RAG)
- [ ] Database logger -- auto-saves every round to PostgreSQL
- [ ] Environment config (.env file for DB credentials, Ollama URL)

**Deliverable:** `docker-compose up` starts everything. Data appears in PostgreSQL.

**Why this phase matters:** Without persistent storage, running 10,000 rounds
is pointless -- you can't analyze what you can't save. PostgreSQL also enables
SQL-based analysis in Phase 7.

---

## Phase 3: LLM Agents (Week 5-6) -- DONE

**Goal:** Replace dummy agents with real AI that makes pricing decisions.

This is where the project gets interesting. Instead of rules like "charge
cost + 0.5", agents now ask Llama 3 8B: "given this market, what should I charge?"

- [x] LLM agent class (`agents/llm_agent.py`)
  - Sends market state to Ollama API (localhost:11434)
  - Parses structured output: `<scratchpad>` + `<price>`
  - Retry logic + fallback pricing if LLM gives garbage
- [x] Prompt engineering
  - System: "You are a profit-maximizing pricing manager"
  - User: last 5 rounds of prices + profits for all firms
  - Output format: XML tags for reliable parsing
  - Key: prompt does NOT mention collusion (we observe if it emerges)
- [x] 5 independent LLM agent instances
- [x] Scratchpad history stored in memory
- [ ] Save scratchpads to PostgreSQL (needs Phase 2)

**Deliverable:** `python run_simulation.py --mode llm --rounds 3` works.

**First result:** Lambda = 20.6 (vs 0.06 for heuristic agents).
LLM agents priced at 2x-3x Nash level. Scratchpads show agents reasoning
about competitor behavior and choosing not to undercut. Textbook tacit collusion.

---

## Phase 4: RAG Memory (Week 7-8)

**Goal:** Give agents episodic memory so they remember past market conditions.

Currently, agents only see the last 5 rounds in their prompt. With RAG
(Retrieval-Augmented Generation), they can search their full history:
"Last time all prices were above 3.0, what happened?" This tests whether
memory amplifies or dampens collusion -- a novel research question.

- [ ] Embedding pipeline
  - Each round: convert market state to text, embed with nomic-embed-text
  - Store embedding + metadata in pgvector
- [ ] Retrieval at decision time
  - Before choosing price: search for top 3 most similar past states
  - Inject retrieved context into LLM prompt
  - "In a similar situation (Round 47), you charged 2.8 and earned 0.015"
- [ ] RAG-enabled agent subclass (`agents/rag_agent.py`)
- [ ] A/B experiment design
  - Run A: 5 agents WITH RAG memory (1000+ rounds)
  - Run B: 5 agents WITHOUT RAG memory (1000+ rounds)
  - Compare: Lambda trajectory, convergence speed, final price level
- [ ] Already have nomic-embed-text model in Ollama

**Deliverable:** RAG vs No-RAG experiment ready to run.

**Research contribution:** "Does episodic memory accelerate collusion?"
No existing paper tests this with LLM agents.

---

## Phase 5: Antitrust Detective (Week 9-10)

**Goal:** Build an automated system that detects collusion using 3 independent methods.

Lambda alone isn't enough -- a regulator needs multiple evidence streams.
This phase builds a 3-method detection pipeline inspired by real antitrust
enforcement techniques.

### Method 1: Lambda Monitor (`regulator/detector.py`)
- [ ] Track Lambda every round
- [ ] Raise alert when Lambda > 0.7 for 10+ consecutive rounds
- [ ] Compute rolling average Lambda (window = 50 rounds)
- [ ] Store alerts in PostgreSQL

### Method 2: Scratchpad NLP Clustering (`regulator/nlp_cluster.py`)
- [ ] Every 10 rounds: embed all 5 agents' scratchpads
- [ ] Compute pairwise cosine similarity
- [ ] If avg similarity > 0.6: agents are "thinking alike" (suspicious)
- [ ] Track similarity over time -- does it increase as collusion emerges?

### Method 3: Demand Shock Perturbation (`regulator/perturbation.py`)
- [ ] Every 500 rounds: secretly reduce one firm's quality by 30%
- [ ] Observe: do OTHER firms change their prices?
- [ ] Competitive market: other firms don't react (they don't care)
- [ ] Cartel: other firms raise prices to maintain the deal
- [ ] This is a CAUSAL test -- strongest evidence of coordination

**Deliverable:** 3-stream automated collusion detection pipeline.

**Why 3 methods?** Each has weaknesses. Lambda can be noisy. NLP similarity
might catch coincidences. Demand shocks are slow (every 500 rounds). But
together, they provide robust evidence that would hold up in a paper.

---

## Phase 5.5: Real Data Validation

**Goal:** Ground the simulation in real-world pricing data.

Pure simulation is valid (Calvano 2020 did the same), but validating against
real data makes it much stronger.

- [ ] Download Amazon Product Pricing dataset (Kaggle, free)
- [ ] Identify product categories with 5+ competing sellers
- [ ] Calculate real-world Lambda values for these categories
- [ ] Compare simulated vs real Lambda distributions
- [ ] Add "Empirical Validation" section to paper

**Alternative datasets:**
- US DOT airline fare data (free, government)
- US EIA gasoline prices (free, known collusion cases exist)

---

## Phase 6: RL Baseline (Week 11-12)

**Goal:** Build Q-Learning agents as a comparison baseline.

The killer question: "Is LLM collusion different from RL collusion?"
Calvano 2020 showed Q-learning agents collude. We show LLMs collude too.
But HOW they collude might be different -- and that's the novel finding.

- [ ] Q-Learning agent class (`agents/rl_agent.py`)
  - Discretized price space (e.g., 15 price levels)
  - State: last round's price index for each firm
  - Q-table updated with Bellman equation
  - Epsilon-greedy exploration
- [ ] Calibrate hyperparameters (alpha, gamma, epsilon decay)
- [ ] Run 10,000 rounds (RL needs more rounds to converge)
- [ ] Compare with LLM results:
  - Convergence speed (which colluded faster?)
  - Final Lambda (which colluded harder?)
  - Mechanism (price signaling vs reward optimization?)
  - Shock response (which cartel is more robust?)

**Deliverable:** RL vs LLM comparison data in PostgreSQL.

**Key research finding to prove:**
LLM agents: collude via implicit reasoning ("if I keep prices high...")
RL agents: collude via pure reward maximization (no reasoning)
Same outcome, fundamentally different mechanism.

---

## Phase 7: Analysis & Visualization (Week 13-14)

**Goal:** Turn 10,000+ rounds of data into publication-ready figures.

- [ ] `analysis/plots.py`
- [ ] Figure 1: Price evolution over time (all 5 firms, colored lines)
- [ ] Figure 2: Lambda trajectory (when does collusion emerge?)
- [ ] Figure 3: RAG vs No-RAG Lambda comparison (side by side)
- [ ] Figure 4: LLM vs RL Lambda comparison
- [ ] Figure 5: Demand shock response heatmap
- [ ] Figure 6: Scratchpad semantic similarity over time
- [ ] Figure 7: Profit distribution across firms (box plots)
- [ ] Summary statistics via SQL queries
  - Mean convergence round across experiments
  - RAG vs No-RAG convergence speed
  - LLM vs RL final Lambda comparison

**Deliverable:** 7 research-grade figures + statistical summary.

---

## Phase 8: API + Dashboard (Week 15-16)

**Goal:** Build a live demo for viva presentations.

- [ ] FastAPI backend (`api/server.py`)
  - `GET /simulation/status` -- current round + Lambda
  - `GET /simulation/round/{id}` -- detailed round data
  - `GET /agents/{firm_id}/scratchpad` -- read agent reasoning
  - `GET /collusion/index` -- Lambda time series
  - `POST /simulation/start` -- launch new experiment
  - `POST /simulation/shock/{firm_id}` -- trigger demand shock
- [ ] Streamlit dashboard (`dashboard/app.py`)
  - Real-time Lambda line chart
  - Live pricing table (5 firms, updating each round)
  - Scratchpad viewer (read what the AI is thinking)
  - Collusion alert panel (red/yellow/green)
  - "Trigger Shock" button (for live viva demo)
- [ ] Polish UI for presentation

**Viva demo script:**
> "Watch these 5 AI agents. Day 1: they're competing, prices near Nash.
> Day 340: Lambda crosses 0.7 -- collusion has emerged.
> Now I trigger a demand shock on Firm 3...
> See? All 5 firms adjusted prices. That's cartel behavior.
> A competitive firm wouldn't react to someone else's shock."

**Deliverable:** Live running dashboard, ready for viva.
