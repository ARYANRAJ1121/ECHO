from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


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


class MarketDataLoader(ABC):
    """Base interface for all real-world data loaders."""

    @abstractmethod
    def load(self) -> MarketContext:
        """Fetch the data (API or CSV) and return the structured market context."""
        pass
