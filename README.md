# ECHO

### Emergent Collusion in Heterogeneous Oligopolies

A research framework that studies whether autonomous AI pricing agents spontaneously develop **illegal cartel behavior** without explicit communication or instruction.

---

## The Problem

Companies already deploy AI pricing bots (Amazon, Uber, airlines). In 2024, the DOJ sued landlords whose AI software ([RealPage](https://www.justice.gov/opa/pr/justice-department-sues-realpage-algorithmic-pricing-scheme-harms-millions-renters)) was autonomously fixing rents. The question nobody can answer yet:

> **When you put multiple AI agents in a competitive market and tell each one "maximize your profit," do they independently learn to form a cartel?**

ECHO answers this computationally.

---

## What ECHO Does

1. **Simulates a market** with 5 competing firms using a Multinomial Logit Demand model
2. **Deploys AI agents** (LLM-powered via Llama 3 8B) that independently set prices each round
3. **Measures collusion** using the Lambda index, NLP scratchpad analysis, and demand shock tests
4. **Compares agent types**: LLM agents vs Q-Learning RL agents vs rule-based heuristics

---

## Key Finding (Preliminary)

| Agent Type | Lambda (Collusion Index) | Interpretation |
|-----------|--------------------------|----------------|
| Heuristic (rule-based) | **0.06** | Competitive. No collusion. |
| LLM (Llama 3 8B) | **20.6** | Prices far above cartel level. |

> After just 3 rounds, LLM agents priced at **2x-3x** the competitive equilibrium. Their scratchpads revealed reasoning like: *"I notice competitors tend to set similar prices... I'll set mine just below theirs"* -- textbook tacit collusion, without any instruction to collude.

---

## The Collusion Index (Lambda)

The single most important metric in the project:

```
Lambda = (avg_price - nash_price) / (monopoly_price - nash_price)
```

| Lambda | Market State |
|--------|-------------|
| 0.0 | Bertrand-Nash Equilibrium (healthy competition) |
| 0.3 | Mild coordination |
| 0.7 | Collusion threshold (detection trigger) |
| 1.0 | Joint Monopoly (full cartel) |
| > 1.0 | Agents overshooting monopoly price |

---

## Architecture

```
ECHO Framework

+---------------------------------------------+
|           ANTITRUST REGULATOR                |
|   Lambda Monitor                             |
|   Scratchpad NLP Clustering                  |
|   Demand Shock Perturbation Tests            |
+----------------------+-----------------------+
                       | observes
+----------------------v-----------------------+
|          BERTRAND MARKET ENGINE               |
|   Logit Demand -> Shares -> Profits -> L     |
+--------+------------------------+------------+
         | prices                 | results
+--------v------------------------v------------+
|             AGENT SWARM                       |
|   5 x Heterogeneous Pricing Agents            |
|   LLM (Llama 3) | RL (Q-Learning) | Rules   |
+----------------------------------------------+
         |                        |
+--------v---------+   +----------v-----------+
|   RAG Memory     |   |    PostgreSQL         |
|   (pgvector)     |   |    + pgvector         |
+------------------+   +----------------------+
```

---

## Project Structure

```
echo/
|-- market/
|   |-- demand.py            # Logit demand model + Nash/Monopoly solvers
|   |-- engine.py            # Bertrand game simulation loop
|
|-- agents/
|   |-- base_agent.py        # Abstract pricing agent interface
|   |-- heuristic_agent.py   # Rule-based agents (Steady, Follower, Undercut)
|   |-- llm_agent.py         # LLM-powered agent (Ollama + Llama 3)
|   |-- rl_agent.py          # Q-Learning baseline agent (planned)
|   |-- rag_agent.py         # RAG-enhanced LLM agent (planned)
|
|-- regulator/               # Collusion detection pipeline (planned)
|   |-- detector.py          # Lambda monitoring + alerts
|   |-- nlp_cluster.py       # Scratchpad semantic analysis
|   |-- perturbation.py      # Demand shock causal testing
|
|-- database/                # PostgreSQL integration (planned)
|-- analysis/                # Research-grade plotting (planned)
|-- api/                     # FastAPI backend (planned)
|-- dashboard/               # Streamlit live dashboard (planned)
|
|-- run_simulation.py        # Main entry point
|-- todo.md                  # Development roadmap
|-- docker-compose.yml       # One-command deployment (planned)
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/ARYANRAJ1121/ECHO.git
cd ECHO

# Run with dummy agents (no GPU needed, instant)
python run_simulation.py --mode dummy --rounds 50

# Run with LLM agents (requires Ollama + Llama 3)
# Terminal 1: start Ollama server
ollama serve

# Terminal 2: run simulation
python run_simulation.py --mode llm --rounds 10
```

### Requirements
- Python 3.10+
- NumPy, SciPy, Requests
- [Ollama](https://ollama.com/) (for LLM agents)
- Llama 3 8B model (`ollama pull llama3`)

---

## Research Contributions

1. **LLM Tacit Collusion**: Demonstrating that language model agents autonomously develop cartel-like pricing without instruction
2. **RAG vs No-RAG Ablation**: First study testing whether episodic memory accelerates AI collusion
3. **Heterogeneous Agent Comparison**: LLM vs RL vs heuristic agents in identical market conditions
4. **Causal Detection**: Demand shock perturbation tests that provide causal evidence of coordination
5. **Scratchpad Analysis**: Using NLP to detect convergent reasoning across independent agents

---

## Theoretical Foundation

- **Demand Model**: Multinomial Logit (Anderson, de Palma, Thisse 1992)
- **Equilibrium Concepts**: Bertrand-Nash for competition, Joint Monopoly for cartel benchmark
- **Collusion Metric**: Lambda index (Calvano et al. 2020)
- **Agent Architecture**: Structured prompting with scratchpad reasoning (Fish et al. 2025)

### References

- Calvano, E., Calzolari, G., Denicolo, V., & Pastorello, S. (2020). *Artificial Intelligence, Algorithmic Pricing, and Collusion.* American Economic Review, 110(10), 3267-3297.
- Anderson, S., de Palma, A., & Thisse, J. (1992). *Discrete Choice Theory of Product Differentiation.* MIT Press.
- Fish, S., et al. (2025). *Algorithmic Collusion by Large Language Models.* arXiv preprint.

---

## Development Roadmap

See [todo.md](todo.md) for the full development plan.

| Phase | Description | Status |
|-------|------------|--------|
| 1. Foundation | Market engine + heuristic agents | Done |
| 2. Infrastructure | Docker + PostgreSQL + pgvector | Next |
| 3. LLM Agents | Llama 3 via Ollama | Done |
| 4. RAG Memory | Episodic memory + A/B testing | Planned |
| 5. Antitrust Detective | 3-method detection pipeline | Planned |
| 6. RL Baseline | Q-Learning comparison agents | Planned |
| 7. Analysis | Research-grade figures | Planned |
| 8. Dashboard | FastAPI + Streamlit live demo | Planned |

---

## Author

**Aryan Raj**

## License

MIT
