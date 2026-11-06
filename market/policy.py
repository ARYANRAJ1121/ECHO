"""
market/policy.py -- Regulatory Policy Counterfactuals & Market Interventions

Provides regulatory mechanisms to test how antitrust interventions
affect algorithmic collusion (F6 in ECHO research backlog):
1. Price Caps (relative to Nash-Monopoly span or absolute)
2. Transparency Delays (lagging rival price visibility to break punishment loops)
3. Corporate Leniency / Whistleblower Bonuses (subsidizing defection from cartels)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class PolicyConfig:
    """
    Antitrust Regulatory Policy Configuration.

    Parameters
    ----------
    name : str
        Human-readable name of the policy regime.
    price_cap_fraction : Optional[float]
        If set (e.g., 0.50), sets price ceiling at:
        p_cap = p_nash + fraction * (p_monopoly - p_nash).
        Any price chosen above p_cap is clamped by the regulator.
    fixed_price_cap : Optional[float]
        If set, sets an absolute hard ceiling.
    transparency_delay : int
        Number of rounds rival prices are lagged before agents can observe them.
        0 = immediate transparency (default).
        k > 0 = agents only observe market state up to round (t - k).
    leniency_bonus : float
        Financial subsidy/bonus given to a firm that deviates downwards from
        a supra-competitive market by undercutting rivals.
    leniency_threshold_lambda : float
        The minimum market Lambda required for leniency bonuses to become active.
        Default is 0.40.
    leniency_undercut_pct : float
        How much below the rivals' average price a defector must price to earn
        leniency (e.g., 0.03 = 3% undercutting).
    active_from_round : int
        Round at which the policy intervention begins.
        Enables A/B split-run experiments: rounds 1..(active_from_round-1) run unconstrained,
        and round active_from_round onwards runs under the policy.
    """
    name: str = "Unregulated Baseline"
    price_cap_fraction: Optional[float] = None
    fixed_price_cap: Optional[float] = None
    transparency_delay: int = 0
    leniency_bonus: float = 0.0
    leniency_threshold_lambda: float = 0.40
    leniency_undercut_pct: float = 0.03
    active_from_round: int = 1

    def is_active(self, round_number: int) -> bool:
        """Whether the policy is currently active in round_number."""
        return round_number >= self.active_from_round

    def compute_effective_ceiling(
        self,
        benchmarks: Any,
        default_ceiling: float,
        round_number: int,
    ) -> float:
        """Calculate the legal price ceiling for this round."""
        if not self.is_active(round_number):
            return default_ceiling

        cap = default_ceiling
        if self.price_cap_fraction is not None:
            span = benchmarks.monopoly_price - benchmarks.nash_price
            relative_cap = benchmarks.nash_price + self.price_cap_fraction * span
            cap = min(cap, relative_cap)

        if self.fixed_price_cap is not None:
            cap = min(cap, self.fixed_price_cap)

        return float(cap)

    def get_visible_history(
        self,
        price_history: list[list[float]],
        profit_history: list[list[float]],
        round_number: int,
    ) -> tuple[list[list[float]], list[list[float]]]:
        """
        Return the history that firms are permitted to observe under the transparency policy.

        If transparency_delay == 0 or policy inactive, firms observe the full history
        up to the previous round.
        If transparency_delay == k > 0, firms only observe history up to round (round_number - 1 - k).
        """
        if not self.is_active(round_number) or self.transparency_delay <= 0:
            return price_history, profit_history

        # If delay is k, in round t we only show history through round (t - 1 - k).
        # Since price_history has length (t - 1), cutoff is len - k.
        cutoff = max(0, len(price_history) - self.transparency_delay)
        return price_history[:cutoff], profit_history[:cutoff]

    def check_leniency(
        self,
        round_number: int,
        raw_prices: list[float],
        current_lambda: float,
        benchmarks: Any,
    ) -> list[int]:
        """
        Identify firms that qualify for an antitrust leniency/whistleblower reward.

        Qualification criteria:
        1. Policy is active and leniency_bonus > 0.
        2. Market is supra-competitive (current_lambda >= leniency_threshold_lambda).
        3. Firm's price is at least leniency_undercut_pct below the average of its rivals,
           or prices near/below Nash equilibrium.
        """
        if not self.is_active(round_number) or self.leniency_bonus <= 0.0:
            return []

        if current_lambda < self.leniency_threshold_lambda:
            return []

        n = len(raw_prices)
        if n <= 1:
            return []

        recipients = []
        for i, price_i in enumerate(raw_prices):
            rival_prices = [p for j, p in enumerate(raw_prices) if j != i]
            rival_avg = sum(rival_prices) / len(rival_prices)
            
            # Condition A: meaningfully undercut rivals
            undercut = (rival_avg - price_i) / max(rival_avg, 1e-4)
            # Condition B: priced at or below Nash equilibrium
            near_nash = price_i <= benchmarks.nash_price * 1.05

            if undercut >= self.leniency_undercut_pct or near_nash:
                recipients.append(i)

        return recipients

    def to_dict(self) -> dict:
        """Serialize policy configuration for logging and API responses."""
        return {
            "name": self.name,
            "price_cap_fraction": self.price_cap_fraction,
            "fixed_price_cap": self.fixed_price_cap,
            "transparency_delay": self.transparency_delay,
            "leniency_bonus": self.leniency_bonus,
            "leniency_threshold_lambda": self.leniency_threshold_lambda,
            "leniency_undercut_pct": self.leniency_undercut_pct,
            "active_from_round": self.active_from_round,
        }

    @classmethod
    def price_cap(cls, fraction: float = 0.5, active_from_round: int = 1) -> PolicyConfig:
        """Preset: enforce a relative price ceiling at Nash + fraction*(Monopoly - Nash)."""
        return cls(
            name=f"Price Cap ({int(fraction*100)}% of Monopoly span)",
            price_cap_fraction=fraction,
            active_from_round=active_from_round,
        )

    @classmethod
    def delayed_transparency(cls, delay: int = 5, active_from_round: int = 1) -> PolicyConfig:
        """Preset: lag competitor price visibility by k rounds to disrupt punishment."""
        return cls(
            name=f"Delayed Transparency ({delay}-round lag)",
            transparency_delay=delay,
            active_from_round=active_from_round,
        )

    @classmethod
    def leniency_program(cls, bonus: float = 50.0, active_from_round: int = 1) -> PolicyConfig:
        """Preset: reward cartel defectors with a regulatory subsidy."""
        return cls(
            name=f"Antitrust Leniency (Bonus: {bonus:.1f})",
            leniency_bonus=bonus,
            active_from_round=active_from_round,
        )

    @classmethod
    def comprehensive_remedy(
        cls,
        fraction: float = 0.5,
        delay: int = 5,
        bonus: float = 50.0,
        active_from_round: int = 1,
    ) -> PolicyConfig:
        """Preset: combined structural intervention."""
        return cls(
            name="Comprehensive Antitrust Remedy",
            price_cap_fraction=fraction,
            transparency_delay=delay,
            leniency_bonus=bonus,
            active_from_round=active_from_round,
        )
