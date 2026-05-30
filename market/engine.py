from __future__ import annotations

from dataclasses import dataclass

from agents.base_agent import Observation, PricingAgent
from market.demand import BenchmarkPrices, DemandOutcome, LogitDemandModel


@dataclass
class MarketConfig:
    n_firms: int
    rounds: int
    price_floor: float
    price_ceiling: float
    marginal_cost: float


@dataclass
class RoundRecord:
    round_number: int
    prices: list[float]
    shares: list[float]
    units_sold: list[float]
    profits: list[float]
    avg_price: float
    total_profit: float
    collusion_index: float


class MarketEngine:
    """Runs the repeated pricing game."""

    def __init__(
        self,
        config: MarketConfig,
        demand_model: LogitDemandModel,
        agents: list[PricingAgent],
    ) -> None:
        if len(agents) != config.n_firms:
            raise ValueError("Number of agents must match number of firms.")

        self.config = config
        self.demand_model = demand_model
        self.agents = agents
        self.benchmarks: BenchmarkPrices = demand_model.compute_benchmarks(
            price_floor=config.price_floor,
            price_ceiling=config.price_ceiling,
        )

        self.price_history: list[list[float]] = []
        self.profit_history: list[list[float]] = []
        self.records: list[RoundRecord] = []

    def run(self) -> list[RoundRecord]:
        for round_number in range(1, self.config.rounds + 1):
            prices = self._collect_prices(round_number)
            outcome = self.demand_model.compute(prices)
            collusion_index = self.demand_model.collusion_index(outcome.avg_price, self.benchmarks)

            record = RoundRecord(
                round_number=round_number,
                prices=outcome.prices,
                shares=outcome.shares,
                units_sold=outcome.units_sold,
                profits=outcome.profits,
                avg_price=outcome.avg_price,
                total_profit=outcome.total_profit,
                collusion_index=collusion_index,
            )

            self.records.append(record)
            self.price_history.append(record.prices)
            self.profit_history.append(record.profits)

        return self.records

    def summary(self) -> dict[str, float | int | None]:
        if not self.records:
            return {}

        collusion_values = [record.collusion_index for record in self.records]
        convergence_round = None
        for record in self.records:
            if record.collusion_index >= 0.7:
                convergence_round = record.round_number
                break

        return {
            "rounds_completed": len(self.records),
            "nash_price": self.benchmarks.nash_price,
            "monopoly_price": self.benchmarks.monopoly_price,
            "final_avg_price": self.records[-1].avg_price,
            "final_total_profit": self.records[-1].total_profit,
            "final_collusion_index": self.records[-1].collusion_index,
            "average_collusion_index": sum(collusion_values) / len(collusion_values),
            "convergence_round": convergence_round,
        }

    def _collect_prices(self, round_number: int) -> list[float]:
        prices: list[float] = []

        for agent in self.agents:
            observation = Observation(
                round_number=round_number,
                firm_id=agent.firm_id,
                marginal_cost=self.config.marginal_cost,
                price_floor=self.config.price_floor,
                price_ceiling=self.config.price_ceiling,
                price_history=self.price_history,
                profit_history=self.profit_history,
            )
            proposed_price = agent.choose_price(observation)
            prices.append(self._clamp_price(proposed_price))

        return prices

    def _clamp_price(self, price: float) -> float:
        if price < self.config.price_floor:
            return self.config.price_floor
        if price > self.config.price_ceiling:
            return self.config.price_ceiling
        return round(price, 2)
