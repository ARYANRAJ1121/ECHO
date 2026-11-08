"""
market/macro.py -- Non-Stationary Demand & Macroeconomic Environments (F5)

=== WHAT IS THIS? ===

Extends the stationary Bertrand oligopoly to model real-world economic volatility:
1. Seasonal / Cyclical Demand: Periodic boom-and-bust demand oscillations (Rotemberg-Saloner cycles).
2. Acute Macroeconomic Shocks: Sudden demand collapses (e.g. 2008 or 2020 recessions).
3. Cost Inflation / Deflation Trends: Input cost drift over time.
4. Dynamic Price Sensitivity: Shifting customer price sensitivity (mu).

=== ECONOMIC THEORY (F5 Backlog) ===
- Rotemberg & Saloner (1986): "A Supergame-Theoretic Model of Price Wars during Booms"
  Predicts tacit collusion is harder to sustain during demand peaks due to defection incentives.
- Green & Porter (1984): Non-stationarity induces price wars when firms cannot distinguish
  between market downturns and rival defection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Any
import numpy as np


@dataclass
class MacroConfig:
    """
    Macroeconomic & Non-Stationary Market Configuration.

    Parameters
    ----------
    name : str
        Human-readable name of the macro regime.
    seasonality_amp : float
        Amplitude of seasonal demand oscillation (e.g. 0.30 for ±30% boom/bust).
    seasonality_period : int
        Rounds per seasonal cycle (default 20 rounds).
    cost_trend : float
        Per-round drift rate in marginal costs (e.g. +0.005 for 0.5% cost inflation per round).
    mu_trend : float
        Per-round drift in price sensitivity parameter mu.
    shock_round : Optional[int]
        Round at which an acute macroeconomic shock triggers (e.g., round 25).
    shock_intensity : float
        Fractional change in market size during shock (e.g. -0.40 = 40% demand collapse).
    shock_duration : int
        How many rounds the shock persists before economic recovery begins (default 6 rounds).
    """
    name: str = "Stationary (Baseline)"
    seasonality_amp: float = 0.0
    seasonality_period: int = 20
    cost_trend: float = 0.0
    mu_trend: float = 0.0
    shock_round: Optional[int] = None
    shock_intensity: float = -0.40
    shock_duration: int = 6

    # Base values cached upon first application
    _base_market_size: Optional[float] = None
    _base_mu: Optional[float] = None
    _base_costs: Optional[np.ndarray] = None

    @classmethod
    def none(cls) -> MacroConfig:
        """Standard stationary market."""
        return cls(name="Stationary Baseline")

    @classmethod
    def seasonal(cls, amp: float = 0.30, period: int = 20) -> MacroConfig:
        """Cyclical seasonal demand swings (±30% default)."""
        return cls(
            name=f"Seasonal Cycles (±{int(amp*100)}%)",
            seasonality_amp=amp,
            seasonality_period=period,
        )

    @classmethod
    def recession(cls, shock_round: int = 20, intensity: float = -0.40, duration: int = 6) -> MacroConfig:
        """Sudden macroeconomic recession / demand collapse."""
        return cls(
            name=f"Recession Shock (R{shock_round}: {int(intensity*100)}%)",
            shock_round=shock_round,
            shock_intensity=intensity,
            shock_duration=duration,
        )

    @classmethod
    def inflation(cls, cost_trend: float = 0.006) -> MacroConfig:
        """Persistent input cost inflation drift."""
        return cls(
            name=f"Cost Inflation (+{cost_trend*100:.1f}%/rd)",
            cost_trend=cost_trend,
        )

    def is_shock_active(self, round_number: int) -> bool:
        """Whether an acute shock is actively affecting the market in this round."""
        if self.shock_round is None:
            return False
        return self.shock_round <= round_number < (self.shock_round + self.shock_duration)

    def apply(self, demand_model: Any, round_number: int) -> dict[str, Any]:
        """
        Apply non-stationary shifts to the demand model for the given round.

        Returns telemetry dictionary of active macroeconomic conditions.
        """
        # Cache base parameters on first call
        if self._base_market_size is None:
            self._base_market_size = float(demand_model.market_size)
            self._base_mu = float(demand_model.mu)
            self._base_costs = demand_model.costs.copy()

        # 1. Seasonal Demand Oscillation
        seasonal_mult = 1.0
        if self.seasonality_amp > 0 and self.seasonality_period > 0:
            phase = 2.0 * math.pi * (round_number % self.seasonality_period) / self.seasonality_period
            seasonal_mult += self.seasonality_amp * math.sin(phase)

        # 2. Acute Shock (e.g. Recession)
        shock_mult = 1.0
        is_shock = self.is_shock_active(round_number)
        if is_shock:
            shock_mult += self.shock_intensity

        effective_market_size = max(0.01, self._base_market_size * seasonal_mult * shock_mult)
        demand_model.market_size = effective_market_size

        # 3. Price Sensitivity (mu) Drift
        if self.mu_trend != 0:
            effective_mu = max(0.05, self._base_mu * (1.0 + self.mu_trend * (round_number - 1)))
            demand_model.mu = effective_mu
        else:
            effective_mu = self._base_mu

        # 4. Cost Drift (Inflation / Deflation)
        if self.cost_trend != 0:
            cost_mult = max(0.1, 1.0 + self.cost_trend * (round_number - 1))
            demand_model.costs = self._base_costs * cost_mult
        else:
            cost_mult = 1.0

        return {
            "round": round_number,
            "market_size": round(effective_market_size, 4),
            "demand_multiplier": round(seasonal_mult * shock_mult, 4),
            "mu": round(effective_mu, 4),
            "cost_multiplier": round(cost_mult, 4),
            "is_shock": is_shock,
            "regime_name": self.name,
        }

