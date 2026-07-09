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
| `ollama` (commented) | `ollama/ollama:latest` | 11434 | LLM server (run on host for GPU) |

**Key Docker Compose features used:**
- `volumes` — persist data across restarts (`echo_pgdata`)
- `healthcheck` — wait for PostgreSQL to be ready before connecting
- `docker-entrypoint-initdb.d` — auto-runs `schema.sql` on first start
- Port mapping (`5433:5432`) — avoids conflict with host PostgreSQL

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
