# ECHO -- Emergent Collusion in Heterogeneous Oligopolies

> A research framework for detecting emergent tacit collusion in autonomous AI pricing agents operating in Bertrand oligopolies.

## What is this?

ECHO is a computational framework that simulates a market where 5 AI agents (LLMs, RL agents) independently set prices for competing products. We study whether these agents **spontaneously learn to fix prices** -- forming illegal cartels -- without any explicit communication or instruction to collude.

This is a real-world problem: in 2024, US landlords were sued because their AI pricing software (RealPage) was autonomously fixing rents. ECHO provides the research infrastructure to study this computationally.

## Architecture

```
                    ECHO Framework

    +---------------------------------------------+
    |           ANTITRUST REGULATOR                |
    |  Collusion Index + NLP Clustering +          |
    |  Demand Shock Perturbation Tests             |
    +----------------------+----------------------+
                           | observes
    +----------------------v----------------------+
    |          BERTRAND MARKET ENGINE              |
    |  Logit Demand -> Shares -> Profits -> L     |
    +--------+-----------------------+------------+
             | prices                | results
    +--------v-----------------------v------------+
    |            AGENT SWARM                       |
    |  5 x Heterogeneous Pricing Agents            |
    |  (LLM / RL / Rule-based)                    |
    +---------------------------------------------+
```

## Key Metric: Collusion Index (Lambda)

```
Lambda = (avg_price - nash_price) / (monopoly_price - nash_price)
```

| Lambda | Interpretation |
|--------|---------------|
| 0.0 | Competitive (Bertrand-Nash Equilibrium) |
| 0.0 - 0.3 | Healthy competition |
| 0.3 - 0.7 | Ambiguous / partial coordination |
| 0.7 - 1.0 | Tacit collusion detected |
| 1.0 | Full cartel (Joint Monopoly) |

## Project Structure

```
echo/
+-- market/
|   +-- demand.py          # Logit demand model + Nash/Monopoly solvers
|   +-- engine.py          # Bertrand simulation loop
+-- agents/
|   +-- base_agent.py      # Abstract pricing agent interface
|   +-- llm_agent.py       # LLM-powered agent (Ollama)
|   +-- rl_agent.py        # Q-learning baseline agent
+-- regulator/
|   +-- detector.py        # Collusion detection pipeline
|   +-- nlp_cluster.py     # Scratchpad semantic analysis
|   +-- perturbation.py    # Demand shock testing
+-- database/              # PostgreSQL + pgvector storage
+-- rag/                   # Retrieval-Augmented Generation memory
+-- analysis/              # Research-grade plotting
+-- config/                # Simulation hyperparameters
```

## Tech Stack

- **Python** -- simulation engine
- **Llama 3.1 8B** via Ollama -- local LLM inference
- **PostgreSQL + pgvector** -- data storage + vector similarity search
- **Docker Compose** -- reproducible infrastructure
- **sentence-transformers** -- semantic embeddings

## Research Contribution

1. **RAG vs No-RAG Ablation**: First study testing whether episodic memory amplifies LLM collusion
2. **Heterogeneous Agent Comparison**: LLM agents vs RL agents in the same market
3. **Causal Perturbation Testing**: Demand shocks to prove agents are executing cartel mechanics
4. **Semantic Scratchpad Analysis**: Detecting reasoning convergence across agents

## References

- Calvano et al. (2020). *Artificial Intelligence, Algorithmic Pricing, and Collusion.* American Economic Review.
- Anderson, de Palma, Thisse (1992). *Discrete Choice Theory of Product Differentiation.* MIT Press.

## Author

Aryan Raj

## License

MIT
