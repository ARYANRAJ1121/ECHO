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
from market.policy import PolicyConfig


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
    raw_prices: list[float] = field(default_factory=list)          # prices chosen before regulatory cap
    consumer_savings: float = 0.0                                 # currency saved by consumers due to price cap
    leniency_recipients: list[int] = field(default_factory=list)  # firms receiving antitrust defector bonuses
    is_policy_active: bool = False                                # whether policy remedy was active this round


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
    policy : PolicyConfig, optional
        Regulatory policy counterfactual (price cap, delayed transparency, leniency).
    """

    def __init__(
        self,
        demand_model: LogitDemandModel,
        agents: list[PricingAgent],
        price_floor: float = 1.0,
        price_ceiling: float = 10.0,
        policy: PolicyConfig | None = None,
    ) -> None:
        if len(agents) != demand_model.n_firms:
            raise ValueError(
                f"Got {len(agents)} agents but demand model expects {demand_model.n_firms} firms."
            )
        self.demand_model = demand_model  
        self.agents = agents
        self.price_floor = price_floor
        self.price_ceiling = price_ceiling
        self.policy = policy

        # Pre-compute benchmarks (Nash and Monopoly prices)
        # These are computed ONCE and reused every round for Lambda calculation
        self.benchmarks = demand_model.get_benchmarks()

        # History storage -- grows by one entry per round
        self.price_history: list[list[float]] = []
        self.profit_history: list[list[float]] = []
        self.records: list[RoundRecord] = []

    def run(self, n_rounds: int, db_logger=None, sim_id: int | None = None) -> list[RoundRecord]:
        """
        Run the full simulation for n_rounds.

        Each round:
        1. Build Observation for each agent (what they can see)
        2. Ask each agent to choose a price
        3. Clamp prices to [floor, ceiling]
        4. Feed prices into demand model -> get market outcome
        5. Compute Lambda (collusion index)
        6. Store the record
        7. (Optional) Save to PostgreSQL via db_logger

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

            # Save to database if logger is provided
            if db_logger and sim_id is not None:
                # Collect scratchpads from LLM agents (if any)
                scratchpads = {}
                response_times = {}
                for agent in self.agents:
                    if hasattr(agent, "scratchpad_history") and agent.scratchpad_history:
                        scratchpads[agent.firm_id] = agent.scratchpad_history[-1]
                    if hasattr(agent, "response_times") and agent.response_times:
                        response_times[agent.firm_id] = agent.response_times[-1]

                db_logger.log_round(
                    sim_id=sim_id,
                    record=record,
                    scratchpads=scratchpads if scratchpads else None,
                    response_times=response_times if response_times else None,
                )

            # Store in RAG memory for agents that support it
            for agent in self.agents:
                if hasattr(agent, "store_round_memory"):
                    try:
                        obs = Observation(
                            round_number=round_num,
                            firm_id=agent.firm_id,
                            marginal_cost=float(self.demand_model.costs[agent.firm_id]),
                            price_floor=self.price_floor,
                            price_ceiling=self.price_ceiling,
                            price_history=self.price_history,
                            profit_history=self.profit_history,
                        )
                        # round_id from DB or use round_num as fallback
                        agent.store_round_memory(
                            round_id=round_num,
                            observation=obs,
                            prices=record.prices,
                            profits=record.profits,
                            shares=record.shares,
                            collusion_index=record.collusion_index,
                        )
                    except Exception as e:
                        print(f"  [RAG] Memory store failed for Firm {agent.firm_id}: {e}")

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

        # Determine effective price ceiling and history visibility under policy
        effective_ceiling = self.price_ceiling
        is_policy_active = False
        if self.policy is not None:
            is_policy_active = self.policy.is_active(round_number)
            effective_ceiling = self.policy.compute_effective_ceiling(
                self.benchmarks, self.price_ceiling, round_number
            )
            visible_price_history, visible_profit_history = self.policy.get_visible_history(
                self.price_history, self.profit_history, round_number
            )
        else:
            visible_price_history = self.price_history
            visible_profit_history = self.profit_history

        # Step 1: Collect prices from all agents
        raw_prices = []
        prices = []
        for agent in self.agents:
            obs = Observation(
                round_number=round_number,
                firm_id=agent.firm_id,
                marginal_cost=float(self.demand_model.costs[agent.firm_id]),
                price_floor=self.price_floor,
                price_ceiling=effective_ceiling,
                price_history=visible_price_history,
                profit_history=visible_profit_history,
            )
            raw_p = agent.choose_price(obs)
            raw_prices.append(round(raw_p, 4))
            clamped = self._clamp(raw_p, effective_ceiling)
            prices.append(clamped)

        # Compute consumer savings from regulatory price cap
        raw_avg = float(np.mean(raw_prices))
        clamped_avg = float(np.mean(prices))
        consumer_savings = max(
            0.0, (raw_avg - clamped_avg) * float(self.demand_model.market_size)
        )

        # Step 2: Feed prices into demand model
        price_array = np.array(prices, dtype=float)
        result: DemandResult = self.demand_model.compute(price_array)

        # Step 3: Compute collusion index
        avg_price = clamped_avg
        collusion_idx = self.demand_model.collusion_index(avg_price)

        # Step 4: Antitrust Leniency Program (rewarding defectors)
        leniency_recipients = []
        if self.policy is not None and self.policy.leniency_bonus > 0.0:
            leniency_recipients = self.policy.check_leniency(
                round_number=round_number,
                raw_prices=raw_prices,
                current_lambda=collusion_idx,
                benchmarks=self.benchmarks,
            )
            for recipient in leniency_recipients:
                result.profits[recipient] += self.policy.leniency_bonus

        total_profit = float(result.profits.sum())

        return RoundRecord(
            round_number=round_number,
            prices=result.prices.tolist(),
            shares=result.shares.tolist(),
            profits=result.profits.tolist(),
            avg_price=avg_price,
            total_profit=total_profit,
            collusion_index=collusion_idx,
            outside_share=result.outside_share,
            raw_prices=raw_prices,
            consumer_savings=round(consumer_savings, 4),
            leniency_recipients=leniency_recipients,
            is_policy_active=is_policy_active,
        )

    def _clamp(self, price: float, ceiling: float | None = None) -> float:
        """Keep price within legal bounds."""
        eff_ceiling = ceiling if ceiling is not None else self.price_ceiling
        return max(self.price_floor, min(eff_ceiling, round(price, 4)))

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

        summary_dict = {
            "rounds_completed": len(self.records),
            "nash_price": self.benchmarks.nash_price,
            "monopoly_price": self.benchmarks.monopoly_price,
            "final_avg_price": self.records[-1].avg_price,
            "final_collusion_index": self.records[-1].collusion_index,
            "converged_collusion_index": converged_lambda,
            "peak_collusion_index": max(lambdas),
            "convergence_round": convergence_round,
        }

        # Policy impact evaluation if policy was configured
        if self.policy is not None:
            pre_records = [r for r in self.records if not r.is_policy_active]
            post_records = [r for r in self.records if r.is_policy_active]

            pre_lambda = (
                sum(r.collusion_index for r in pre_records) / len(pre_records)
                if pre_records else None
            )
            post_lambda = (
                sum(r.collusion_index for r in post_records) / len(post_records)
                if post_records else None
            )

            total_savings = sum(r.consumer_savings for r in self.records)
            capped_rounds = sum(1 for r in self.records if r.consumer_savings > 0)
            total_leniency = sum(len(r.leniency_recipients) for r in self.records)

            lambda_reduction = None
            if pre_lambda is not None and post_lambda is not None:
                lambda_reduction = round(pre_lambda - post_lambda, 4)

            summary_dict["policy"] = {
                "name": self.policy.name,
                "config": self.policy.to_dict(),
                "active_rounds_count": len(post_records),
                "pre_policy_avg_lambda": round(pre_lambda, 4) if pre_lambda is not None else None,
                "post_policy_avg_lambda": round(post_lambda, 4) if post_lambda is not None else None,
                "lambda_reduction": lambda_reduction,
                "total_consumer_savings": round(total_savings, 2),
                "capped_rounds_count": capped_rounds,
                "total_leniency_awarded_count": total_leniency,
            }

        return summary_dict
