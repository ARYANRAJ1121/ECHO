"""
run_simulation.py -- ECHO Orchestrator

=== HOW TO RUN ===

    python run_simulation.py --mode dummy --rounds 50      # heuristic (fast)
    python run_simulation.py --mode llm --rounds 10        # LLM agents
    python run_simulation.py --mode rag --rounds 10 --db   # RAG agents (needs DB)
"""

from __future__ import annotations
import argparse

from market.demand import LogitDemandModel
from market.engine import MarketEngine


def build_llm_simulation(n_rounds: int) -> tuple[MarketEngine, int]:
    """Wire up 5 LLM agents talking to Ollama."""
    from agents.llm_agent import LLMPricingAgent

    demand_model = LogitDemandModel(
        n_firms=5,
        mu=0.5,
        marginal_cost=1.0,
        quality=None,
        outside_quality=0.0,
        market_size=1.0,
    )

    agents = [
        LLMPricingAgent(firm_id=i, model="llama3", temperature=0.7)
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=5.0,
    )

    return engine, n_rounds


def build_rag_simulation(n_rounds: int, sim_id: int) -> tuple[MarketEngine, int]:
    """
    Wire up 5 RAG-enhanced LLM agents.

    Requires PostgreSQL running (for pgvector) and Ollama running
    (for both LLM inference and nomic-embed-text embeddings).
    """
    from agents.rag_agent import RAGPricingAgent
    from database.memory import VectorMemory

    demand_model = LogitDemandModel(
        n_firms=5,
        mu=0.5,
        marginal_cost=1.0,
        quality=None,
        outside_quality=0.0,
        market_size=1.0,
    )

    # Shared memory store (all agents write/read from same pgvector)
    memory = VectorMemory()

    agents = [
        RAGPricingAgent(
            firm_id=i,
            memory=memory,
            sim_id=sim_id,
            top_k=3,
            model="llama3",
            temperature=0.7,
        )
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=5.0,
    )

    return engine, n_rounds


def build_dummy_simulation(n_rounds: int) -> tuple[MarketEngine, int]:
    """Wire up 5 heuristic agents (fast, no LLM needed)."""
    from agents.heuristic_agent import SteadyAgent, FollowerAgent, UndercutAgent

    demand_model = LogitDemandModel(
        n_firms=5,
        mu=0.5,
        marginal_cost=1.0,
        quality=None,
        outside_quality=0.0,
        market_size=1.0,
    )

    agents = [
        SteadyAgent(firm_id=0, markup=0.5),
        FollowerAgent(firm_id=1, target_markup=0.6, adjustment_speed=0.5),
        UndercutAgent(firm_id=2, undercut_amount=0.05, safe_markup=0.3),
        FollowerAgent(firm_id=3, target_markup=0.4, adjustment_speed=0.3),
        SteadyAgent(firm_id=4, markup=0.7),
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=5.0,
    )

    return engine, n_rounds


def build_rl_simulation(n_rounds: int) -> tuple[MarketEngine, int]:
    """
    Wire up 5 Q-Learning agents (Calvano 2020 replication).

    No GPU needed. Pure tabular Q-learning.
    Needs ~10,000+ rounds to converge.
    """
    from agents.rl_agent import QLearningAgent

    demand_model = LogitDemandModel(
        n_firms=5,
        mu=0.5,
        marginal_cost=1.0,
        quality=None,
        outside_quality=0.0,
        market_size=1.0,
    )

    agents = [
        QLearningAgent(
            firm_id=i,
            n_prices=15,
            alpha=0.15,
            gamma=0.95,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.99995,
            price_floor=1.0,
            price_ceiling=5.0,
        )
        for i in range(5)
    ]

    engine = MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=1.0,
        price_ceiling=5.0,
    )

    return engine, n_rounds


def print_results(engine: MarketEngine, show_scratchpads: bool = False) -> None:
    """Print simulation results."""
    records = engine.records
    summary = engine.summary()

    # Per-round table
    print("\n" + "=" * 80)
    print("ROUND-BY-ROUND RESULTS")
    print("=" * 80)
    print(f"{'Round':>5}  {'AvgPrice':>9}  {'Lambda':>7}  {'TotProfit':>10}  Prices")
    print("-" * 80)

    for r in records:
        price_str = ", ".join(f"{p:.3f}" for p in r.prices)
        print(
            f"{r.round_number:>5}  "
            f"{r.avg_price:>9.4f}  "
            f"{r.collusion_index:>7.4f}  "
            f"{r.total_profit:>10.6f}  "
            f"[{price_str}]"
        )

    # Summary
    print("\n" + "=" * 80)
    print("SIMULATION SUMMARY")
    print("=" * 80)
    print(f"  Rounds completed:         {summary['rounds_completed']}")
    print(f"  Nash benchmark price:     {summary['nash_price']:.4f}")
    print(f"  Monopoly benchmark:       {summary['monopoly_price']:.4f}")
    print(f"  Final avg price:          {summary['final_avg_price']:.4f}")
    print(f"  Final Lambda:             {summary['final_collusion_index']:.4f}")
    print(f"  Converged Lambda (last 20%): {summary['converged_collusion_index']:.4f}")
    print(f"  Peak Lambda:              {summary['peak_collusion_index']:.4f}")
    print(f"  Convergence round (>0.7): {summary['convergence_round']}")
    print("=" * 80)

    # Show last round's scratchpads for LLM/RAG agents
    if show_scratchpads:
        print("\n" + "=" * 80)
        print("LAST ROUND SCRATCHPADS (Agent reasoning)")
        print("=" * 80)
        for agent in engine.agents:
            if hasattr(agent, "scratchpad_history") and agent.scratchpad_history:
                print(f"\n--- {agent.name} ---")
                print(agent.scratchpad_history[-1])
        print("=" * 80)

    # Show RL agent stats if applicable
    rl_agents = [a for a in engine.agents if hasattr(a, "stats")]
    if rl_agents:
        print("\n" + "=" * 80)
        print("RL AGENT STATS")
        print("=" * 80)
        for agent in rl_agents:
            stats = agent.stats()
            print(f"  {agent.name}: {stats['total_q_updates']} updates | "
                  f"{stats['q_table_size']} states discovered | "
                  f"final epsilon: {stats['final_epsilon']:.4f}")
        print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ECHO Simulation")
    parser.add_argument("--mode", choices=["llm", "dummy", "rag", "rl"], default="llm",
                        help="Agent type: 'llm', 'rag' (with memory), or 'dummy' (heuristic)")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of rounds to simulate (use 10000+ for RL)")
    parser.add_argument("--db", action="store_true",
                        help="Save results to PostgreSQL (required for --mode rag)")
    parser.add_argument("--validate", action="store_true",
                        help="Run Phase 1.5 empirical validation after simulation")
    args = parser.parse_args()

    # RAG mode requires database
    if args.mode == "rag" and not args.db:
        print("RAG mode requires --db flag (needs PostgreSQL for pgvector).")
        print("Usage: python run_simulation.py --mode rag --rounds 10 --db")
        exit(1)

    print("=" * 80)
    print("ECHO -- Emergent Collusion in Heterogeneous Oligopolies")
    print(f"Mode: {args.mode.upper()} agents | Rounds: {args.rounds} | DB: {'ON' if args.db else 'OFF'}")
    print("=" * 80)

    # Database logging (optional, required for RAG)
    db_logger = None
    sim_id = None

    if args.db:
        from database.db import DatabaseLogger
        db_logger = DatabaseLogger()

    # Build simulation
    if args.mode == "rag":
        # RAG needs sim_id upfront (agents need it for memory isolation)
        sim_id = db_logger.start_simulation({
            "mode": "rag",
            "n_firms": 5,
            "n_rounds": args.rounds,
            "mu": 0.5,
            "marginal_cost": 1.0,
        })
        engine, n_rounds = build_rag_simulation(args.rounds, sim_id=sim_id)
        # Update benchmarks after engine is created
        db_logger.conn.cursor().execute(
            "UPDATE simulations SET nash_price=%s, monopoly_price=%s WHERE sim_id=%s",
            (engine.benchmarks.nash_price, engine.benchmarks.monopoly_price, sim_id),
        )
        db_logger.conn.commit()
    elif args.mode == "llm":
        engine, n_rounds = build_llm_simulation(args.rounds)
    elif args.mode == "rl":
        engine, n_rounds = build_rl_simulation(args.rounds)
    else:
        engine, n_rounds = build_dummy_simulation(args.rounds)

    # Start sim in DB (for non-RAG modes)
    if args.db and sim_id is None:
        sim_id = db_logger.start_simulation({
            "mode": args.mode,
            "n_firms": 5,
            "n_rounds": args.rounds,
            "mu": 0.5,
            "marginal_cost": 1.0,
            "nash_price": engine.benchmarks.nash_price,
            "monopoly_price": engine.benchmarks.monopoly_price,
        })

    engine.run(n_rounds=n_rounds, db_logger=db_logger, sim_id=sim_id)

    if db_logger:
        db_logger.end_simulation(sim_id)
        db_logger.close()

    print_results(engine, show_scratchpads=(args.mode in ("llm", "rag")))

    # --- Antitrust Regulator: Lambda Monitor ---
    from regulator.detector import LambdaMonitor

    monitor = LambdaMonitor()
    for record in engine.records:
        alerts = monitor.observe(record.round_number, record.collusion_index)
        for alert in alerts:
            print(f"  *** {alert.detail}")

    report = monitor.report()
    print("\n" + "=" * 80)
    print("REGULATOR REPORT (Lambda Monitor)")
    print("=" * 80)
    print(f"  Rounds analyzed:     {report['total_rounds']}")
    print(f"  Mean Lambda:         {report['mean_lambda']:.4f}")
    print(f"  Peak Lambda:         {report['peak_lambda']:.4f}")
    print(f"  Final Lambda:        {report['final_lambda']:.4f}")
    print(f"  Rolling avg (50r):   {report['rolling_avg']:.4f}")
    print(f"  Trend:               {report['trend']}")
    print(f"  Total alerts:        {report['total_alerts']}")
    print(f"    Watch (low):       {report['alert_breakdown']['watch']}")
    print(f"    Warning (medium):  {report['alert_breakdown']['warning']}")
    print(f"    Alert (high):      {report['alert_breakdown']['alert']}")
    if report['first_alert_round']:
        print(f"  First alert round:   {report['first_alert_round']}")
    print("=" * 80)

    # --- Phase 1.5: Empirical Validation ---
    if args.validate:
        from analysis.real_data import run_validation
        summary = engine.summary()
        sim_lambda = summary['converged_collusion_index']
        run_validation(sim_lambda=sim_lambda)
