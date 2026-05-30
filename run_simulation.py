from __future__ import annotations

from agents.heuristic_agent import FollowerAgent, SteadyAgent, UndercutAgent
from market.demand import LogitDemandModel
from market.engine import MarketConfig, MarketEngine


def build_simulation() -> MarketEngine:
    config = MarketConfig(
        n_firms=5,
        rounds=25,
        price_floor=10.0,
        price_ceiling=20.0,
        marginal_cost=10.0,
    )

    demand_model = LogitDemandModel(
        market_size=1000.0,
        price_sensitivity=0.35,
        qualities=[6.0, 6.0, 6.0, 6.0, 6.0],
        marginal_costs=[10.0, 10.0, 10.0, 10.0, 10.0],
        outside_option_utility=0.0,
    )

    agents = [
        SteadyAgent(firm_id=0, markup=2.0),
        FollowerAgent(firm_id=1, target_markup=2.2, adjustment_speed=0.6),
        UndercutAgent(firm_id=2, undercut_amount=0.15, safe_markup=1.2),
        FollowerAgent(firm_id=3, target_markup=1.8, adjustment_speed=0.4),
        SteadyAgent(firm_id=4, markup=2.5),
    ]

    return MarketEngine(config=config, demand_model=demand_model, agents=agents)


def print_round_table(records) -> None:
    print("\nRound-by-round results")
    print("-" * 78)
    print(f"{'Round':>5}  {'AvgPrice':>8}  {'TotProfit':>10}  {'Collusion':>9}  Prices")
    print("-" * 78)

    for record in records:
        price_text = ", ".join(f"{price:.2f}" for price in record.prices)
        print(
            f"{record.round_number:>5}  "
            f"{record.avg_price:>8.2f}  "
            f"{record.total_profit:>10.2f}  "
            f"{record.collusion_index:>9.2f}  "
            f"[{price_text}]"
        )


def print_summary(summary: dict[str, float | int | None]) -> None:
    print("\nSummary")
    print("-" * 40)
    print(f"Rounds completed:       {summary['rounds_completed']}")
    print(f"Nash benchmark price:   {summary['nash_price']:.2f}")
    print(f"Monopoly benchmark:     {summary['monopoly_price']:.2f}")
    print(f"Final average price:    {summary['final_avg_price']:.2f}")
    print(f"Final total profit:     {summary['final_total_profit']:.2f}")
    print(f"Final collusion index:  {summary['final_collusion_index']:.2f}")
    print(f"Average collusion idx:  {summary['average_collusion_index']:.2f}")
    print(f"Convergence round:      {summary['convergence_round']}")


if __name__ == "__main__":
    engine = build_simulation()
    records = engine.run()
    summary = engine.summary()

    print("Starter simulation for the antitrust project")
    print_round_table(records)
    print_summary(summary)
