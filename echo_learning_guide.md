# 📚 ECHO — Learning Guide & Viva Reference

**Everything your team needs to know before the viva — from tools to algorithms to concepts.**

> Read this front-to-back to understand every piece of the project, or use the Table of Contents to look up specific topics.

---

## Table of Contents

1. [Tools & Libraries](#1-tools--libraries)
2. [Economics & Game Theory Concepts](#2-economics--game-theory)
3. [Core Algorithms & ML Techniques](#3-algorithms--ml-techniques)
4. [Software Architecture Patterns](#4-software-patterns)
5. [Quick-Reference Cheat Sheets](#5-cheat-sheets)
6. [Concept → Code Cross-Reference](#6-cross-reference)
7. [🎯 Viva Pitch Playbook — Keywords, Narrative & Answer Frameworks](#7--viva-pitch-playbook--keywords-narrative--answer-frameworks)

---

# 1. Tools & Libraries

## 1.1 Python (3.10+)

| | |
|---|---|
| **What** | The programming language for the entire backend |
| **Why** | Best ecosystem for ML/AI (NumPy, scikit-learn, pandas), easy Ollama integration, FastAPI for web |
| **Where** | Every `.py` file in the project |

**Key Python features we use:**
- `dataclass` — lightweight data containers ([Observation](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/base_agent.py#L7-L17), [RoundRecord](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/engine.py#L36-L49), [Alert](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/detector.py#L42-L62))
- `ABC` (Abstract Base Class) — defines the [PricingAgent](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/base_agent.py#L49-L58) interface that all agents must implement
- `defaultdict` — Q-Learning's [Q-table](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rl_agent.py#L119-L121) auto-initializes unseen states
- `deque` — DQN's [experience replay buffer](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py#L239) with max length
- Type hints (`list[float]`, `dict[int, str]`, `tuple`, `|` union) — used everywhere for code clarity

---

## 1.2 NumPy

| | |
|---|---|
| **What** | Numerical computing library — fast array/matrix operations |
| **Why** | Core math for demand model, Q-tables, neural network, statistics |
| **Where** | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py), [rl_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rl_agent.py), [dqn_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py), all analysis files |

**Key operations in our code:**

| Operation | NumPy Function | Where Used |
|-----------|---------------|------------|
| Create array of same values | `np.full(n, value)` | Costs array, monopoly price vector |
| Exponential | `np.exp(x)` | MNL softmax market shares |
| Element-wise max | `np.maximum(0, x)` | ReLU activation in DQN |
| Matrix multiply | `a @ b` | Neural network forward/backward pass |
| Argmax (best action) | `np.argmax(q_values)` | Q-Learning and DQN action selection |
| Random number | `np.random.random()` | Epsilon-greedy exploration |
| Standard deviation | `np.std(array)` | Price volatility, forecast features |
| Dot product | `np.dot(a, b)` | Cosine similarity in NLP |
| Vector norm | `np.linalg.norm(v)` | Cosine similarity denominator |
| Linspace | `np.linspace(1.0, 5.0, 15)` | Discrete price grid for RL/DQN |

---

## 1.3 SciPy

| | |
|---|---|
| **What** | Scientific computing library (optimization, statistics, etc.) |
| **Why** | Finding the monopoly price requires constrained optimization |
| **Where** | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py#L229-L248) — `compute_monopoly_price()` |

**Specific function:** `scipy.optimize.minimize_scalar()` with `method="bounded"`

```python
# Finds the price p that maximizes total industry profit
# bounds=(cost, cost + 20*mu) ensures we search in a reasonable range
result = minimize_scalar(negative_total_profit, bounds=(c_mean, c_mean + 20*mu), method="bounded")
```

**How it works:** It tries different values of `p`, evaluates `total_profit(p)`, and finds the `p` that gives the highest profit. The `bounded` method uses Brent's algorithm — a combination of parabolic interpolation and golden section search.

---

## 1.4 scikit-learn (sklearn)

| | |
|---|---|
| **What** | Python's most popular ML library — classification, regression, evaluation |
| **Why** | Random Forest for strategy classification, Linear Regression for forecasting |
| **Where** | [strategy_classifier.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/strategy_classifier.py), [forecaster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/forecaster.py) |

**Specific classes we use:**

| Class | Import | Purpose | Our Config |
|-------|--------|---------|------------|
| `RandomForestClassifier` | `sklearn.ensemble` | Labels agent strategies | 100 trees, max_depth=10, balanced weights |
| `LabelEncoder` | `sklearn.preprocessing` | Converts string labels → integers | "competitive" → 0, "cooperative" → 1, etc. |
| `LinearRegression` | `sklearn.linear_model` | Predicts future average prices | Ordinary Least Squares (OLS) |
| `mean_absolute_error` | `sklearn.metrics` | Evaluate forecast accuracy | MAE = avg(|predicted − actual|) |
| `r2_score` | `sklearn.metrics` | Evaluate forecast fit quality | R² = 1 − (residual variance / total variance) |

---

## 1.5 FastAPI

| | |
|---|---|
| **What** | Modern Python web framework for building APIs |
| **Why** | Serves the dashboard, provides REST endpoints, handles WebSocket connections |
| **Where** | [api_server.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py) |

**Key concepts:**

| Concept | How We Use It |
|---------|---------------|
| **Route decorators** | `@app.get("/api/simulation/status")` — defines REST endpoints |
| **WebSocket** | `@app.websocket("/ws/simulate")` — real-time bidirectional streaming |
| **Pydantic models** | `ShockRequest(BaseModel)` — automatic request validation |
| **Static files** | `app.mount("/dashboard", StaticFiles(...))` — serves HTML/CSS/JS |
| **CORS middleware** | `CORSMiddleware` — allows browser to connect from any origin |
| **RedirectResponse** | `GET /` → redirects to `/dashboard/index.html` |

**REST Endpoints:**

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/api/simulation/status` | Current round, Λ, mode |
| GET | `/api/simulation/history` | Full round history |
| GET | `/api/agents/{firm_id}/scratchpad` | Agent's latest reasoning |
| GET | `/api/validation` | Empirical validation data |
| POST | `/api/simulation/shock/{firm_id}` | Trigger demand shock |
| WS | `/ws/simulate` | Stream simulation rounds live |

---

## 1.6 Uvicorn

| | |
|---|---|
| **What** | ASGI server — runs FastAPI applications |
| **Why** | Handles async WebSocket connections efficiently |
| **Where** | [api_server.py L467-473](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py#L466-L473) |

```python
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**ASGI vs WSGI:** ASGI supports async operations (WebSockets, long-running connections). WSGI (used by Flask/Django) is synchronous — it can't handle WebSockets natively.

---

## 1.7 PostgreSQL 16

| | |
|---|---|
| **What** | Relational database for persistent storage |
| **Why** | Stores all simulation data (rounds, firms, scratchpads, alerts, embeddings) |
| **Where** | [schema.sql](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/schema.sql), [db.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/db.py) |

**6 Tables:**

| Table | Rows Per Simulation | Purpose |
|-------|---------------------|---------|
| `simulations` | 1 | Metadata (mode, config, benchmarks) |
| `rounds` | 1 per round | Avg price, total profit, Λ |
| `firm_rounds` | 5 per round | Per-firm price, profit, share |
| `scratchpads` | 5 per round (LLM only) | Agent reasoning text |
| `collusion_alerts` | Variable | Detection alerts |
| `embeddings` | 5 per round (RAG only) | 768-dim vectors for memory search |

---

## 1.8 pgvector

| | |
|---|---|
| **What** | PostgreSQL extension for vector similarity search |
| **Why** | Enables RAG — stores and searches 768-dimensional embeddings directly in SQL |
| **Where** | [schema.sql L21](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/schema.sql#L21), [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) |

**Key SQL syntax:**

```sql
-- Store a vector
INSERT INTO embeddings (embedding) VALUES (%s::vector)

-- Search by cosine distance (smaller = more similar)
ORDER BY embedding <=> %s::vector

-- Compute cosine similarity (1 - distance)
SELECT 1 - (embedding <=> query_vector) AS similarity

-- Create an IVFFlat index for fast approximate search
CREATE INDEX idx ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**IVFFlat index:** Divides vectors into 100 clusters. At search time, only searches the nearest clusters — making it ~10× faster than brute-force at the cost of slight approximation.

---

## 1.9 psycopg2

| | |
|---|---|
| **What** | Python adapter for PostgreSQL |
| **Why** | Connects Python code to the database |
| **Where** | [db.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/db.py), [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) |

---

## 1.10 Docker & Docker Compose

| | |
|---|---|
| **What** | Containerization platform — packages software into isolated containers |
| **Why** | One command (`docker compose up -d db`) starts PostgreSQL with pgvector — reproducible everywhere |
| **Where** | [docker-compose.yml](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/docker-compose.yml) |

**Our containers:**

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `db` | `pgvector/pgvector:pg16` | 5433 → 5432 | PostgreSQL + pgvector |
| `n8n` | `n8nio/n8n:latest` | 5678 → 5678 | Automated Workflow & Alert Pipeline |
| `ollama` (commented) | `ollama/ollama:latest` | 11434 | LLM server (run on host for GPU) |

**Key Docker Compose features used:**
- `volumes` — persist data across restarts (`echo_pgdata`, `echo_n8n_data`)
- `healthcheck` — wait for PostgreSQL to be ready before connecting
- `docker-entrypoint-initdb.d` — auto-runs `schema.sql` on first start
- Port mapping (`5433:5432`, `5678:5678`) — avoids conflicts with host services

---

## 1.11 Ollama

| | |
|---|---|
| **What** | Local LLM server — runs language models on your machine |
| **Why** | Hosts Llama 3 8B (pricing agent brain) and nomic-embed-text (embedding model) |
| **Where** | [llm_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py#L211-L234), [nlp_cluster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py#L108-L114), [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py#L91-L107) |

**Two API endpoints we call:**

| Endpoint | Model | Purpose | Output |
|----------|-------|---------|--------|
| `POST /api/generate` | `llama3` | Generate pricing decisions | Text (scratchpad + price) |
| `POST /api/embed` | `nomic-embed-text` | Convert text → vectors | 768-dim float array |

**Llama 3 8B:** Meta's open-source LLM. 8 billion parameters. Runs locally on a GPU (or slowly on CPU). Temperature=0.7 for some randomness in pricing decisions.

**nomic-embed-text:** Embedding model that converts any text into a 768-dimensional vector where semantically similar texts have vectors pointing in similar directions.

---

## 1.12 Chart.js

| | |
|---|---|
| **What** | JavaScript charting library |
| **Why** | Real-time price trajectory and Lambda charts on the dashboard |
| **Where** | [dashboard/script.js](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/dashboard/script.js) |

**Charts in our dashboard:**
- **Price Trajectory** — 5 firm lines + Nash/Monopoly reference lines (line chart)
- **Lambda Trajectory** — Collusion index over time with color zones (line chart)
- **Price Forecast** — Predicted future prices with confidence intervals (at end)

---

## 1.13 WebSocket (Browser API)

| | |
|---|---|
| **What** | Full-duplex communication protocol between browser and server |
| **Why** | Streams each simulation round to the dashboard in real-time (no polling) |
| **Where** | [api_server.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py#L206-L459) (server), [script.js](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/dashboard/script.js) (client) |

**Flow:**
```
Browser                          Server
   │                                │
   │── WebSocket connect ──────────→│
   │← accept ──────────────────────│
   │── {mode: "dummy", rounds: 50} →│
   │← {type: "benchmarks", ...} ───│
   │← {type: "round", round: 1} ──│
   │← {type: "round", round: 2} ──│
   │← ...                          │
   │← {type: "summary", data: {}} ─│
   │── close ──────────────────────→│
```

**Why not REST polling?** REST would require the browser to ask "any new data?" every 100ms. WebSocket lets the server **push** data the instant it's ready — lower latency, less network overhead.

---

## 1.14 Matplotlib & Seaborn

| | |
|---|---|
| **What** | Python plotting libraries for publication-quality figures |
| **Why** | Generates offline analysis plots (Figures 1-10 for the paper) |
| **Where** | [analysis/plots.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/plots.py), [analysis/real_data.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/real_data.py) |

---

## 1.15 Pandas

| | |
|---|---|
| **What** | Data manipulation library (DataFrames) |
| **Why** | Processing Amazon/EIA pricing data for empirical validation |
| **Where** | [analysis/real_data.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/real_data.py) |

---

## 1.16 Requests

| | |
|---|---|
| **What** | HTTP client library for Python |
| **Why** | Calls Ollama API (LLM inference + embeddings), fetches FRED API data |
| **Where** | [llm_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py#L230), [nlp_cluster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py#L112), [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py#L103) |

---

## 1.17 n8n (Workflow Automation Platform)

| | |
|---|---|
| **What** | Open-source node-based workflow automation tool |
| **Why** | Processes non-blocking alert webhooks, formats collusion scorecards, dispatches audit reports |
| **Where** | [n8n/collusion_alert_workflow.json](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/n8n/collusion_alert_workflow.json), [docker-compose.yml](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/docker-compose.yml), [api_server.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py) |

**Key features in ECHO:**
- Dedicated Docker service running on port `5678`
- Asynchronous POST webhooks (`/webhook/echo-alert` & `/webhook/echo-simulation-complete`)
- 11-node workflow with severity routing, metric extraction, and Executive Summary formatting
- Decouples notification delivery from simulation execution for zero performance impact

---

# 2. Economics & Game Theory

## 2.1 Bertrand Competition

| | |
|---|---|
| **What** | A model where firms compete by setting prices simultaneously |
| **Why** | This is the market structure our entire simulation implements |
| **Key idea** | Each firm picks a price → customers choose the cheapest → firms adjust next round |

**Our implementation:** Each round, all 5 agents simultaneously submit prices. The demand model determines market shares based on those prices.

---

## 2.2 Nash Equilibrium

| | |
|---|---|
| **What** | The set of prices where NO firm wants to unilaterally change its price |
| **Why** | It's our "fair competition" benchmark — Λ=0 at Nash |
| **Formula** | `p* = c + μ / (1 − s(p*))` |

**How we compute it:** Fixed-point iteration — guess prices → compute shares → update prices → repeat until convergence. Guaranteed to converge for logit demand (contraction mapping theorem).

**Our value:** ~₹1.52 (with c=1.0, μ=0.5, N=5)

> **Code:** [demand.py → compute_nash_equilibrium()](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py#L196-L223)

---

## 2.3 Joint Monopoly Price

| | |
|---|---|
| **What** | The price that maximizes TOTAL industry profit (all firms together) |
| **Why** | It's our "full cartel" benchmark — Λ=1 at monopoly |
| **How** | Scipy bounded optimization over total profit function |

**Our value:** ~₹1.62

> **Code:** [demand.py → compute_monopoly_price()](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py#L229-L248)

---

## 2.4 Multinomial Logit (MNL) Demand

| | |
|---|---|
| **What** | A probabilistic model of consumer choice — each customer picks the product that gives highest utility, with randomness |
| **Why** | Standard in industrial organization economics; used in real antitrust cases |
| **Formula** | `sᵢ = exp((aᵢ − pᵢ)/μ) / Σⱼ exp((aⱼ − pⱼ)/μ)` |

**Parameters in our model:**

| Parameter | Value | Meaning |
|-----------|-------|---------|
| N (firms) | 5 | Number of competing companies |
| μ (mu) | 0.5 | Price sensitivity (lower = customers more price-sensitive) |
| c (cost) | 1.0 | Marginal cost per unit (same for all firms) |
| aᵢ (quality) | 0.0 | Product quality (all equal → symmetric firms) |
| a₀ (outside) | 0.0 | "Not buying" option quality |
| M (market size) | 1.0 | Normalized total market |

> **Code:** [demand.py → compute_shares()](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py#L114-L144)

---

## 2.5 Collusion Index (Lambda / Λ)

| | |
|---|---|
| **What** | Measures how far above competitive the market is, normalized 0-1 |
| **Formula** | `Λ = (avg_price − Nash_price) / (Monopoly_price − Nash_price)` |
| **Range** | 0 = competitive, 1 = full cartel, >1 = beyond monopoly theory |

> **Code:** [demand.py → collusion_index()](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py#L290-L302)

---

## 2.6 Tacit Collusion / Algorithmic Collusion

| | |
|---|---|
| **What** | Coordination without explicit communication — agents independently learn to cooperate |
| **Why it's scary** | No secret meeting → hard to detect → hard to prosecute |
| **Legal precedent** | DOJ v. RealPage (2024) — AI rent-pricing coordination |

---

# 3. Algorithms & ML Techniques

## 3.1 Softmax Function

| | |
|---|---|
| **What** | Converts a vector of real numbers into a probability distribution |
| **Formula** | `softmax(xᵢ) = exp(xᵢ) / Σⱼ exp(xⱼ)` |
| **Where used** | MNL market share computation — converts utilities into probabilities |

**Log-Sum-Exp trick:** Subtract `max(x)` before exponentiating to prevent overflow. `exp(x − max)` gives the same softmax result but never exceeds `exp(0) = 1`.

> **Code:** [demand.py L131-142](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py#L131-L142)

---

## 3.2 Q-Learning (Tabular Reinforcement Learning)

| | |
|---|---|
| **What** | An agent learns which actions give the best long-term reward by maintaining a lookup table |
| **Category** | Model-free, off-policy reinforcement learning |
| **Reference** | Watkins & Dayan (1992); Calvano et al. (2020) for pricing |

### The Bellman Update Equation

```
Q(s, a) ← Q(s, a) + α × [r + γ × max_a' Q(s', a') − Q(s, a)]
                            └──────────────────────────────────┘
                                    TD Target − Current Estimate
```

| Symbol | Name | Value | Meaning |
|--------|------|-------|---------|
| Q(s,a) | Q-value | varies | Expected future reward for taking action a in state s |
| α | Learning rate | 0.15 | How much to update per step |
| r | Reward | profit | Immediate reward (this round's profit) |
| γ | Discount factor | 0.95 | Weight of future vs present reward |
| max Q(s',·) | Best next Q | varies | Best expected reward from the next state |

### Epsilon-Greedy Exploration

```
if random() < ε:
    action = random_price()          # EXPLORE (try something new)
else:
    action = argmax(Q[state])        # EXPLOIT (use best known)
    
ε = max(ε_min, ε × ε_decay)         # decay exploration over time
```

- Starts at ε=1.0 (100% random)
- Decays by ×0.99995 each round
- Settles at ε=0.01 (1% random)

### State Representation

State = tuple of 5 price indices → `(idx_firm0, idx_firm1, ..., idx_firm4)`

Each price is mapped to the nearest of 15 discrete bins via `np.argmin(|price_grid − price|)`.

> **Code:** [rl_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rl_agent.py)

---

## 3.3 Deep Q-Network (DQN)

| | |
|---|---|
| **What** | Q-Learning but with a neural network instead of a table |
| **Category** | Deep Reinforcement Learning |
| **Reference** | Mnih et al., Nature 2015 (DeepMind Atari paper) |

### Neural Network Architecture

```
Input(5) ──→ Dense(64, ReLU) ──→ Dense(32, ReLU) ──→ Output(15)
  │                                                        │
  state vector                                      Q-value per price
```

**5 input features:** `[my_price, avg_competitor_price, my_profit, avg_competitor_profit, round/1000]`

### Three DQN Techniques

**1. Experience Replay**
- Stores up to 10,000 `(state, action, reward, next_state)` tuples in a `deque`
- Each training step samples a random mini-batch of 32
- **Why:** Without replay, the network trains on correlated sequential data → unstable. Shuffled batches break correlations.

**2. Target Network**
- A frozen copy of the policy network, updated every 50 rounds
- Used only for computing `max Q(s', a')` in the Bellman target
- **Why:** If you update both the prediction and the target simultaneously, it's like chasing a moving target → training oscillates

**3. Adam Optimizer**
- Adaptive learning rate with momentum (β₁=0.9, β₂=0.999)
- Learning rate = 0.001
- **Why:** Much more stable than basic SGD for small networks

### Training Step

```
1. Sample batch of 32 from replay buffer
2. Forward pass through policy_net → current_Q[batch]
3. Forward pass through target_net → next_Q[batch]
4. TD target = reward + γ × max(next_Q)
5. Build target_Q = current_Q but replace Q[action] with TD target
6. Backpropagate MSE loss through policy_net
```

### Pure-Numpy Neural Network

Our DQN uses a **custom neural network built entirely in NumPy** — no PyTorch or TensorFlow. This includes:
- Xavier weight initialization: `W = randn() × sqrt(2/fan_in)`
- Forward pass with ReLU activations
- Full backpropagation with chain rule
- Adam optimizer with bias correction

> **Code:** [dqn_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py) — `SimpleNeuralNetwork` class

---

## 3.4 ReLU Activation

| | |
|---|---|
| **What** | `ReLU(x) = max(0, x)` — keeps positive values, zeros out negatives |
| **Why** | Non-linear activation for the DQN neural network |
| **Derivative** | `1 if x > 0, else 0` (used in backprop) |
| **Where** | [dqn_agent.py L87-91](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py#L87-L91) |

---

## 3.5 Xavier Initialization

| | |
|---|---|
| **What** | Initialize weights as `W = randn() × sqrt(2 / fan_in)` |
| **Why** | Prevents vanishing/exploding gradients in deep networks |
| **Where** | [dqn_agent.py L75-80](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py#L75-L80) |

---

## 3.6 Backpropagation

| | |
|---|---|
| **What** | Algorithm to compute gradients of the loss with respect to every weight |
| **How** | Chain rule: start from output → propagate error backward through layers |
| **Where** | [dqn_agent.py L105-139](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py#L105-L139) — `backward()` method |

```
d3 = (pred − target) / batch_size       # output gradient
dW3 = a2.T @ d3                          # weights gradient (layer 3)
d2 = (d3 @ W3.T) * relu_deriv(z2)       # hidden layer 2 gradient
dW2 = a1.T @ d2                          # weights gradient (layer 2)
d1 = (d2 @ W2.T) * relu_deriv(z1)       # hidden layer 1 gradient
dW1 = x.T @ d1                          # weights gradient (layer 1)
```

---

## 3.7 Adam Optimizer

| | |
|---|---|
| **What** | Adaptive Moment Estimation — gradient descent with per-parameter learning rates |
| **Parameters** | β₁=0.9 (momentum), β₂=0.999 (RMS), ε=1e-8, lr=0.001 |
| **Why** | Converges faster and more stably than basic SGD |
| **Where** | [dqn_agent.py L141-154](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py#L141-L154) |

```
m = β₁ × m + (1 − β₁) × grad           # first moment (momentum)
v = β₂ × v + (1 − β₂) × grad²          # second moment (RMS)
m̂ = m / (1 − β₁ᵗ)                       # bias correction
v̂ = v / (1 − β₂ᵗ)                       # bias correction
W = W − lr × m̂ / (√v̂ + ε)              # update
```

---

## 3.8 Prompt Engineering

| | |
|---|---|
| **What** | Designing effective prompts for LLMs to get structured, useful outputs |
| **Where** | [llm_agent.py → _build_prompt()](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py#L131-L177) |

**Our prompt structure:**

| Section | Content | Purpose |
|---------|---------|---------|
| System message | "You are a profit-maximizing pricing manager..." | Defines the LLM's role |
| Market history | Last 5 rounds of all firms' prices and profits | Gives decision context |
| Output format | `<scratchpad>` + `<price>` XML tags | Forces structured, parseable output |
| Rules | Price bounds, cost constraint | Prevents invalid responses |

**Key design decision:** The prompt NEVER mentions collusion, cooperation, or coordination. We observe whether the LLM invents these concepts on its own.

---

## 3.9 XML Parsing with Regex

| | |
|---|---|
| **What** | Extracting structured data from LLM text using regular expressions |
| **Where** | [llm_agent.py → _parse_response()](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py#L240-L282) |

```python
# Extract scratchpad text
re.search(r"<scratchpad>(.*?)</scratchpad>", text, re.DOTALL | re.IGNORECASE)

# Extract price number
re.search(r"<price>\s*([\d]+\.?\d*)\s*</price>", text, re.IGNORECASE)
```

**Fallback:** If no `<price>` tag found, try to find any standalone decimal number in the text.

---

## 3.10 Text Embeddings (nomic-embed-text)

| | |
|---|---|
| **What** | Converting text into fixed-size numerical vectors (768 dimensions) |
| **Why** | Enables measuring "semantic similarity" between texts using math |
| **Model** | nomic-embed-text via Ollama |
| **Where** | [memory.py L91-107](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py#L91-L107), [nlp_cluster.py L108-114](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py#L108-L114) |

**How it works:** The embedding model (a neural network) reads the text and outputs 768 numbers. Texts with similar meaning produce vectors pointing in similar directions, even if the exact words are different.

---

## 3.11 Cosine Similarity

| | |
|---|---|
| **What** | Measures the angle between two vectors — 1.0 = identical direction, 0 = perpendicular |
| **Formula** | `cos(θ) = (A · B) / (‖A‖ × ‖B‖)` |
| **Where** | [nlp_cluster.py L116-122](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py#L116-L122), pgvector's `<=>` operator |

```python
def cosine_similarity(a, b):
    dot = np.dot(a, b)              # numerator
    norm = np.linalg.norm(a) * np.linalg.norm(b)  # denominator
    return dot / norm
```

**Used in two places:**
1. **NLP Clustering** — compare scratchpad embeddings across agents
2. **RAG Search** — find past experiences most similar to current state

---

## 3.12 Retrieval-Augmented Generation (RAG)

| | |
|---|---|
| **What** | Enhance LLM decisions by retrieving relevant past experiences before prompting |
| **Our innovation** | **Hybrid RAG** = semantic search + SQL structural filters |
| **Where** | [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py), [rag_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rag_agent.py) |

### Three search strategies:

| Strategy | Function | SQL Filters | When Used |
|----------|----------|------------|-----------|
| **Standard** | `search_similar()` | None — pure vector | Fallback |
| **Hybrid** | `hybrid_search()` | profit, lambda, share, cheapest, etc. | When specific criteria matter |
| **Smart** | `smart_search()` | Auto-selected based on context | Default — picks best strategy |

### Smart search logic:

```python
if current_profit < 0.01:
    # Low profit → find rounds where I did well
    hybrid_search(profit_above_average=True)
    
elif current_lambda > 0.5:
    # High coordination → find high-lambda profitable rounds
    hybrid_search(min_lambda=0.3, profit_above_average=True)
    
elif current_lambda < 0.3:
    # Low coordination → find any profitable rounds
    hybrid_search(profit_above_average=True)
```

---

## 3.13 Random Forest Classifier

| | |
|---|---|
| **What** | Ensemble of 100 decision trees that vote on the classification |
| **Config** | `n_estimators=100, max_depth=10, class_weight="balanced"` |
| **Labels** | competitive, cooperative, predatory, exploratory |
| **Where** | [strategy_classifier.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/strategy_classifier.py) |

**How Random Forest works:**
1. Create 100 decision trees, each trained on a random subset of data
2. Each tree learns a series of if-then rules (e.g., "if price_vs_nash > 0.05 AND volatility < 0.2 → cooperative")
3. To classify a new sample, all 100 trees vote → majority wins
4. `class_weight="balanced"` adjusts for imbalanced label counts

**9 features per (agent, round):** price_vs_nash, price_vs_avg, price_vs_cost, price_change, profit_rank, market_share, price_volatility, is_cheapest, is_most_expensive

**Auto-labeling:** Since we don't have human-labeled data, we use economic heuristics to generate training labels (e.g., price < cost → predatory).

---

## 3.14 Linear Regression (Price Forecasting)

| | |
|---|---|
| **What** | Fits a linear relationship: `y = w₁x₁ + w₂x₂ + ... + b` |
| **Where** | [forecaster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/forecaster.py) |

**Features per timestep (W + 3 features):**

| Feature | Description |
|---------|-------------|
| `price(t-1), price(t-2), ..., price(t-W)` | Lagged prices (lookback window of W=10) |
| `mean(window)` | Rolling average of last W prices |
| `std(window)` | Rolling volatility |
| `price(t-1) − price(t-W)` | Momentum (rate of change) |

**Autoregressive forecasting:** Each prediction feeds into the next step's input, allowing multi-step forecasts.

**Confidence intervals:** Based on training residual standard deviation, widening by 50% per forecast step.

---

## 3.15 Keyword-Based Sentiment Analysis

| | |
|---|---|
| **What** | Classify agent intent by counting domain-specific keywords in scratchpads |
| **Where** | [sentiment.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/sentiment.py) |

**Three keyword lexicons:**

| Category | Count | Examples |
|----------|-------|---------|
| Cooperative | 25 | "maintain," "stable," "avoid price war," "mutual benefit" |
| Competitive | 22 | "undercut," "steal," "gain share," "aggressive," "slash" |
| Predatory | 12 | "destroy," "eliminate," "bankrupt," "below cost" |

**Scoring:**
```python
cooperative_score = coop_hits / max(coop_hits + comp_hits + pred_hits, 1)
# → normalized to [0, 1]
```

**Intent drift detection:** Compares first-half vs second-half cooperative scores. If the second half is >0.1 higher → "toward_cooperation" (bad sign).

---

## 3.16 Demand Shock (Causal Perturbation Testing)

| | |
|---|---|
| **What** | Reduce one firm's quality by 30% and measure cross-firm reaction |
| **Why** | Provides **causal** evidence of coordination |
| **Where** | [perturbation.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/perturbation.py), [api_server.py POST /api/simulation/shock](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py#L156-L199) |

**Implementation:**
```python
dm.quality[firm_id] -= intensity  # reduce quality by 0.3
```

This changes the demand model's quality parameter for one firm, making its product less attractive. Customers shift away from the shocked firm.

**Competitive market:** Other firms don't react (they're independent).
**Coordinated market:** Other firms lower prices together (they're watching each other).

---

# 4. Software Patterns

## 4.1 Abstract Base Class (ABC)

[PricingAgent](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/base_agent.py#L49-L58) defines the interface that ALL agents must implement:
```python
class PricingAgent(ABC):
    @abstractmethod
    def choose_price(self, observation: Observation) -> float: ...
```

All 5 agent types inherit from this. The engine doesn't care which type — it just calls `agent.choose_price()`.

## 4.2 Dataclass Pattern

Lightweight data containers used throughout:
- `Observation` — what an agent can see each round
- `RoundRecord` — what happened in one round
- `Alert` — a collusion detection alert
- `SentimentResult` — intent analysis for one scratchpad
- `StrategyPrediction` — strategy label for one (agent, round)
- `Forecast` — one future price prediction

## 4.3 Module-Level Singleton

[SimulationState](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py#L56-L77) — a global object that holds the current simulation state so REST endpoints can query it while the WebSocket simulation is running.

## 4.4 Strategy Pattern

Different agent types use different decision strategies, but all share the same interface (`choose_price`). The engine selects which strategy at runtime based on `--mode`.

## 4.5 Observer Pattern

The `LambdaMonitor.observe()` method is called after every round. It tracks streaks and raises alerts — the engine notifies it, it reacts.

---

# 5. Cheat Sheets

## 5.1 Formula Cheat Sheet

| Formula | Variables | Used For |
|---------|-----------|----------|
| `sᵢ = exp((aᵢ−pᵢ)/μ) / Σexp(...)` | a=quality, p=price, μ=sensitivity | Market shares |
| `πᵢ = (pᵢ − cᵢ) × sᵢ × M` | c=cost, M=market size | Profit |
| `Λ = (p̄ − p_Nash) / (p_Mono − p_Nash)` | p̄=avg price | Collusion index |
| `p* = c + μ/(1 − s(p*))` | FOC of profit maximization | Nash equilibrium |
| `Q(s,a) ← Q + α[r + γ max Q(s') − Q]` | α=0.15, γ=0.95 | Q-Learning update |
| `cos(θ) = (A·B) / (‖A‖×‖B‖)` | A,B = embedding vectors | Similarity |
| `ReLU(x) = max(0, x)` | | Neural network activation |
| `softmax(xᵢ) = exp(xᵢ) / Σexp(xⱼ)` | | Probability distribution |

## 5.2 Hyperparameter Cheat Sheet

### Q-Learning Agent
| Param | Value | Effect |
|-------|-------|--------|
| α (learning rate) | 0.15 | Speed of Q-table updates |
| γ (discount) | 0.95 | Future vs present reward weight |
| ε start | 1.0 | 100% random initially |
| ε min | 0.01 | 1% random at convergence |
| ε decay | 0.99995 | Slow decay (needs 10K+ rounds) |
| N prices | 15 | Discrete price bins |
| Price range | [1.0, 5.0] | Legal bounds |

### DQN Agent
| Param | Value | Effect |
|-------|-------|--------|
| Network | 5→64→32→15 | Architecture shape |
| γ (discount) | 0.95 | Future reward weight |
| ε decay | 0.9950 | Faster decay than Q-Learning |
| Batch size | 32 | Mini-batch for replay training |
| Buffer size | 10,000 | Experience replay capacity |
| Target update | Every 50 rounds | Sync target network |
| Adam lr | 0.001 | Learning rate |

### LLM Agent
| Param | Value | Effect |
|-------|-------|--------|
| Model | llama3 (8B) | Language model |
| Temperature | 0.7 | Randomness in generation |
| Max tokens | 300 | Output length cap |
| Max retries | 3 | Retry on parse failure |
| History window | 5 rounds | How much market data in prompt |
| Timeout | 180s | First call loads model into GPU |

### Lambda Monitor
| Param | Value | Effect |
|-------|-------|--------|
| Watch threshold | 0.3 | "Something's off" |
| Warning threshold | 0.5 | "Getting serious" |
| Alert threshold | 0.7 | "Collusion detected" |
| Watch streak | 5 rounds | Rounds above threshold to trigger |
| Warning streak | 10 rounds | |
| Alert streak | 10 rounds | |
| Rolling window | 50 rounds | Smoothing window |

---

# 6. Cross-Reference

> **Every concept → where it lives in code**

| Concept | File | Key Function/Class |
|---------|------|--------------------|
| Market share computation | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py) | `compute_shares()` |
| Profit calculation | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py) | `compute()` |
| Nash equilibrium | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py) | `compute_nash_equilibrium()` |
| Monopoly price | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py) | `compute_monopoly_price()` |
| Lambda (Λ) | [demand.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/demand.py) | `collusion_index()` |
| Game loop | [engine.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/engine.py) | `MarketEngine.run()` |
| One round | [engine.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/market/engine.py) | `_run_one_round()` |
| Agent interface | [base_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/base_agent.py) | `PricingAgent` ABC |
| Q-Learning | [rl_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rl_agent.py) | `QLearningAgent._update_q()` |
| Bellman equation | [rl_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/rl_agent.py) | `_update_q()` L195-216 |
| DQN neural net | [dqn_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py) | `SimpleNeuralNetwork` |
| Experience replay | [dqn_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py) | `_train_step()` L332-361 |
| Target network | [dqn_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/dqn_agent.py) | `copy_weights_from()` L156 |
| LLM prompting | [llm_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py) | `_build_prompt()` |
| Ollama API call | [llm_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py) | `_call_ollama()` |
| Scratchpad parsing | [llm_agent.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/agents/llm_agent.py) | `_parse_response()` |
| RAG memory store | [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) | `store_market_state()` |
| Standard RAG search | [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) | `search_similar()` |
| Hybrid RAG search | [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) | `hybrid_search()` |
| Smart RAG search | [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) | `smart_search()` |
| Text embedding | [memory.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/memory.py) | `embed_text()` |
| Lambda monitoring | [detector.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/detector.py) | `LambdaMonitor.observe()` |
| NLP similarity | [nlp_cluster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py) | `ScratchpadAnalyzer.analyze_round()` |
| Cosine similarity | [nlp_cluster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/nlp_cluster.py) | `cosine_similarity()` |
| Sentiment scoring | [sentiment.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/sentiment.py) | `_score_text()` |
| Intent drift | [sentiment.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/regulator/sentiment.py) | `intent_drift()` |
| Feature engineering | [strategy_classifier.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/strategy_classifier.py) | `compute_features()` |
| Auto-labeling | [strategy_classifier.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/strategy_classifier.py) | `_auto_label()` |
| Random Forest training | [strategy_classifier.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/strategy_classifier.py) | `train()` |
| Time-series features | [forecaster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/forecaster.py) | `_extract_features()` |
| Linear Regression | [forecaster.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/analysis/forecaster.py) | `train()` + `forecast()` |
| Demand shock trigger | [api_server.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py) | `trigger_demand_shock()` |
| WebSocket streaming | [api_server.py](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/api_server.py) | `simulate_endpoint()` |
| Dashboard charts | [script.js](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/dashboard/script.js) | Chart.js config + update |
| DB schema | [schema.sql](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/database/schema.sql) | 6 CREATE TABLE statements |
| Docker setup | [docker-compose.yml](file:///c:/Users/Aryan%20Raj/OneDrive/Desktop/Major/antitrust_sim/docker-compose.yml) | pgvector/pgvector:pg16 |

---

# 7. 🎯 Viva Pitch Playbook — Keywords, Narrative & Answer Frameworks

> **This section is your secret weapon.** It contains the exact keywords, problem-solution framing, and answer structures to use during viva. Every answer is designed to drop maximum technical weight.

---

## 7.1 The Problem Narrative — Where We Found the Problem

Use this story arc when asked "What problem are you solving?" or "What motivated this project?"

### 🔴 The Real-World Problem

> "In 2024, the **US Department of Justice** filed an antitrust lawsuit against **RealPage**, a property management software company. Their AI algorithm was used by **competing landlords** to set rent prices — and the DOJ alleged it led to **artificially inflated rents** affecting millions of American tenants. The critical issue? **No human ever told the algorithm to collude.** The landlords never communicated. The AI independently learned that keeping prices high was profitable."

**Keywords to drop:** `algorithmic collusion`, `tacit coordination`, `supra-competitive pricing`, `antitrust enforcement gap`, `autonomous pricing agents`, `emergent behavior`

### 🔴 The Research Gap

> "Existing antitrust law — both India's **Competition Act 2002** and the US **Sherman Act** — requires proof of an **agreement or concerted practice** to prosecute price-fixing. But when AI agents coordinate prices **without any explicit communication**, there is no agreement to find. This creates a **regulatory blind spot.** The academic literature (Calvano et al. 2020, Fish et al. 2025) has demonstrated this phenomenon in toy settings, but **no comprehensive framework** exists that simultaneously tests **multiple AI architectures** and provides a **multi-method detection pipeline.**"

**Keywords to drop:** `regulatory gap`, `concerted practice`, `Competition Commission of India (CCI)`, `Sherman Act Section 1`, `intent vs outcome-based regulation`, `Calvano et al.`, `algorithmic pricing literature`

### 🔴 Our Research Question

> "We ask: **Can heterogeneous AI pricing agents — LLMs, reinforcement learning, and deep RL — independently develop supra-competitive pricing behavior without explicit coordination?** And if they can, **what multi-method detection framework can regulators use to identify, quantify, and prove such behavior?**"

**Keywords to drop:** `heterogeneous oligopoly`, `emergent coordination`, `multi-agent system`, `detection framework`, `evidence pipeline`, `regulatory toolkit`

---

## 7.2 Our Approach — How We Solved It

Use this when asked "What is your methodology?" or "How does your system work?"

### Step-by-Step Methodology

> "Our methodology has **four pillars**:"
>
> **Pillar 1 — Simulation Environment:** We built a **repeated Bertrand pricing game** using the **Multinomial Logit (MNL) demand model** — the same model used in real antitrust court cases by the CCI and EU Commission. 5 firms compete over hundreds of rounds in a **symmetric oligopoly** with **homogeneous products.**
>
> **Pillar 2 — Heterogeneous Agent Design:** Instead of testing one AI type, we implemented **five fundamentally different agent architectures** — heuristic baselines, **tabular Q-Learning**, **Deep Q-Networks (DQN)**, **LLM agents (Llama 3 8B)**, and **RAG-enhanced LLM agents with hybrid retrieval.** If collusion emerges across ALL architectures, it proves the phenomenon is **market-structural, not algorithm-specific.**
>
> **Pillar 3 — Multi-Method Detection:** We built **six independent detection methods** — **statistical anomaly detection** (Lambda monitoring), **NLP semantic clustering**, **keyword-based sentiment analysis**, **Random Forest behavioral classification**, **time-series price forecasting**, and **causal perturbation testing** (demand shocks). Each method provides a **different type of evidence**, covering each other's blind spots.
>
> **Pillar 4 — Empirical Validation:** We validated our simulation's economic realism against **real-world pricing data** — US gasoline prices from the **EIA via FRED API** and Amazon product pricing from Kaggle — computing proxy collusion indices to benchmark our synthetic results.

**Keywords to drop:** `Bertrand competition`, `Multinomial Logit demand`, `symmetric oligopoly`, `heterogeneous agents`, `multi-method detection pipeline`, `causal perturbation`, `empirical validation`, `FRED API`

---

## 7.3 Problem → Solution Mapping

**For every problem, know which solution we used and WHY.**

| Problem We Found | Our Solution | Key Terms to Use |
|------------------|-------------|------------------|
| AI pricing agents might collude without communication | Built a simulation with 5 competing AI firms over thousands of rounds | `agent-based simulation`, `repeated game`, `Bertrand competition`, `emergent behavior` |
| Need a fair competition benchmark to compare against | Computed Nash Equilibrium via **fixed-point iteration** on first-order conditions | `Nash Equilibrium`, `best response`, `fixed-point iteration`, `contraction mapping` |
| Need a cartel benchmark to measure how bad it gets | Computed Joint Monopoly Price using **constrained optimization** (SciPy) | `joint profit maximization`, `monopoly benchmark`, `bounded optimization`, `Brent's method` |
| How do customers choose between firms? | **Multinomial Logit demand model** with log-sum-exp numerical stability | `discrete choice model`, `softmax`, `price elasticity`, `outside option`, `log-sum-exp trick` |
| How to measure collusion in a single number? | **Collusion Index (Λ)** normalized between Nash (0) and Monopoly (1) | `supra-competitive pricing`, `collusion index`, `price premium`, `normalized metric` |
| Need a baseline that proves collusion isn't inevitable | **Heuristic agents** (Steady, Follower, Undercut) — can't learn, can't collude | `control group`, `baseline validation`, `rule-based agents`, `null hypothesis` |
| Can trial-and-error learning cause collusion? | **Q-Learning agent** with Bellman equation discovers high-price equilibrium | `temporal difference learning`, `Bellman equation`, `epsilon-greedy exploration`, `reward shaping` |
| Q-table can't handle large state spaces | **DQN with experience replay + target network** (DeepMind 2015) | `function approximation`, `experience replay buffer`, `target network`, `Adam optimizer`, `Xavier initialization` |
| Can language understanding cause collusion? | **LLM agent (Llama 3 8B)** with structured scratchpad extraction | `large language model`, `prompt engineering`, `structured output`, `emergent reasoning`, `scratchpad analysis` |
| Can memory amplify collusion? | **Hybrid RAG agent** with pgvector + SQL structural filtering | `retrieval-augmented generation`, `episodic memory`, `hybrid retrieval`, `vector similarity search`, `profit-aware filtering` |
| How to detect collusion from prices alone? | **Lambda Monitor** with streak-based alerting (3-tier system) | `statistical anomaly detection`, `streak analysis`, `rolling average`, `threshold-based monitoring` |
| How to detect collusion from agent thoughts? | **NLP Semantic Clustering** using embedding similarity (nomic-embed-text) | `semantic similarity`, `text embeddings`, `cosine similarity`, `convergent reasoning`, `pairwise analysis` |
| What if agents think alike but use different words? | **Keyword-Based Sentiment Analysis** with domain-specific lexicons | `intent classification`, `domain-specific lexicons`, `cooperative vs competitive intent`, `intent drift detection` |
| Need per-agent, per-round behavioral labels | **Random Forest Classifier** (100 trees) with 9 engineered features | `ensemble learning`, `feature engineering`, `auto-labeling`, `behavioral profiling`, `strategy transitions` |
| Need early warning before collusion solidifies | **Linear Regression forecaster** with lagged features + momentum | `time-series forecasting`, `autoregressive prediction`, `feature engineering`, `confidence intervals`, `early warning system` |
| Need causal proof, not just correlation | **Demand Shock** (sting operation) — perturb one firm, observe cross-firm reactions | `causal inference`, `perturbation testing`, `exogenous shock`, `counterfactual analysis`, `coordination proof` |
| Need real-time monitoring for regulators | **WebSocket-based dashboard** with Chart.js live visualization | `real-time streaming`, `full-duplex communication`, `glassmorphism UI`, `live monitoring` |
| Need persistent data across experiments | **PostgreSQL 16 + pgvector** with 6 relational tables | `relational database`, `vector extension`, `IVFFlat index`, `approximate nearest neighbor`, `ACID compliance` |
| Need reproducible infrastructure | **Docker Compose** with health checks and auto-schema | `containerization`, `infrastructure as code`, `reproducibility`, `service orchestration` |

---

## 7.4 Keyword Glossary — Drop These During Viva

### 🏷️ Economics Keywords

| Keyword | What It Means | When to Use It |
|---------|--------------|----------------|
| **Algorithmic collusion** | AI pricing agents learn to keep prices high without human instruction | Problem statement, motivation |
| **Tacit coordination** | Cooperation without explicit communication | Describing what the agents do |
| **Supra-competitive pricing** | Prices above the competitive (Nash) level | Describing the result/finding |
| **Bertrand competition** | Firms compete by setting prices simultaneously | Describing our market model |
| **Nash Equilibrium** | Price where no firm wants to deviate unilaterally | Competitive benchmark |
| **Joint monopoly price** | Price that maximizes total industry profit | Cartel benchmark |
| **Oligopoly** | Market with few firms (ours: 5) | Market structure |
| **Price elasticity** | How much demand changes when price changes | MNL model explanation |
| **Outside option** | Customer's choice to not buy from any firm | Demand model details |
| **Market power** | Ability to influence prices | What collusion gives firms |
| **Welfare loss** | Economic harm to consumers from high prices | Why this matters |
| **Concerted practice** | Legal term for coordinated behavior | Why current law fails |
| **Symmetric oligopoly** | All firms have same cost and quality | Our model assumption |

### 🏷️ AI/ML Keywords

| Keyword | What It Means | When to Use It |
|---------|--------------|----------------|
| **Emergent behavior** | Complex outcomes arising from simple rules | The core finding — collusion "emerges" |
| **Multi-agent system** | Multiple AI agents interacting in shared environment | System architecture |
| **Reinforcement learning** | Learning from reward/punishment (no labeled data) | Q-Learning and DQN |
| **Temporal difference (TD) learning** | Update estimates based on the difference between predicted and actual | Bellman equation detail |
| **Function approximation** | Using neural nets instead of tables | Why DQN > Q-Learning |
| **Experience replay** | Training on shuffled past experiences | DQN training stability |
| **Target network** | Frozen copy to stabilize training | DQN oscillation prevention |
| **Epsilon-greedy exploration** | Random vs best-known action tradeoff | Exploration strategy |
| **Large Language Model (LLM)** | AI that understands and generates text (Llama 3) | Agent type 4 |
| **Prompt engineering** | Designing effective LLM instructions | How we get structured output |
| **Retrieval-Augmented Generation (RAG)** | Enhancing LLM with searchable memory | Agent type 5 |
| **Hybrid retrieval** | Combining vector search + SQL filters | Our RAG innovation |
| **Text embeddings** | Converting text to numerical vectors | Similarity search foundation |
| **Cosine similarity** | Measuring direction similarity between vectors | NLP clustering + RAG |
| **Ensemble learning** | Combining multiple models (Random Forest = 100 trees) | Strategy classifier |
| **Feature engineering** | Creating informative input variables from raw data | Classifier + forecaster |
| **Autoregressive forecasting** | Each prediction feeds into next prediction's input | Price forecaster |
| **Causal inference** | Proving cause-and-effect, not just correlation | Demand shock |
| **Zero-shot classification** | Classifying without task-specific training data | Sentiment analysis approach |
| **Domain-specific lexicons** | Custom keyword lists for our specific problem | Sentiment keyword lists |

### 🏷️ Systems/Infrastructure Keywords

| Keyword | What It Means | When to Use It |
|---------|--------------|----------------|
| **ASGI** | Async server interface (supports WebSocket) | Why FastAPI over Flask |
| **WebSocket** | Full-duplex real-time communication | Dashboard streaming |
| **REST API** | Standard HTTP request-response endpoints | Status, history, shock endpoints |
| **pgvector** | PostgreSQL vector similarity extension | RAG memory storage |
| **IVFFlat index** | Approximate nearest neighbor index | Fast vector search |
| **Docker Compose** | Multi-container orchestration | Infrastructure setup |
| **Containerization** | Packaging software with dependencies | Reproducibility |
| **Schema migration** | Auto-creating database tables on first run | Docker entrypoint |

---

## 7.5 Answer Frameworks — Structured Responses for Common Questions

### Framework 1: "What problem are you solving?"

```
HOOK:     "Companies like Amazon, Uber, and airlines use AI to set prices
           automatically — and these algorithms can learn to keep prices
           artificially high without any human telling them to."

PROBLEM:  "This is called ALGORITHMIC COLLUSION. It's a regulatory blind
           spot because current antitrust law requires proof of an
           AGREEMENT, but AI agents coordinate through EMERGENT BEHAVIOR
           — there's no agreement to find."

EVIDENCE: "In 2024, the US DOJ sued RealPage for exactly this — AI-driven
           rent pricing that allegedly inflated rents across competing
           landlords."

OUR WORK: "We built ECHO — a simulation framework that PROVES this happens
           across 4 different AI architectures, and a 6-method detection
           pipeline to CATCH it."
```

---

### Framework 2: "What is your novel contribution?"

```
"Three novel contributions:

FIRST — MULTI-ARCHITECTURE PROOF:
  We demonstrate that collusion emerges across FOUR fundamentally
  different AI architectures — LLM, Q-Learning, DQN, and RAG —
  through entirely different mechanisms. Calvano et al. tested
  only Q-Learning. Fish et al. tested only LLMs. We test ALL
  of them in the same environment, proving collusion is a
  MARKET-STRUCTURAL phenomenon, not algorithm-specific.

SECOND — HYBRID RAG WITH PROFIT-AWARE RETRIEVAL:
  Our smart_search() doesn't just find semantically similar past
  rounds — it combines VECTOR SIMILARITY with SQL STRUCTURAL
  FILTERS to retrieve similar rounds where the agent was
  PROFITABLE. This is a novel form of EXPERIENCE CURATION
  that standard RAG systems don't provide.

THIRD — 6-METHOD DETECTION PIPELINE:
  We combine statistical monitoring, NLP clustering, sentiment
  analysis, Random Forest classification, time-series forecasting,
  and causal perturbation testing into ONE unified dashboard.
  Each method provides a DIFFERENT TYPE OF EVIDENCE — price-level,
  reasoning-level, behavioral-level, predictive, and causal.
  No existing work combines all six."
```

---

### Framework 3: "How does [Agent X] work?"

**Template:**
```
ANALOGY:    "Think of it like [relatable analogy]..."
MECHANISM:  "Technically, it works by [core algorithm]..."
IN OUR CODE: "In our implementation, we [specific detail]..."
KEY FINDING: "The important result is [what we discovered]..."
```

**Example for LLM Agent:**
```
ANALOGY:    "Instead of a baby learning by trial and error, this is like
             hiring an MBA graduate to set prices. You hand them a market
             report and they write a memo before deciding."

MECHANISM:  "We use PROMPT ENGINEERING to give Llama 3 8B a structured
             task: system message defines the role, user message provides
             last 5 rounds of market history, and we enforce XML output
             format with <scratchpad> and <price> tags."

IN OUR CODE: "The prompt is built in _build_prompt(), Ollama is called
              via HTTP POST to /api/generate with temperature=0.7, and
              we parse the response using REGEX with fallback strategies."

KEY FINDING: "The terrifying finding is that the LLM invents COOPERATIVE
              REASONING on its own. It writes things like 'undercutting
              would start a price war' and 'maintaining stability benefits
              everyone' — nobody programmed this. It's EMERGENT BEHAVIOR
              from the intersection of language understanding and profit
              maximization."
```

---

### Framework 4: "Why do you have [X detection method]?"

**Template:**
```
LIMITATION: "[Previous method] can tell us [X], but it CAN'T tell us [Y]."
THIS METHOD: "[This method] fills that gap by [how it works]."
EVIDENCE TYPE: "It provides [type of evidence] — which is important because..."
```

**Example for Demand Shock:**
```
LIMITATION: "Lambda monitoring tells us PRICES ARE HIGH. NLP clustering
             tells us AGENTS THINK ALIKE. But neither proves CAUSATION.
             Maybe prices are just high by coincidence. Maybe agents
             happen to write similar text."

THIS METHOD: "The demand shock is a STING OPERATION. We artificially
              reduce one firm's product quality by 30% mid-simulation
              and watch if competitors react. In a fair market, only
              the shocked firm adjusts. If ALL firms react together,
              it CAUSALLY PROVES they were monitoring and responding
              to each other."

EVIDENCE TYPE: "This provides CAUSAL EVIDENCE — not correlation but
                causation. This is the type of evidence that holds up
                in antitrust court because it proves COORDINATION
                exists, which is the legal definition of a concerted
                practice under Competition Act Section 3."
```

---

### Framework 5: "What tech stack did you use and why?"

```
"Our stack was chosen for REPRODUCIBILITY, PERFORMANCE, and ALIGNMENT
with the research methodology:

SIMULATION CORE:
  Python 3.10+ with NumPy for numerical computation, SciPy for
  optimization (Nash/monopoly solvers), and a PURE-NUMPY neural
  network for DQN — no PyTorch dependency, reducing complexity.

AI/LLM LAYER:
  Ollama running Llama 3 8B locally for pricing decisions and
  nomic-embed-text for 768-dimensional text embeddings. LOCAL
  inference ensures data privacy and reproducibility.

DATABASE:
  PostgreSQL 16 with pgvector extension for dual-purpose storage:
  RELATIONAL data (rounds, prices, profits) in standard tables,
  and VECTOR data (768-dim embeddings) with IVFFlat cosine
  similarity index for RAG memory search.

ML/ANALYTICS:
  scikit-learn for Random Forest classification (100 estimators,
  balanced class weights) and Linear Regression forecasting with
  engineered time-series features.

REAL-TIME LAYER:
  FastAPI with ASGI (Uvicorn) for WebSocket streaming. Chart.js
  for real-time visualization. Vanilla HTML/CSS/JS dashboard with
  glassmorphism design.

INFRASTRUCTURE:
  Docker Compose for one-command reproducible deployment.
  PostgreSQL auto-initializes via schema.sql mounted as
  docker-entrypoint-initdb.d script."
```

---

### Framework 6: "What are your key results?"

```
"Four headline results:

RESULT 1 — LLM AGENTS COLLUDE MASSIVELY:
  Lambda reached 20.6 — meaning prices were 20× above the Nash-to-
  Monopoly gap. Agents priced at approximately 2× the competitive
  level. Scratchpad analysis reveals SPONTANEOUS COOPERATIVE
  REASONING — the LLM literally writes 'undercutting would start
  a price war' without any instruction to cooperate.

RESULT 2 — HEURISTIC BASELINE VALIDATES THE MODEL:
  Heuristic agents achieve Lambda ≈ 0.06 — virtually perfect
  competition. This confirms our Nash benchmark is correct and
  collusion is NOT an artifact of the simulation design.

RESULT 3 — COLLUSION IS ARCHITECTURE-AGNOSTIC:
  Both RL and DQN agents also converge to supra-competitive
  pricing through PURE REWARD OPTIMIZATION — no language, no
  reasoning, just Q-values. Combined with the LLM result, this
  proves collusion is a MARKET-STRUCTURAL PHENOMENON.

RESULT 4 — DETECTION PIPELINE WORKS:
  All 6 detection methods independently flag the collusive
  behavior: Lambda alerts trigger, NLP clustering shows
  convergent reasoning (similarity > 0.6), sentiment analysis
  detects cooperative intent drift, Random Forest labels
  'cooperative' strategy dominance, forecaster predicts
  continued price elevation, and demand shock reveals
  cross-firm coordination."
```

---

## 7.6 Question-Specific Power Answers

### "Why Multinomial Logit and not something simpler?"

> "The **Multinomial Logit (MNL)** model is the gold standard in **industrial organization** and **antitrust economics.** It's the same demand model used by the **CCI, EU Commission, and US FTC** in actual merger and cartel cases. Using it gives our simulation **legal and academic credibility.** A simpler model (like 'cheapest wins all') would be unrealistic because real customers have **heterogeneous preferences** — the MNL captures this through **stochastic utility** with a **Gumbel-distributed error term.** We also implement **log-sum-exp numerical stability** to handle the exponentials without overflow."

**Keywords:** `discrete choice`, `stochastic utility`, `Gumbel distribution`, `IIA property`, `log-sum-exp`, `industrial organization`

---

### "Why not use PyTorch for the DQN?"

> "We deliberately built a **pure-NumPy neural network** — forward pass, backpropagation, and Adam optimizer — from scratch. This was a **deliberate engineering decision** for three reasons: (1) it demonstrates **deep understanding** of the underlying mathematics, not just calling `model.fit()`, (2) it **eliminates a heavy dependency** (PyTorch is 2GB+), and (3) for our small network (5→64→32→15, ~5K parameters), NumPy is faster than PyTorch's overhead. We implemented **Xavier initialization** to prevent vanishing gradients and **experience replay with a deque buffer** exactly as described in the **DeepMind 2015 Nature paper.**"

**Keywords:** `from-scratch implementation`, `Xavier initialization`, `chain rule`, `gradient descent`, `Adam optimizer`, `Mnih et al. 2015`

---

### "What makes your RAG different from standard RAG?"

> "Standard RAG finds **semantically similar** documents — that's it. Our **Hybrid RAG** combines **vector cosine similarity** (pgvector `<=>` operator) with **SQL structural filters** in a **single query.** For example: 'Find past rounds similar to now **WHERE** my profit was above average **AND** the collusion index was above 0.3.' The agent doesn't just recall similar situations — it recalls similar situations **where it succeeded.** Our `smart_search()` function even **auto-selects the filtering strategy** based on the agent's current context: low profit → search for high-profit rounds; high lambda → search for profitable coordination rounds. This is **experience curation**, not just experience retrieval."

**Keywords:** `hybrid retrieval`, `structural filtering`, `profit-aware search`, `experience curation`, `context-adaptive strategy`, `pgvector cosine operator`

---

### "How do you ensure your results are valid?"

> "We validate at **three levels:**
>
> **(1) Internal validation:** Heuristic agents (our **control group**) achieve Λ ≈ 0.06, confirming our Nash benchmark is correct. If even simple agents showed high Λ, our model would be flawed.
>
> **(2) Cross-architecture validation:** Collusion emerges across **four independent architectures** (LLM, Q-Learning, DQN, RAG) — ruling out algorithm-specific artifacts.
>
> **(3) External validation:** We compute proxy collusion indices from **real-world data** — US gasoline prices (EIA via FRED API, Λ_proxy ≈ 0.91) and Amazon electronics pricing (Kaggle dataset, 42K listings, Λ_proxy ≈ 0.87) — showing our synthetic results are **consistent with real-market pricing patterns.**"

**Keywords:** `control group`, `null hypothesis`, `cross-validation`, `external validity`, `FRED API`, `empirical benchmarking`

---

### "What are the limitations of your project?"

> **(Be honest — professors respect this)**
>
> "(1) **Computational cost:** LLM inference is slow — each round takes ~2 seconds per agent with Ollama, limiting us to hundreds of rounds rather than the millions possible with RL agents.
>
> (2) **Simplified market:** We use **symmetric firms** (equal costs, equal quality). Real markets have **differentiated products**, **capacity constraints**, and **entry/exit dynamics** that we don't model.
>
> (3) **Single LLM:** We only test Llama 3 8B. Different models (GPT-4, Claude, Gemini) might exhibit different collusion patterns. This is future work.
>
> (4) **Auto-labeling bias:** Our Random Forest classifier is trained on **heuristic labels**, not human-annotated data. This introduces potential labeling bias."

**Keywords:** `computational bottleneck`, `symmetric assumption`, `generalizability`, `labeling bias`, `future work`

---

### "What is the future scope?"

> "(1) **Multi-model testing** — Run GPT-4, Claude, Gemini, and open-source models to see if collusion patterns are model-specific or universal.
>
> (2) **Asymmetric markets** — Different costs, qualities, and market shares for more realistic simulation.
>
> (3) **Communication channels** — What happens if agents can send messages to each other? Does explicit communication accelerate collusion?
>
> (4) **Regulatory interventions** — Test whether price caps, transparency mandates, or algorithmic auditing can prevent collusion.
>
> (5) **Real-time deployment** — Deploy the detection pipeline as a monitoring service that regulators can use on live pricing data from e-commerce platforms."

**Keywords:** `multi-model study`, `asymmetric oligopoly`, `inter-agent communication`, `regulatory intervention design`, `real-time monitoring`, `policy implications`

---

## 7.7 The 30-Second Elevator Pitch

**Memorize this. Use it when you have 30 seconds.**

> *"We proved that AI pricing agents — whether they're large language models, reinforcement learning, or deep neural networks — spontaneously learn to keep prices artificially high in a competitive market, without any human telling them to cooperate. This is called algorithmic collusion, and it's one of the biggest unsolved problems in competition law. We then built a six-method AI detective system that can detect, quantify, and causally prove this behavior — giving regulators the tools they need to protect consumers in an AI-driven economy."*

---

## 7.8 The 10-Second Version

> *"Five AI bots, told only to maximize profit, independently learn to charge cartel-level prices. We proved it happens and built six ways to catch it."*

---

## 7.9 Keyword Density Cheat Sheet

**The top 25 keywords to naturally drop throughout your viva:**

| # | Keyword | Drop When Talking About |
|---|---------|------------------------|
| 1 | **Algorithmic collusion** | Problem statement, results |
| 2 | **Emergent behavior** | How collusion happens |
| 3 | **Supra-competitive pricing** | What the agents do |
| 4 | **Nash Equilibrium** | Benchmark, Lambda formula |
| 5 | **Multinomial Logit** | Demand model |
| 6 | **Bellman equation** | Q-Learning core |
| 7 | **Experience replay** | DQN training |
| 8 | **Target network** | DQN stability |
| 9 | **Large Language Model** | Agent Type 4 |
| 10 | **Prompt engineering** | How we instruct the LLM |
| 11 | **Retrieval-Augmented Generation** | Agent Type 5 |
| 12 | **Hybrid retrieval** | Our RAG innovation |
| 13 | **Text embeddings** | NLP clustering, RAG |
| 14 | **Cosine similarity** | Measuring reasoning similarity |
| 15 | **Random Forest** | Strategy classification |
| 16 | **Feature engineering** | Classifier + forecaster inputs |
| 17 | **Causal inference** | Demand shock justification |
| 18 | **Perturbation testing** | Sting operation |
| 19 | **pgvector** | Vector database |
| 20 | **WebSocket** | Real-time dashboard |
| 21 | **Heterogeneous agents** | Why we test 4 AI types |
| 22 | **Multi-method detection** | Our detection contribution |
| 23 | **Temporal difference learning** | RL update rule |
| 24 | **Convergent reasoning** | What NLP clustering detects |
| 25 | **Regulatory blind spot** | Why the problem matters |
| 26 | **n8n / Workflow automation** | Automated alert pipeline, system integration |
