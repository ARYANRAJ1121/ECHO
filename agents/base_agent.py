from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Observation:
    """Information an agent can see before choosing its next price."""

    round_number: int
    firm_id: int
    marginal_cost: float
    price_floor: float
    price_ceiling: float
    price_history: list[list[float]]
    profit_history: list[list[float]]

    @property
    def last_round_prices(self) -> list[float] | None:
        return self.price_history[-1] if self.price_history else None

    @property
    def last_average_price(self) -> float | None:
        if not self.price_history:
            return None
        prices = self.price_history[-1]
        return sum(prices) / len(prices)

    @property
    def last_cheapest_price(self) -> float | None:
        if not self.price_history:
            return None
        return min(self.price_history[-1])

    @property
    def last_own_price(self) -> float | None:
        if not self.price_history:
            return None
        return self.price_history[-1][self.firm_id]

    @property
    def last_own_profit(self) -> float | None:
        if not self.profit_history:
            return None
        return self.profit_history[-1][self.firm_id]


class PricingAgent(ABC):
    """Base class for all pricing agents."""

    def __init__(self, firm_id: int, name: str) -> None:
        self.firm_id = firm_id
        self.name = name

    @abstractmethod
    def choose_price(self, observation: Observation) -> float:
        """Return the price the agent wants to post this round."""

