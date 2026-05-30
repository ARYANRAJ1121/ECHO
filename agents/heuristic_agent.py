from __future__ import annotations

from agents.base_agent import Observation, PricingAgent


class SteadyAgent(PricingAgent):
    """Always charges cost plus a fixed markup."""

    def __init__(self, firm_id: int, markup: float) -> None:
        super().__init__(firm_id=firm_id, name=f"SteadyAgent_{firm_id}")
        self.markup = markup

    def choose_price(self, observation: Observation) -> float:
        return observation.marginal_cost + self.markup


class FollowerAgent(PricingAgent):
    """
    Moves gradually toward last round's average market price.

    This is useful because it models a simple "watch rivals and adapt" behavior.
    """

    def __init__(self, firm_id: int, target_markup: float, adjustment_speed: float = 0.5) -> None:
        super().__init__(firm_id=firm_id, name=f"FollowerAgent_{firm_id}")
        self.target_markup = target_markup
        self.adjustment_speed = adjustment_speed

    def choose_price(self, observation: Observation) -> float:
        base_price = observation.marginal_cost + self.target_markup

        if observation.last_average_price is None or observation.last_own_price is None:
            return base_price

        target_price = max(base_price, observation.last_average_price)
        current_price = observation.last_own_price
        return current_price + self.adjustment_speed * (target_price - current_price)


class UndercutAgent(PricingAgent):
    """
    Tries to beat the cheapest rival while staying safely above cost.

    This is a simple model of aggressive competition.
    """

    def __init__(self, firm_id: int, undercut_amount: float, safe_markup: float) -> None:
        super().__init__(firm_id=firm_id, name=f"UndercutAgent_{firm_id}")
        self.undercut_amount = undercut_amount
        self.safe_markup = safe_markup

    def choose_price(self, observation: Observation) -> float:
        fallback_price = observation.marginal_cost + self.safe_markup + 1.0

        if observation.last_cheapest_price is None:
            return fallback_price

        target_price = observation.last_cheapest_price - self.undercut_amount
        minimum_safe_price = observation.marginal_cost + self.safe_markup
        return max(target_price, minimum_safe_price)
