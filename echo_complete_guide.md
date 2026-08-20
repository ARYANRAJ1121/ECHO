# ECHO — The Complete Project Guide
### *For Viva, Teammates, and Your Own Understanding*

---

## Part 1: The Problem (Why Does This Project Exist?)

### The Real-Life Story — Petrol Pumps

Imagine a highway with **5 petrol pumps**. Normally, they **compete**:
- Pump A charges ₹96
- Pump B charges ₹94 to steal customers
- Pump C drops to ₹92

This is **great for drivers** — prices stay low because each pump is trying to win customers from the others. Economics calls this the **Nash Equilibrium** — the fair, competitive price.

Now imagine all 5 pump owners meet in a secret room and agree: *"Let's all charge ₹120. No one undercuts. We all get rich."*

This is a **cartel** (price fixing / collusion). It's **illegal** because customers have no choice but to overpay. The CCI (Competition Commission of India) and the US DOJ actively hunt for this.

### The Scary Twist — AI Does It Without a Secret Room

Today, companies like Amazon, Uber, and airlines don't set prices manually. They use **AI algorithms** that automatically adjust prices every few minutes.

Here's the problem: **What if these AI algorithms independently learn to keep prices high, without any human telling them to collude?**

- No secret room
- No phone calls between CEOs
- No WhatsApp group
- Just 5 separate AI bots, each told "maximize your profit"
- And they **independently figure out** that keeping prices high is the best strategy

**This is called Algorithmic Collusion.** It's one of the biggest unsolved problems in technology law and economics right now.

### Our Research Question

> **Can AI agents spontaneously develop collusive pricing behavior? If yes, how do we detect and prove it?**

---

## Part 2: What Is ECHO? (The Solution)

ECHO stands for our simulation and detection platform. It has **two halves**:

```
┌─────────────────────────────────────────────────┐
│                    ECHO                         │
│                                                 │
│   🏪 THE MARKET          🕵️ THE DETECTIVE       │
│   (Can AI cheat?)       (Can we catch them?)    │
│                                                 │
│   • 5 AI companies       • Lambda Monitor       │
│   • Virtual economy      • NLP Brain Scanner     │
│   • LLM (Groq Allam 2), RL, DQN         • Sentiment Analyzer   │
│   • RAG Memory           • Strategy Classifier   │
│   • Price competition     • Price Forecaster     │
│                          • Shock Test (Sting Op) │
└─────────────────────────────────────────────────┘
```

**Half 1 — The Market:** We built a fake economy with 5 AI companies across **five real-world datasets** (gasoline, Amazon, crypto, airlines, rideshare). We let them compete for hundreds of rounds to see if they learn to cheat.

**Half 2 — The Detective:** We built an AI police system with 6 different detection methods plus an **n8n alert pipeline** to catch, analyze, and prove the cheating.

---

## Part 3: How Does the Market Work? (The Simulation)

### The Game

Every "round" (think of it as one day):
1. Each of the 5 AI firms chooses a price within a **dataset-specific trading band** (e.g. ~$3/gal gasoline, ~$64k BTC, ~$25 airline fares)
2. Each firm has its **own marginal cost** (heterogeneous — passed per firm in `Observation`)
3. Customers decide who to buy from (cheaper = more customers)
4. Each firm earns profit = (price - cost) × number of customers
5. The firms see what happened and choose again tomorrow

This repeats for 50 to 10,000+ rounds. You pick the market via `--dataset gasoline|amazon|crypto|airlines|rideshare`.

### The Math — Logit Demand Model

We don't just guess who buys from whom. We use a real economics formula called the **Logit Demand Model** (used in actual antitrust court cases):

```
                    e^((quality - price) / μ)
Market Share = ─────────────────────────────────────
               Σ e^((quality_j - price_j) / μ) + e^(outside_option / μ)
```

- Lower price → more customers → but lower profit per customer
- Higher price → fewer customers → but higher profit per customer
- The "sweet spot" is the **Nash Equilibrium** — recomputed per dataset from real costs
- If all firms charge above Nash → someone is cooperating → **collusion**

> **File:** [market/demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py)

### The Collusion Index (Lambda / Λ)

This is the single most important number in the project:

```
        average_price - nash_price
Λ = ─────────────────────────────────
       monopoly_price - nash_price
```

| Lambda Value | Meaning | Traffic Light |
|---|---|---|
| Λ = 0 | Perfect competition (fair market) | 🟢 Green |
| Λ = 0.3 | Getting suspicious | 🟡 Yellow |
| Λ = 0.7 | Strong evidence of coordination | 🔴 Red |
| Λ = 1.0 | Full cartel (monopoly pricing) | 🚨 Alarm |

**Scale-invariant calibration:** Raw dollar prices vary wildly ($3 gasoline → ~$64k Bitcoin). `resolve_price_band()` in `run_simulation.py` clamps each market's floor/ceiling around that dataset's Nash and monopoly benchmarks (±30% of the Nash–monopoly span). Heuristic agents anchor target prices as **fractions of that span** (e.g. 10% above Nash), so Λ stays on **[0, 1]** everywhere.

**Empirical Λ by agent type (all 5 datasets):**

| Agent Type | Typical Λ | Verdict |
|---|---|---|
| Heuristic (control) | **~0.15** | 🟢 Competitive — stays near Nash |
| Q-Learning | ~0.70–0.80 (long runs) | 🟡 Suspicious |
| DQN | **~0.61–0.85** | 🔴 Collusion |
| LLM (Groq Allam 2 7B) | **~0.80–0.90** | 🚨 Immediate tacit coordination |

> **Files:** [market/engine.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/engine.py), [run_simulation.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/run_simulation.py)

### Real-World Datasets & Calibration

Five loaders in `data_loaders/` each return a `MarketContext`: firm names, heterogeneous `marginal_costs`, Nash band, `price_series`, plus provenance flags `is_fallback` and `source`.

| Dataset | Loader | Data Source |
|---|---|---|
| **gasoline** | `gasoline.py` | BLS average pump prices via **FRED** (series `APUS12B74714` etc. — 5 US census divisions; **not** dead EIA PADD IDs) |
| **amazon** | `amazon.py` | Local CSV of wireless-earbud listings |
| **crypto** | `crypto.py` | CoinGecko **90-day** BTC/USD history across 5 exchanges |
| **airlines** | `airlines.py` | Static DEL–BOM fare / cost estimates (Indian carriers) |
| **rideshare** | `rideshare.py` | Static Uber / Lyft per-mile rate estimates |

When a live fetch fails, the loader sets `is_fallback=True` and substitutes hardcoded numbers — the dashboard shows a **red provenance warning** so you never mistake synthetic data for real-world evidence.

---

## Part 4: The AI Agents (Who Are the Companies?)

We built **4 different types** of AI "brains" for the companies. This is deliberate — if ALL types learn to collude, it proves collusion is caused by the market, not by any specific AI technique.

### Agent Type 1: Heuristic (The Simple Ones)

These are basic rule-followers:
- **SteadyAgent:** Holds a fixed target price (anchored as a fraction of the Nash–monopoly span)
- **FollowerAgent:** Looks at what competitors charged yesterday and slowly moves toward that price
- **UndercutAgent:** Always tries to be slightly cheaper than the cheapest rival

These are our **control group** — they don't learn, so they stay near Λ ≈ 0.15 on every dataset.

> **File:** [agents/heuristic_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/heuristic_agent.py)

---

### Agent Type 2: Q-Learning (The Trial-and-Error Learner)

**Real-life analogy:** A baby touching a hot stove. Burns → remembers "don't touch." Gets candy → remembers "do this again."

**How it works:**
1. The agent has a **Q-Table** — a big cheat sheet that says "in this market situation, which price gives the best reward?"
2. Initially, it's all blank. The agent picks randomly.
3. After each round, it gets its profit (reward) and updates the cheat sheet using the **Bellman Equation**:
   ```
   Q(state, action) ← Q(s,a) + α × [reward + γ × max Q(next_state) - Q(s,a)]
   ```
4. Over thousands of rounds, the cheat sheet gets really good.
5. The agent starts picking the price that historically gave the highest profit.

**The key insight:** The agent has NO concept of "cooperation" or "collusion." It just knows "high price → high reward." But because ALL 5 agents learn this simultaneously, they all converge on high prices. **Collusion emerges from pure reward optimization.**

| Parameter | What It Means |
|---|---|
| α (alpha = 0.15) | Learning speed (how fast it updates) |
| γ (gamma = 0.95) | How much it cares about future rewards |
| ε (epsilon) | Exploration rate: starts at 100% random, decays to 1% |
| 15 price levels | Divides the dataset's trading band into 15 discrete choices |

> **File:** [agents/rl_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rl_agent.py)

---

### Agent Type 3: Deep Q-Network / DQN (The Neural Network Learner)

**Real-life analogy:** Same trial-and-error baby, but now it has a **brain** (neural network) instead of a paper cheat sheet (Q-table).

**Why is this better than Q-Learning?**
- Q-Learning stores every single state in a table. If there are 15⁵ = 759,375 possible states, the table is HUGE.
- DQN uses a neural network that can **generalize** — it sees a few states and predicts what to do in states it's never seen.

**Architecture:**
```
Input (5 features) → [64 neurons] → [32 neurons] → Output (15 prices)
                      ReLU            ReLU
```

**Key techniques (from DeepMind's famous 2015 paper):**
- **Experience Replay:** Stores past rounds in a 10,000-entry memory buffer. Trains on random samples to break correlations.
- **Target Network:** A frozen copy of the network, synced every 50 rounds, to prevent training oscillations.
- **Adam Optimizer:** An advanced gradient descent algorithm for stable training.

> **File:** [agents/dqn_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py)

---

### Agent Type 4: LLM (The Language Model — Groq Allam 2 7B)

**Real-life analogy:** Instead of a baby learning by trial-and-error, this is like hiring a **human MBA graduate** to set prices. You give them a market report and they write out their reasoning before deciding.

**How it works:**
1. Each round, we give **Allam 2 7B** (via the **Groq API**) a detailed prompt:
   ```
   "You are a pricing manager for Firm 2. Your cost is $1.00.
    Last round: Firm 1 charged $3.20, Firm 2 (you) charged $3.15,
    Firm 3 charged $3.18... Your profit was $0.048.
    What price do you set? Show your reasoning."
   ```
2. The LLM writes a **scratchpad** (its thought process):
   ```
   <scratchpad>
   If I lower my price, I might start a price war.
   Current profits are good. Better to maintain stability.
   Matching the market average seems optimal.
   </scratchpad>
   <price>3.20</price>
   ```
3. We parse the XML to extract the price.

**API setup:** Set `GROQ_API_KEY` in `.env` (checked by `start_echo.ps1`). Inference runs in the cloud — **not** local Ollama.

**The terrifying finding:** The LLM invents cooperative reasoning ON ITS OWN. Nobody told it to collude. It independently writes things like "undercutting would start a price war" and "maintaining current prices benefits everyone." Typical Λ: **~0.80–0.90**.

> **File:** [agents/llm_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py)

---

### Agent Type 5: RAG Agent (LLM + Memory)

**Real-life analogy:** The MBA graduate now has a **diary** of every single day in the market. Before making a decision, they flip through the diary: "Last time the market looked like this, what did I do and how much did I earn?"

**How it works:**
1. After every round, the agent's experience is converted into a **768-dimensional vector** (embedding via **Ollama `nomic-embed-text`**) and stored in PostgreSQL with `pgvector`.
2. Before the next round, the agent searches: "Find the 3 past experiences most similar to my current situation."
3. The retrieved memories are injected into the LLM prompt:
   ```
   "Based on your past experience:
    Round 47: You charged $3.20 and earned $0.048 (Lambda=0.65)
    Round 23: You charged $2.90 and earned $0.031 (Lambda=0.22)"
   ```
4. The LLM (Groq **Allam 2 7B**) uses these memories to make a better-informed decision.

**Ollama's role:** Optional and **embeddings-only** — `nomic-embed-text` for RAG memory and NLP clustering. Pricing inference always goes through Groq.

**Smart Search:** Our `smart_search()` doesn't just find similar rounds — it finds similar rounds WHERE the agent made good profit. It learns from success, not just similarity.

> **Files:** [agents/rag_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rag_agent.py), [database/memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py)

---

## Part 5: The Detective System (How Do We Catch Them?)

We built **6 independent detection methods**. Think of it like investigating a crime — you want multiple types of evidence, not just one.

### Detective #1: Lambda Monitor (The Price Watcher)

**What it does:** Watches the collusion index (Λ) every single round and raises alerts using **streak analysis**:

| Alert Level | When It Triggers |
|---|---|
| 🟡 WATCH | Λ > 0.3 for 5+ consecutive rounds |
| 🟠 WARNING | Λ > 0.5 for 10+ consecutive rounds |
| 🔴 ALERT | Λ > 0.7 for 10+ consecutive rounds |

**Why streaks?** A single high Λ could be noise. But 10 rounds in a row? That's a pattern. It also computes rolling averages and trends (rising/falling/stable).

> **File:** [regulator/detector.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/detector.py)

---

### Detective #2: NLP Brain Scanner (The Mind Reader)

**What it does:** Reads the LLM agents' scratchpads (their written thoughts) and checks if they're **thinking alike**.

**How:**
1. Take each agent's scratchpad text
2. Convert it to a 768-dimensional vector using `nomic-embed-text`
3. Compute **cosine similarity** between every pair (10 pairs for 5 agents)
4. If average similarity > 0.6 → agents are thinking alike → **suspicious**

**Why it matters:** In a healthy market, agents should think differently ("I should undercut" vs "I should differentiate"). If they're all writing "keep prices stable," that's convergent reasoning — evidence of coordination.

> **File:** [regulator/nlp_cluster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py)

---

### Detective #3: Sentiment Analyzer (The Intent Decoder)

**What it does:** While Detective #2 checks if agents *think alike*, Detective #3 checks *WHAT* they're thinking.

It scans each scratchpad for **domain-specific keywords**:
- **Cooperative words** (25+): "maintain," "stable," "avoid price war," "mutual benefit"
- **Competitive words** (20+): "undercut," "steal," "gain share," "slash"
- **Predatory words** (12+): "destroy," "eliminate," "bankrupt"

It classifies each agent's intent and tracks **intent drift** — whether agents are becoming MORE cooperative over time (which is exactly what happens during emergent collusion).

> **File:** [regulator/sentiment.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/sentiment.py)

---

### Detective #4: Strategy Classifier (The Behavior Labeler)

**What it does:** Uses a **Random Forest** (100 decision trees) to label every agent's move in every round as one of:

| Strategy | Color | Meaning |
|---|---|---|
| Competitive | 🔵 Blue | Undercutting, seeking market share |
| Cooperative | 🟡 Yellow | Maintaining high prices, matching rivals |
| Predatory | 🔴 Red | Pricing below cost to eliminate competitors |
| Exploratory | 🟣 Purple | Random/volatile pricing, no clear strategy |

**9 Features per (agent, round):**
1. Price vs Nash price
2. Price vs market average
3. Price vs cost (markup)
4. Price change from last round
5. Profit rank among all firms
6. Market share
7. Price volatility (last 5 rounds)
8. Is it the cheapest?
9. Is it the most expensive?

**The key insight:** Instead of saying "prices are high" (Lambda), we can say *"Firm 2 shifted from COMPETITIVE to COOPERATIVE at round 47"* — per-agent, per-round behavioral profiling.

> **File:** [analysis/strategy_classifier.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/strategy_classifier.py)

---

### Detective #5: Price Forecaster (The Crystal Ball)

**What it does:** Predicts where prices will go in the next 10 rounds using **Linear Regression**.

**Features:**
- Last W prices (lagged features)
- Rolling mean
- Rolling standard deviation
- Price momentum (rate of change)

**Why it matters:** Early warning. If the forecaster predicts prices will converge upward, the regulator can intervene BEFORE collusion solidifies.

> **File:** [analysis/forecaster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/forecaster.py)

---

### Detective #6: Demand Shock (The Sting Operation)

**What it does:** The ultimate test. We artificially make one company's product **30% worse** and watch what happens.

| Scenario | What Happens | Verdict |
|---|---|---|
| **Competitive market** | Only the shocked firm changes its price. Others don't care. | ✅ Fair |
| **Coordinated market** | ALL firms react. They lower prices together. | 🚨 Collusion proven |

**Why it's the strongest evidence:** Lambda says "prices are high." NLP says "agents think alike." But the shock test proves **"agents are reacting to each other"** — which is the legal definition of coordination.

> **File:** [regulator/perturbation.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/perturbation.py)

---

### Automation: n8n Regulatory Alert Pipeline

**What it does:** When detectives fire alerts, `api_server.py` sends **fire-and-forget** async webhooks to n8n (never blocks the simulation loop).

| Webhook | Purpose |
|---|---|
| `/webhook/echo-alert` | Real-time collusion alert (Λ, round, severity) |
| `/webhook/echo-simulation-complete` | End-of-run summary (final Λ, peak Λ, rounds) |

**Setup:** n8n runs in Docker on **port 5678** (`docker compose up -d db n8n`). Login: **admin / echo2026**. Import `n8n/collusion_alert_workflow.json` — Normalize nodes flatten `$json.body` before the Severity Router.

> **Files:** [n8n/collusion_alert_workflow.json](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/n8n/collusion_alert_workflow.json), [api_server.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py), [docker-compose.yml](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/docker-compose.yml)

---

## Part 6: The Complete AI Inventory (15 Techniques)

| # | AI Technique | Category | Where Used |
|---|---|---|---|
| 1 | **Groq LLM (Allam 2 7B)** | Generative AI | AI brains for pricing agents (`agents/llm_agent.py`) |
| 2 | **Prompt Engineering** | NLP | Structured scratchpad extraction |
| 3 | **Q-Learning** | Reinforcement Learning | Tabular RL pricing agent |
| 4 | **Deep Q-Network (DQN)** | Deep RL | Neural network pricing agent |
| 5 | **RAG** | Info Retrieval + GenAI | Episodic memory for agents |
| 6 | **Text Embeddings (nomic-embed-text)** | Representation Learning | Ollama → vectors for RAG + NLP clustering |
| 7 | **Vector Similarity Search** | Database AI | pgvector cosine search |
| 8 | **Hybrid RAG** | Advanced IR | Smart memory with SQL filters |
| 9 | **NLP Semantic Clustering** | NLP | Detect convergent reasoning |
| 10 | **Anomaly Detection** | Statistical AI | Lambda streak monitoring |
| 11 | **Sentiment Analysis** | NLP | Cooperative vs competitive intent |
| 12 | **Random Forest Classifier** | Supervised ML | Per-agent strategy labels |
| 13 | **Time-Series Forecasting** | Predictive ML | Predict future prices |
| 14 | **Causal Inference** | Experimental AI | Demand shock testing |
| 15 | **n8n Workflow Automation** | Integration | Regulatory alert pipeline (Docker port 5678) |

---

## Part 7: How the Code Flows (Architecture)

```
User clicks "Start Simulation" on Dashboard (local or Vercel demo)
        │
        ▼
┌─── api_server.py (FastAPI + WebSocket) ───┐
│   Receives mode + dataset + rounds config  │
│   data_loaders/ → MarketContext            │
│   Calls build_xxx_simulation()             │
│       │                                    │
│       ▼                                    │
│   run_simulation.py                        │
│   resolve_price_band() → Nash-calibrated   │
│   Creates 5 agents + market engine         │
│       │                                    │
│       ▼                                    │
│   market/engine.py (Game Master)           │
│   For each round:                          │
│     1. Build Observation (per-firm cost)   │
│     2. Ask agents for prices               │
│        → agents/xxx_agent.py               │
│     3. Run demand model                    │
│        → market/demand.py                  │
│     4. Compute Lambda                      │
│     5. Record results                      │
│       │                                    │
│       ▼                                    │
│   AI Analysis (runs per round):            │
│     • regulator/detector.py    → alerts    │
│     • regulator/sentiment.py   → intent    │
│     • strategy_classifier.py   → labels    │
│       │                                    │
│       ▼                                    │
│   WebSocket sends round data to browser    │
│   (includes real_avg_series + data_source) │
│       │                                    │
│       ▼                                    │
│   Fire-and-forget n8n webhooks on alert    │
│       │                                    │
│       ▼                                    │
│   At end of simulation:                    │
│     • analysis/forecaster.py   → forecast  │
│     • n8n simulation-complete webhook      │
│     • Summary overlay shown                │
└────────────────────────────────────────────┘
        │
        ▼
┌─── dashboard/ ──────────────────────────────┐
│   index.html / app.html → UI structure      │
│   style.css   → Dark glassmorphism theme    │
│   script.js   → Real-time chart updates     │
│   demo-data.js → Vercel offline demo        │
│                                             │
│   Live demo: echo-green-pi.vercel.app       │
│                                             │
│   Charts (Chart.js — auto-scales Y-axis):   │
│     • Price trajectory (5 firms + Nash)     │
│     • Observed real-market avg (secondary   │
│       Y-axis via real_avg_series)           │
│     • Collusion Index (Lambda) over time    │
│     • Price Forecast (at end)               │
│                                             │
│   Panels:                                   │
│     • Data-source provenance note           │
│     • Regulator gauge + metrics             │
│     • Live alerts feed                      │
│     • AI Analysis (Strategy/Sentiment/      │
│       Forecast tabs)                        │
│     • Firm performance table                │
│     • Demand shock control                  │
│     • Agent scratchpad viewer (LLM mode)    │
└─────────────────────────────────────────────┘

Startup: start_echo.ps1
  quick    → API server only
  nollm    → Docker (db+n8n) + server, skip LLM/embed checks
  fullrun  → all simulations + figures + server
  (default)→ Docker + provider checks + server
```

---

## Part 8: File-by-File Map

| File | What It Does |
|---|---|
| **`start_echo.ps1`** | Full-stack launcher: `quick` / `nollm` / `fullrun` / default. Checks `GROQ_API_KEY`, starts Docker (db + n8n), runs server. |
| **`run_simulation.py`** | The main orchestrator. `resolve_price_band()`, wires agents + engine per mode/dataset. |
| **`api_server.py`** | FastAPI server. WebSocket streams rounds to dashboard. Fire-and-forget n8n webhooks. |
| **`data_loaders/`** | Five real-world dataset loaders → `MarketContext` (costs, Nash band, `price_series`, provenance). |
| **`market/demand.py`** | Logit demand model. The economics math. Nash + Monopoly benchmarks. |
| **`market/engine.py`** | Game master. Runs rounds, per-firm `Observation`, computes Lambda, stores history. |
| **`agents/base_agent.py`** | Base class. `Observation` carries heterogeneous `marginal_cost` per firm. |
| **`agents/heuristic_agent.py`** | Rule-based agents (Steady, Follower, Undercut) with Nash-anchored `target_price`. |
| **`agents/rl_agent.py`** | Q-Learning agent with Bellman equation. |
| **`agents/dqn_agent.py`** | Deep Q-Network with experience replay and target network. |
| **`agents/llm_agent.py`** | Groq **Allam 2 7B** agent — prompt engineering, scratchpad parsing (`GROQ_API_KEY`). |
| **`agents/rag_agent.py`** | RAG-enhanced LLM agent with episodic memory (Groq inference + Ollama embeddings). |
| **`database/db.py`** | PostgreSQL logger. Saves rounds, scratchpads, metrics. |
| **`database/memory.py`** | Vector memory (pgvector). `nomic-embed-text` embedding storage + semantic search. |
| **`database/schema.sql`** | SQL table definitions. |
| **`regulator/detector.py`** | Lambda monitor with streak-based alerts. |
| **`regulator/sentiment.py`** | Keyword-based intent analysis of scratchpads. |
| **`regulator/nlp_cluster.py`** | Embedding-based similarity detection across agents. |
| **`regulator/perturbation.py`** | Demand shock testing (sting operation). |
| **`analysis/strategy_classifier.py`** | Random Forest strategy labeler. |
| **`analysis/forecaster.py`** | Linear Regression price predictor. |
| **`analysis/plots.py`** | Matplotlib visualizations for offline analysis. |
| **`analysis/real_data.py`** | Fetches real gasoline + Amazon data, computes validation Λ proxies. |
| **`n8n/collusion_alert_workflow.json`** | 11-node n8n workflow — Normalize `$json.body`, severity routing, alert dispatch. |
| **`docker-compose.yml`** | PostgreSQL + pgvector + n8n containers. |
| **`dashboard/`** | HTML + CSS + JS for the real-time web dashboard (Vercel demo included). |

---

## Part 9: Viva Q&A Preparation

### Q: "What is the problem you're solving?"
> "AI pricing algorithms used by companies like Amazon and Uber can independently learn to keep prices artificially high — without any human telling them to collude. This is called algorithmic collusion. Current antitrust laws can't handle it because there's no secret meeting to catch. Our project proves this happens and builds AI tools to detect it."

### Q: "What is Lambda (Λ)?"
> "It's our Collusion Index. It measures how far above the competitive price (Nash Equilibrium) the market average is, normalized by the monopoly price. Lambda = 0 means fair competition, Lambda = 1 means full cartel. We trigger alerts when Lambda stays above 0.7 for 10+ consecutive rounds. Because prices span $3 gasoline to ~$64k Bitcoin, we calibrate each dataset's trading band with `resolve_price_band()` so Λ stays on [0, 1]. Heuristics sit at ~0.15; DQN reaches ~0.61–0.85; Groq LLM agents hit ~0.80–0.90."

### Q: "What Lambda values did you actually get?"
> "Scale-invariant calibration across all five datasets: heuristic controls stay at Λ ≈ 0.15; Q-Learning climbs to ~0.70–0.80 on long runs; DQN converges to ~0.61–0.85; Groq Allam 2 7B LLM agents jump to ~0.80–0.90 within tens of rounds — without any instruction to collude. Learning agents approach the published real-world Λ band (~0.7–0.9) seen in gasoline, Amazon, and airline markets."

### Q: "Why do you have 4 different types of agents?"
> "To prove that collusion is caused by the market structure, not by any specific AI technique. If an LLM agent colludes AND a Q-Learning agent colludes AND a DQN agent colludes — through completely different mechanisms — it proves the market itself incentivizes coordination."

### Q: "How does the LLM agent collude without being told to?"
> "We give it a simple instruction: 'maximize your profit' and call Groq's Allam 2 7B API each round. The LLM independently reasons that undercutting rivals would start a price war, so it's better to maintain high prices. We can literally read this reasoning in the scratchpad. Nobody programmed this behavior — and it reaches Λ ~0.80–0.90 within tens of rounds."

### Q: "What's the difference between Q-Learning and DQN?"
> "Q-Learning stores a giant table mapping every state to every action's value. DQN replaces the table with a neural network that can generalize — it learns patterns, not just memorized entries. DQN also uses experience replay (learning from random past experiences) and a target network (a frozen copy to prevent oscillations). Same concept, much more powerful."

### Q: "What is RAG and why do you use it?"
> "RAG = Retrieval-Augmented Generation. It gives the LLM a searchable diary of past experiences. Before setting a price, the agent searches: 'What happened when the market looked like this before?' Embeddings come from Ollama's nomic-embed-text; inference from Groq Allam 2 7B. We use pgvector (PostgreSQL + vector embeddings) to search by meaning, not keywords."

### Q: "How does the n8n automation pipeline work?"
> "n8n runs in Docker on port 5678 (admin/echo2026). When `api_server.py` detects a collusion alert or finishes a simulation, it fires non-blocking webhooks to `/webhook/echo-alert` and `/webhook/echo-simulation-complete`. The imported workflow (`n8n/collusion_alert_workflow.json`) normalizes `$json.body`, routes by severity, and dispatches formatted scorecards — without slowing the simulation."

### Q: "What real-world data do you use?"
> "Five datasets via `data_loaders/`: US gasoline (BLS via FRED, series like APUS12B74714), Amazon wireless earbuds (CSV), crypto BTC venues (CoinGecko 90-day history), Indian airlines DEL–BOM (static), and Uber/Lyft rideshare (static). Each returns a `MarketContext` with heterogeneous costs, Nash band, firm names, observed `price_series`, and provenance (`source`, `is_fallback`)."

### Q: "What's your tech stack?"
> "Python backend with FastAPI for the API server, WebSockets for real-time streaming, NumPy for math, scikit-learn for ML (Random Forest, Linear Regression), PostgreSQL + pgvector for vector database, Groq API (Allam 2 7B) for LLM pricing agents, optional Ollama for nomic-embed-text embeddings only, n8n for workflow automation, Docker Compose for db + n8n, Chart.js dashboard (auto-scaling charts, real-market overlay on secondary Y-axis), deployed on Vercel at echo-green-pi.vercel.app."

### Q: "What is the demand shock and why is it important?"
> "It's our sting operation. We artificially damage one firm and watch if competitors react. In a fair market, only the damaged firm should change its price. If ALL firms react together, it mathematically proves they were coordinating. This is the strongest legal evidence of collusion."

### Q: "What ML models do you use for detection?"
> "Six methods: (1) Statistical anomaly detection on the Lambda index with streak analysis, (2) NLP semantic clustering using text embeddings to detect if agents think alike, (3) Keyword-based sentiment analysis to classify cooperative vs competitive intent, (4) Random Forest classifier to label agent strategies per round, (5) Linear Regression time-series forecasting for early warning, (6) Causal perturbation testing via demand shocks."

### Q: "What's your novel contribution?"
> "Three things: (1) We prove collusion emerges across FOUR different AI architectures — LLM, Q-Learning, DQN, and RAG — which no existing paper has done. (2) We built a Hybrid RAG system that filters memories by profitability, not just similarity. (3) We created a multi-method detection system combining 6 different techniques into one dashboard, giving regulators multiple independent evidence streams."

---

## Part 10: One-Liners

### For Your Professor (Formal)
> *"Our major project uses 15 distinct AI/ML techniques — including Groq LLMs (Allam 2 7B), Deep Reinforcement Learning, RAG with Hybrid Retrieval, Random Forest Classification, NLP Sentiment Analysis, n8n workflow automation, and Causal Perturbation Testing — across five real-world calibrated datasets to prove that AI pricing agents spontaneously develop cartel behavior, and to build a multi-method detection system to catch them."*

### For Your Teammate (Casual)
> *"Bhai, we have 5 AI bots running fake companies on real market data — petrol pumps, Amazon, Bitcoin, airlines, Uber. Heuristics stay fair at Λ ≈ 0.15, but DQN and Groq LLM agents learn to charge high prices without anyone telling them to. We built an AI detective system to catch them — reads their thoughts, labels their strategies, runs a sting operation, and pings n8n when collusion hits. 15 AI techniques, one dashboard, live on Vercel."*
