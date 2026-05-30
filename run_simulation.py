"""
run_simulation.py -- ECHO Orchestrator

=== HOW TO RUN ===

    python run_simulation.py              # LLM agents (default, 10 rounds)
    python run_simulation.py --mode dummy  # heuristic agents (fast test)
    python run_simulation.py --rounds 50   # change number of rounds
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

    # If LLM agents, show last round's scratchpads
    if show_scratchpads:
        print("\n" + "=" * 80)
        print("LAST ROUND SCRATCHPADS (LLM reasoning)")
        print("=" * 80)
        for agent in engine.agents:
            if hasattr(agent, "scratchpad_history") and agent.scratchpad_history:
                print(f"\n--- Firm {agent.firm_id} ---")
                print(agent.scratchpad_history[-1])
        print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ECHO Simulation")
    parser.add_argument("--mode", choices=["llm", "dummy"], default="llm",
                        help="Agent type: 'llm' (Ollama) or 'dummy' (heuristic)")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of rounds to simulate")
    parser.add_argument("--db", action="store_true",
                        help="Save results to PostgreSQL (requires docker-compose up)")
    args = parser.parse_args()

    print("=" * 80)
    print("ECHO -- Emergent Collusion in Heterogeneous Oligopolies")
    print(f"Mode: {args.mode.upper()} agents | Rounds: {args.rounds} | DB: {'ON' if args.db else 'OFF'}")
    print("=" * 80)

    if args.mode == "llm":
        engine, n_rounds = build_llm_simulation(args.rounds)
    else:
        engine, n_rounds = build_dummy_simulation(args.rounds)

    # Database logging (optional)
    db_logger = None
    sim_id = None

    if args.db:
        from database.db import DatabaseLogger
        db_logger = DatabaseLogger()
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

    print_results(engine, show_scratchpads=(args.mode == "llm"))
