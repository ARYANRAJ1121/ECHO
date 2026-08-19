"""
agents/heuristic_agent.py -- Rule-based control agents.

These are the control group: fixed rules that cannot learn, so any collusion
the learning agents show cannot be blamed on the market model alone.

=== WHY MARKUPS ARE PRICES, NOT CONSTANTS ===

Each rule originally carried an absolute markup (cost + 0.50) tuned for the
$1-5 toy market. On a dataset where a unit costs $64,000 a fifty-cent markup
is indistinguishable from pricing at cost, so every firm posted below Nash,
profits went negative, and the collusion index came out negative on four of
the five datasets.

Callers should therefore pass `target_price` (and `floor_price` for the
undercutter), computed from the market's own Nash and monopoly benchmarks.
The absolute `markup` arguments still work for backwards compatibility.
"""

from __future__ import annotations

from agents.base_agent import Observation, PricingAgent


class SteadyAgent(PricingAgent):
    """Holds one price regardless of what rivals do."""

    def __init__(
        self,
        firm_id: int,
        markup: float | None = None,
        identity_name: str | None = None,
        target_price: float | None = None,
    ) -> None:
        name = identity_name if identity_name else f"SteadyAgent_{firm_id}"
        super().__init__(firm_id=firm_id, name=name)
        if markup is None and target_price is None:
            raise ValueError("SteadyAgent needs either markup or target_price")
        self.markup = markup
        self.target_price = target_price

    def choose_price(self, observation: Observation) -> float:
        if self.target_price is not None:
            return self.target_price
        return observation.marginal_cost + self.markup


class FollowerAgent(PricingAgent):
    """
    Moves gradually toward last round's average market price.

    Models a simple "watch rivals and adapt" behavior. It never drops below
    its own floor, so it drifts upward if rivals drift upward.
    """

    def __init__(
        self,
        firm_id: int,
        target_markup: float | None = None,
        adjustment_speed: float = 0.5,
        identity_name: str | None = None,
        target_price: float | None = None,
    ) -> None:
        name = identity_name if identity_name else f"FollowerAgent_{firm_id}"
        super().__init__(firm_id=firm_id, name=name)
        if target_markup is None and target_price is None:
            raise ValueError("FollowerAgent needs either target_markup or target_price")
        self.target_markup = target_markup
        self.target_price = target_price
        self.adjustment_speed = adjustment_speed

    def _base_price(self, observation: Observation) -> float:
        if self.target_price is not None:
            return self.target_price
        return observation.marginal_cost + self.target_markup

    def choose_price(self, observation: Observation) -> float:
        base_price = self._base_price(observation)

        if observation.last_average_price is None or observation.last_own_price is None:
            return base_price

        target_price = max(base_price, observation.last_average_price)
        current_price = observation.last_own_price
        return current_price + self.adjustment_speed * (target_price - current_price)


class UndercutAgent(PricingAgent):
    """
    Tries to beat the cheapest rival while staying safely above cost.

    A simple model of aggressive competition, and the main force keeping the
    heuristic control group near the competitive benchmark.
    """

    def __init__(
        self,
        firm_id: int,
        undercut_amount: float | None = None,
        safe_markup: float | None = None,
        identity_name: str | None = None,
        undercut_frac: float = 0.005,
        floor_price: float | None = None,
    ) -> None:
        name = identity_name if identity_name else f"UndercutAgent_{firm_id}"
        super().__init__(firm_id=firm_id, name=name)
        if safe_markup is None and floor_price is None:
            raise ValueError("UndercutAgent needs either safe_markup or floor_price")
        self.undercut_amount = undercut_amount
        self.undercut_frac = undercut_frac
        self.safe_markup = safe_markup
        self.floor_price = floor_price

    def _minimum_safe_price(self, observation: Observation) -> float:
        if self.floor_price is not None:
            return self.floor_price
        return observation.marginal_cost + self.safe_markup

    def _step(self, reference_price: float) -> float:
        """How far below the cheapest rival to price.

        Defaults to a fraction of the rival's price so the step stays
        meaningful whether prices are $3 or $64,000.
        """
        if self.undercut_amount is not None:
            return self.undercut_amount
        return abs(reference_price) * self.undercut_frac

    def choose_price(self, observation: Observation) -> float:
        minimum_safe_price = self._minimum_safe_price(observation)

        if observation.last_cheapest_price is None:
            return minimum_safe_price + self._step(minimum_safe_price)

        cheapest = observation.last_cheapest_price
        return max(cheapest - self._step(cheapest), minimum_safe_price)
