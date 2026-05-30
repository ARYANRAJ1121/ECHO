"""
market/engine.py -- The Simulation Loop (Bertrand Market Engine)

=== WHY DOES THIS FILE EXIST? ===

demand.py gives us the MATH (given prices -> compute shares/profits).
But who RUNS the game? Who asks agents for prices, passes them to the
demand model, records results, and repeats for 1000+ rounds?

That's this file. It's the "game master."

=== WHAT IT DOES ===

1. Each round: ask every agent "what price do you want?"
2. Clamp prices to legal bounds [price_floor, price_ceiling]
3. Pass prices to LogitDemandModel -> get shares, profits
4. Compute collusion index (Lambda)
5. Record everything
6. Give agents their results so they can learn
7. Repeat for N rounds

=== KEY DESIGN DECISIONS ===

- Agents get an Observation object (not raw arrays) -> clean interface
- Engine stores full history -> needed for analysis/plots later
- Price clamping prevents agents from posting absurd prices
- Engine is SYNCHRONOUS for now (Phase 5 adds async for LLM agents)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from agents.base_agent import Observation, PricingAgent
from market.demand import LogitDemandModel, DemandResult


@dataclass
class RoundRecord:
    """
    Everything that happened in one round of the game.
    One of these is created per round and stored in the history.
    """
    round_number: int
    prices: list[float]         # what each firm charged
    shares: list[float]         # what fraction of customers each got
    profits: list[float]        # how much money each made
    avg_price: float            # average price across all firms
    total_profit: float         # sum of all profits
    collusion_index: float      # Lambda: 0=competitive, 1=cartel
    outside_share: float        # fraction who didn't buy anything


class MarketEngine:
    """
    Runs the repeated Bertrand pricing game.

    Think of this as a referee: it collects prices from agents,
    runs the demand model, computes scores, and keeps history.

    Parameters
    ----------
    demand_model : LogitDemandModel
        The economic engine that computes shares/profits.
    agents : list[PricingAgent]
        The N firms competing in the market.
    price_floor : float
        Minimum legal price (must be >= marginal cost).
    price_ceiling : float
        Maximum legal price.
    """

    def __init__(
        self,
        demand_model: LogitDemandModel,
        agents: list[PricingAgent],
        price_floor: float = 1.0,
        price_ceiling: float = 10.0,
    ) -> None:
        if len(agents) != demand_model.n_firms:
            raise ValueError(
                f"Got {len(agents)} agents but demand model expects {demand_model.n_firms} firms."
            )

        self.demand_model = demand_model
        self.agents = agents
        self.price_floor = price_floor
        self.price_ceiling = price_ceiling

        # Pre-compute benchmarks (Nash and Monopoly prices)
        # These are computed ONCE and reused every round for Lambda calculation
        self.benchmarks = demand_model.get_benchmarks()

        # History storage -- grows by one entry per round
        self.price_history: list[list[float]] = []
        self.profit_history: list[list[float]] = []
        self.records: list[RoundRecord] = []

    def run(self, n_rounds: int) -> list[RoundRecord]:
        """
        Run the full simulation for n_rounds.

        Each round:
        1. Build Observation for each agent (what they can see)
        2. Ask each agent to choose a price
        3. Clamp prices to [floor, ceiling]
        4. Feed prices into demand model -> get market outcome
        5. Compute Lambda (collusion index)
        6. Store the record

        Returns the full list of round records.
        """
        print(f"\nRunning {n_rounds} rounds...")
        print(f"  Nash price:     {self.benchmarks.nash_price:.4f}")
        print(f"  Monopoly price: {self.benchmarks.monopoly_price:.4f}")
        print(f"  Price bounds:   [{self.price_floor:.2f}, {self.price_ceiling:.2f}]")
        print()

        for round_num in range(1, n_rounds + 1):
            record = self._run_one_round(round_num)
            self.records.append(record)
            self.price_history.append(record.prices)
            self.profit_history.append(record.profits)

            # Print progress every 10 rounds (or last round)
            if round_num % 10 == 0 or round_num == n_rounds:
                print(
                    f"  Round {round_num:4d} | "
                    f"Avg price: {record.avg_price:.4f} | "
                    f"Lambda: {record.collusion_index:.4f} | "
                    f"Total profit: {record.total_profit:.6f}"
                )

        return self.records

    def _run_one_round(self, round_number: int) -> RoundRecord:
        """Execute a single round of the game."""
        import numpy as np

        # Step 1: Collect prices from all agents
        prices = []
        for agent in self.agents:
            # Build what this agent can see
            obs = Observation(
                round_number=round_number,
                firm_id=agent.firm_id,
                marginal_cost=float(self.demand_model.costs[0]),
                price_floor=self.price_floor,
                price_ceiling=self.price_ceiling,
                price_history=self.price_history,
                profit_history=self.profit_history,
            )
            raw_price = agent.choose_price(obs)
            clamped = self._clamp(raw_price)
            prices.append(clamped)

        # Step 2: Feed prices into demand model
        price_array = np.array(prices, dtype=float)
        result: DemandResult = self.demand_model.compute(price_array)

        # Step 3: Compute collusion index
        avg_price = float(price_array.mean())
        collusion_idx = self.demand_model.collusion_index(avg_price)

        return RoundRecord(
            round_number=round_number,
            prices=result.prices.tolist(),
            shares=result.shares.tolist(),
            profits=result.profits.tolist(),
            avg_price=avg_price,
            total_profit=result.total_profit,
            collusion_index=collusion_idx,
            outside_share=result.outside_share,
        )

    def _clamp(self, price: float) -> float:
        """Keep price within legal bounds."""
        return max(self.price_floor, min(self.price_ceiling, round(price, 4)))

    def summary(self) -> dict:
        """
        Summary statistics for the full simulation run.
        Called once at the end to get the headline numbers.
        """
        if not self.records:
            return {}

        lambdas = [r.collusion_index for r in self.records]

        # When did Lambda first cross 0.7? (collusion threshold)
        convergence_round = None
        for r in self.records:
            if r.collusion_index >= 0.7:
                convergence_round = r.round_number
                break

        # Average Lambda in the last 20% of rounds
        tail_start = max(1, int(len(lambdas) * 0.8))
        converged_lambda = sum(lambdas[tail_start:]) / max(1, len(lambdas[tail_start:]))

        return {
            "rounds_completed": len(self.records),
            "nash_price": self.benchmarks.nash_price,
            "monopoly_price": self.benchmarks.monopoly_price,
            "final_avg_price": self.records[-1].avg_price,
            "final_collusion_index": self.records[-1].collusion_index,
            "converged_collusion_index": converged_lambda,
            "peak_collusion_index": max(lambdas),
            "convergence_round": convergence_round,
        }
