"""
run_simulation.py -- ECHO Orchestrator

=== WHY DOES THIS FILE EXIST? ===

This is the ENTRY POINT. You type `python run_simulation.py` and
the entire simulation runs. It wires everything together:

1. Creates the demand model (the economy)
2. Creates the agents (the firms)
3. Creates the engine (the referee)
4. Runs N rounds
5. Prints results

Right now it uses DUMMY agents (heuristic rules).
Later we'll swap in LLM agents and RL agents.

=== HOW TO RUN ===

    cd antitrust_sim
    python run_simulation.py
"""

from __future__ import annotations

from agents.heuristic_agent import SteadyAgent, FollowerAgent, UndercutAgent
from market.demand import LogitDemandModel
from market.engine import MarketEngine


def build_simulation() -> MarketEngine:
    """
    Wire up all components and return a ready-to-run engine.

    Current setup: 5 dummy agents with different strategies.
    This is Phase 1-2 -- just proving the math + engine work.
    """

    # The economy: 5 symmetric firms, mu=0.5 (moderate price sensitivity)
    demand_model = LogitDemandModel(
        n_firms=5,
        mu=0.5,
        marginal_cost=1.0,
        quality=None,           # all firms equal quality
        outside_quality=0.0,
        market_size=1.0,
    )

    # The firms: 5 different heuristic strategies
    agents = [
        SteadyAgent(firm_id=0, markup=0.5),         # always charges cost + 0.5
        FollowerAgent(firm_id=1, target_markup=0.6, adjustment_speed=0.5),  # follows avg price
        UndercutAgent(firm_id=2, undercut_amount=0.05, safe_markup=0.3),    # undercuts cheapest
        FollowerAgent(firm_id=3, target_markup=0.4, adjustment_speed=0.3),  # slower follower
        SteadyAgent(firm_id=4, markup=0.7),          # charges more (premium brand)
    ]

    return MarketEngine(
        demand_model=demand_model,
        agents=agents,
        price_floor=1.0,        # can't go below cost
        price_ceiling=5.0,      # reasonable upper bound
    )


def print_results(engine: MarketEngine) -> None:
    """Print a clean summary of the simulation."""
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
    print(f"  Rounds completed:        {summary['rounds_completed']}")
    print(f"  Nash benchmark price:    {summary['nash_price']:.4f}")
    print(f"  Monopoly benchmark:      {summary['monopoly_price']:.4f}")
    print(f"  Final avg price:         {summary['final_avg_price']:.4f}")
    print(f"  Final Lambda:            {summary['final_collusion_index']:.4f}")
    print(f"  Converged Lambda (last 20%): {summary['converged_collusion_index']:.4f}")
    print(f"  Peak Lambda:             {summary['peak_collusion_index']:.4f}")
    print(f"  Convergence round (>0.7): {summary['convergence_round']}")
    print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("ECHO -- Emergent Collusion in Heterogeneous Oligopolies")
    print("Phase 1-2: Market Engine + Heuristic Agents (No LLM, No DB)")
    print("=" * 80)

    engine = build_simulation()
    engine.run(n_rounds=50)
    print_results(engine)
