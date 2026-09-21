# ECHO

**Emergent Collusion in Heterogeneous Oligopolies**

A closed laboratory for *algorithmic tacit collusion*: five independent pricing programs post fares in a repeated Bertrand market. Nobody is told to collude. We measure how far the average price sits between competition and a cartel, and we try to detect that from the fare board.

This is not a legal finding and not a live ticket feed. The [Vercel demo](https://echo-green-pi.vercel.app) is static playback. The engine runs locally.

Python 3.10+ · FastAPI · NumPy DQN · Groq (`allam-2-7b`) · PostgreSQL / pgvector (optional)

---

## Why it exists

Airlines, ride-hailing, retail, and housing already let software set prices. A classical cartel is a meeting. **Tacit** collusion is quieter: separate profit-maximisers learn that price wars are expensive, so they keep prices high with no WhatsApp group and no shared weights. That is hard to prosecute. ECHO holds the market fixed, swaps only the *brain*, and asks whether learners sit above Nash—and whether an outsider can see it.

## How a round works

Named market (costs, quality, $\mu$) → each of five agents `choose_price` → logit demand (shares, profits) → $\Lambda$ vs this market’s Nash and monopoly → detectors / dashboard → repeat.

Agents see own cost, the trading band, and last prices and profits. They do not see rivals’ weights, Q-tables, or scratchpads.

## Demand and $\Lambda$

Multinomial logit (Anderson, de Palma, Thisse, 1992):

$$
s_i(p)=\frac{\exp((a_i-p_i)/\mu)}{\sum_j\exp((a_j-p_j)/\mu)+\exp(a_0/\mu)}
$$

$$
\pi_i=(p_i-c_i)\,s_i\,M
\qquad
\Lambda=\frac{\bar p-p_{\mathrm{Nash}}}{p_{\mathrm{Monopoly}}-p_{\mathrm{Nash}}}
$$

| | Meaning |
|---|---|
| $\mu$ | Price sensitivity (dataset-specific; not a global 0.25) |
| Nash | No firm wants to change price *alone* (fixed-point FOC) |
| Monopoly | One price maximising industry profit |
| $\Lambda\approx 0$ | Competitive |
| $\Lambda\approx 1$ | Joint-cartel prices |
| $M$ | Market size; orchestrator uses $1$ |

Trading band is cut from **this** market’s Nash–monopoly span (`resolve_price_band`), not a fixed rupee markup. $\Lambda$ is the official score; other sensors are supporting. A high $\Lambda$ is treated as serious only if it **lasts**.

## Agents

Same stage game, five minds. Heuristics are the control: if they already look like a cartel, the rulers are wrong.

| Mode | Implementation | Role |
|---|---|---|
| `dummy` | Steady / follower / undercut | No learning |
| `rl` | Tabular Q-learning, 15-rung grid | Calvano-style RL |
| `dqn` | NumPy MLP $5\to64\to32\to15$, replay, target net | Live demo |
| `llm` | Groq **Allam 2 7B**, `<scratchpad>` + `<price>` | Language as officer |
| `rag` | LLM + pgvector + Ollama embeddings | CLI only (`--db`) |

Dashboard modes: heuristic, Q-learning, DQN, LLM. RAG is not in the website dropdown.

Typical lab $\Lambda$ (order of magnitude, this engine): heuristic $\sim0.15$; Q-learning $\sim0.70$–$0.80$ after long $T$; DQN $\sim0.61$–$0.85$; LLM $\sim0.80$–$0.90$. Prompt never contains “collude.”

## Markets

Simulated Bertrand always draws the moving lines. Series calibrate costs / $\mu$ / names and may overlay. Failed live fetches set `is_fallback`; those runs are not empirical proof.

| Dataset | Calibration |
|---|---|
| `airlines` | DEL–BOM static params (IndiGo, Air India, SpiceJet, Vistara, Akasa). Demo market. |
| `gasoline` | BLS via FRED, five US divisions |
| `amazon` | Local CSV, wireless earbuds |
| `crypto` | CoinGecko BTC/USD venues |
| `rideshare` | Static Uber/Lyft-style costs |

A tightness proxy on real series is **not** the Nash-anchored $\Lambda$. Overlay $\neq$ “these firms collude.”

## Detection

| Sensor | Job |
|---|---|
| $\Lambda$ monitor | Streaks: watch $>0.3\times5$, warning $>0.5\times10$, alert $>0.7\times10$ |
| Quality shock | Cut one firm’s quality (15 / 30 / 50%). Co-movement is a lab sketch of coupling, not a court. |
| Scratchpad sentiment | LLM memos only |
| Strategy labels | Nine features; live path is rule-based unless a forest is trained. Can disagree with $\Lambda$. |
| Forecast | Lagged average prices at end of run |
| NLP clustering | In repo; not wired to the live API |
| n8n | Optional webhook on alerts |

End of run: `analysis/run_pack.py` wipes `analysis/latest_run/` and writes figures (prices, $\Lambda$, profits, shares, snapshot, optional real overlay, per-firm roster). Roster is a **lab** label.

## Layout

```
data_loaders → MarketContext → Nash / monopoly / band
     → 5 × PricingAgent → market/demand.py → Λ + monitors
     → FastAPI WebSocket → dashboard/app.html
     → optional Postgres / pgvector / n8n
```

`run_simulation.py` is the CLI. `api_server.py` is the live lab. Stack: SciPy, scikit-learn, Chart.js. Docker Compose: Postgres 16 + pgvector (host **5433**), n8n. Ollama is embeddings, not chat.

## Run

```bash
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO
pip install -r requirements.txt
```

`.env`: `GROQ_API_KEY=...` (LLM / RAG). Optional: `ECHO_DB_*`, `N8N_WEBHOOK_URL`.

```powershell
.\start_echo.ps1 quick      # UI only
.\start_echo.ps1            # Docker + checks + server
.\start_echo.ps1 fullrun    # sims, figures, server
```

Lab: [http://127.0.0.1:8000/dashboard/app.html](http://127.0.0.1:8000/dashboard/app.html)

```bash
python run_simulation.py --dataset airlines --mode dqn --rounds 500
python run_simulation.py --dataset airlines --mode rag --rounds 10 --db
```

## Limits

Simulated prices. $\Lambda$ is an index. Vercel is playback. Airlines / rideshare are parameters, not a GDS. FRED / CoinGecko can fall back. Live Random Forest is untrained. RAG and NLP-cluster are not on the main dropdown / live path.

## References

1. Calvano, E., Calzolari, G., Denicolò, V. & Pastorello, S. (2020). Artificial intelligence, algorithmic pricing, and collusion. *American Economic Review*.
2. Anderson, S. P., de Palma, A. & Thisse, J.-F. (1992). *Discrete Choice Theory of Product Differentiation*. MIT Press.
3. Mnih, V. et al. (2015). Human-level control through deep reinforcement learning. *Nature*.
4. Fish, S. et al. (2024). Algorithmic collusion by large language models.

## Authors

Aryan Raj (engine, agents, API, dashboard). Nikita Agarwal & Pranav Kudesia (documentation). MIT License.
