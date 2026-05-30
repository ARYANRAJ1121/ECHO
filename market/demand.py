from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass
class DemandOutcome:
    prices: list[float]
    shares: list[float]
    units_sold: list[float]
    profits: list[float]
    outside_share: float
    total_profit: float
    avg_price: float


@dataclass
class BenchmarkPrices:
    nash_price: float
    monopoly_price: float


class LogitDemandModel:
    """
    Simple multinomial-logit demand model.

    Idea:
    - lower prices make a firm more attractive
    - buyers choose probabilistically across firms
    - some buyers pick the outside option and do not buy at all
    """

    def __init__(
        self,
        market_size: float,
        price_sensitivity: float,
        qualities: list[float],
        marginal_costs: list[float],
        outside_option_utility: float = 0.0,
    ) -> None:
        self.market_size = market_size
        self.price_sensitivity = price_sensitivity
        self.qualities = qualities
        self.marginal_costs = marginal_costs
        self.outside_option_utility = outside_option_utility
        self.n_firms = len(qualities)

    def compute(self, prices: list[float]) -> DemandOutcome:
        utilities = []
        for quality, price in zip(self.qualities, prices):
            utilities.append(quality - self.price_sensitivity * price)

        exp_values = [exp(value) for value in utilities]
        exp_outside = exp(self.outside_option_utility)
        denominator = sum(exp_values) + exp_outside

        shares = [value / denominator for value in exp_values]
        outside_share = exp_outside / denominator
        units_sold = [self.market_size * share for share in shares]

        profits = []
        for price, cost, units in zip(prices, self.marginal_costs, units_sold):
            profits.append((price - cost) * units)

        avg_price = sum(prices) / len(prices)

        return DemandOutcome(
            prices=prices,
            shares=shares,
            units_sold=units_sold,
            profits=profits,
            outside_share=outside_share,
            total_profit=sum(profits),
            avg_price=avg_price,
        )

    def estimate_profit(self, firm_id: int, candidate_price: float, rival_prices: list[float]) -> float:
        prices = rival_prices[:]
        prices[firm_id] = candidate_price
        outcome = self.compute(prices)
        return outcome.profits[firm_id]

    def compute_benchmarks(self, price_floor: float, price_ceiling: float, step: float = 0.25) -> BenchmarkPrices:
        nash_price = self._find_symmetric_nash_price(price_floor, price_ceiling, step)
        monopoly_price = self._find_symmetric_monopoly_price(price_floor, price_ceiling, step)
        return BenchmarkPrices(nash_price=nash_price, monopoly_price=monopoly_price)

    def collusion_index(self, avg_price: float, benchmarks: BenchmarkPrices) -> float:
        gap = benchmarks.monopoly_price - benchmarks.nash_price
        if gap <= 0:
            return 0.0

        raw_value = (avg_price - benchmarks.nash_price) / gap
        return max(0.0, min(1.0, raw_value))

    def _find_symmetric_nash_price(self, price_floor: float, price_ceiling: float, step: float) -> float:
        current_price = price_floor + 1.0

        for _ in range(40):
            candidate_prices = self._price_grid(price_floor, price_ceiling, step)
            best_price = current_price
            best_profit = float("-inf")

            rival_prices = [current_price] * self.n_firms
            for candidate_price in candidate_prices:
                profit = self.estimate_profit(
                    firm_id=0,
                    candidate_price=candidate_price,
                    rival_prices=rival_prices,
                )
                if profit > best_profit:
                    best_profit = profit
                    best_price = candidate_price

            if abs(best_price - current_price) < step / 2:
                return best_price

            current_price = best_price

        return current_price

    def _find_symmetric_monopoly_price(self, price_floor: float, price_ceiling: float, step: float) -> float:
        best_price = price_floor
        best_total_profit = float("-inf")

        for candidate_price in self._price_grid(price_floor, price_ceiling, step):
            prices = [candidate_price] * self.n_firms
            total_profit = self.compute(prices).total_profit
            if total_profit > best_total_profit:
                best_total_profit = total_profit
                best_price = candidate_price

        return best_price

    @staticmethod
    def _price_grid(price_floor: float, price_ceiling: float, step: float) -> list[float]:
        prices = []
        current = price_floor
        while current <= price_ceiling + 1e-9:
            prices.append(round(current, 2))
            current += step
        return prices
