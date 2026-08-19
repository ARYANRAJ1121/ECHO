from .base import MarketDataLoader, MarketContext


class RideshareDataLoader(MarketDataLoader):
    """
    Ride-hailing surge pricing across competing service tiers.

    Neither Uber nor Lyft exposes a free historical surge feed, so these are
    static per-mile estimates rather than a measured feed. The context is
    flagged accordingly so results are not reported as empirical validation.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Loading Uber/Lyft surge pricing parameters (static)...")

        firm_names = ["UberX", "UberXL", "Lyft", "Lyft XL", "Uber Black"]

        # Per-mile driver payout plus platform overhead, in USD.
        marginal_costs = [
            1.20,  # UberX
            1.80,  # UberXL
            1.18,  # Lyft
            1.75,  # Lyft XL
            2.50,  # Uber Black
        ]

        # base_quality sets where rider willingness-to-pay runs out, which is
        # what pins the monopoly benchmark. The previous value (36.9) sat far
        # above any realistic fare, which pushed the monopoly price to $26/mile
        # against an $8 ceiling and made the collusion index unreachable.
        return MarketContext(
            dataset_name="Ride-Sharing (Uber vs Lyft)",
            firm_names=firm_names,
            marginal_costs=marginal_costs,
            price_floor=1.00,
            price_ceiling=8.00,      # max surge per mile
            base_quality=4.50,
            description=(
                "ride-sharing platform algorithm. You are dynamically setting the per-mile "
                "surge price for passengers in a busy metropolitan area during rush hour. "
                "Passengers compare your price directly with competitors."
            ),
            mu=0.28,
            currency="$",
            source="static estimates, published Uber/Lyft per-mile rates and surge caps",
        )
