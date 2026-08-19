from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MarketContext:
    """The real-world parameters extracted for a specific simulation dataset."""
    dataset_name: str
    firm_names: list[str]          # Exact names of the 5 competitors
    marginal_costs: list[float]    # Base production/service cost per firm
    price_floor: float             # Legal/realistic minimum price
    price_ceiling: float           # Realistic maximum price
    base_quality: float            # Product quality (utility), needed for Logit demand to scale with price
    description: str               # Description for the LLM system prompt
    mu: float = 0.5                # Market sensitivity (scale of price variation)
    currency: str = "$"

    # --- Provenance ------------------------------------------------
    # is_fallback is True when the live fetch failed and hardcoded numbers
    # were substituted. Anything derived from a fallback context is NOT
    # real-world evidence and must not be reported as empirical validation.
    is_fallback: bool = False
    source: str = ""               # Human-readable citation for the numbers
    fallback_reason: str = ""      # Why the live fetch failed, if it did

    # --- Observed real-world price history -------------------------
    # price_series[i] is firm i's actual observed price history, oldest
    # first. Kept so the dashboard and figures can plot real prices
    # against simulated ones instead of discarding the download.
    price_series: list[list[float]] | None = None
    series_dates: list[str] | None = None

    @property
    def price_scale(self) -> float:
        """Typical price magnitude for this market.

        Agent markups and undercut steps are expressed as fractions of this
        so the same heuristic behaves the same way whether prices are in
        dollars per gallon or dollars per Bitcoin.
        """
        return sum(self.marginal_costs) / len(self.marginal_costs)

    @property
    def observed_mean_prices(self) -> list[float] | None:
        """Per-firm mean of the observed real price history."""
        if not self.price_series:
            return None
        return [sum(s) / len(s) for s in self.price_series if s]

    def observed_market_average(self, n: int | None = None) -> list[float] | None:
        """Cross-firm average real price per observation, oldest first.

        Only observations where every firm reported a price are included, so
        the returned series is directly comparable across firms. Pass n to
        keep just the most recent n observations.
        """
        if not self.price_series:
            return None
        series = [s for s in self.price_series if s]
        if not series:
            return None
        length = min(len(s) for s in series)
        if length == 0:
            return None
        averages = [
            sum(s[len(s) - length + t] for s in series) / len(series)
            for t in range(length)
        ]
        return averages[-n:] if n else averages

    def observed_dispersion_lambda(self) -> float | None:
        """Cross-sectional price-convergence proxy for the collusion index.

        Λ_proxy = 1 − coefficient of variation across firms, averaged over
        observations. Identical prices across competitors give 1.0; widely
        dispersed prices give ~0. This is the same proxy used in
        analysis/real_data.py, and it is a convergence measure — not the
        Nash/monopoly-anchored Λ the simulation reports. Compare trends, not
        absolute values.
        """
        if not self.price_series:
            return None
        series = [s for s in self.price_series if s]
        if len(series) < 2:
            return None
        length = min(len(s) for s in series)
        if length == 0:
            return None

        ratios = []
        for t in range(length):
            row = [s[len(s) - length + t] for s in series]
            mean = sum(row) / len(row)
            if mean <= 0:
                continue
            variance = sum((x - mean) ** 2 for x in row) / len(row)
            ratios.append(1.0 - (variance ** 0.5) / mean)
        if not ratios:
            return None
        return sum(ratios) / len(ratios)

    def describe(self) -> str:
        """One-line provenance summary printed at simulation start."""
        if self.is_fallback:
            reason = f" ({self.fallback_reason})" if self.fallback_reason else ""
            return f"{self.dataset_name} -- SYNTHETIC FALLBACK{reason}"
        if self.price_series:
            obs = min(len(s) for s in self.price_series)
            return f"{self.dataset_name} -- real data, {obs} obs/firm [{self.source}]"
        return f"{self.dataset_name} -- static parameters [{self.source}]"


class MarketDataLoader(ABC):
    """Base interface for all real-world data loaders."""

    @abstractmethod
    def load(self) -> MarketContext:
        """Fetch the data (API or CSV) and return the structured market context."""
        pass
