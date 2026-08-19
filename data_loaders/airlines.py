from .base import MarketDataLoader, MarketContext


class AirlinesDataLoader(MarketDataLoader):
    """
    Indian domestic airline pricing on the Delhi-Mumbai trunk route.

    There is no free live fare API, so these are static published-parameter
    estimates rather than a measured feed. The context is flagged accordingly
    so results are not reported as empirical validation.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Loading Indian Airlines DEL-BOM parameters (static)...")

        firm_names = ["IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air"]

        # Cost per seat on a DEL-BOM narrowbody rotation, in INR. Legacy and
        # premium carriers carry higher overhead than the low-cost carriers.
        marginal_costs = [
            2500.0,  # IndiGo (low-cost carrier)
            3000.0,  # Air India (legacy, higher overhead)
            2600.0,  # SpiceJet
            3200.0,  # Vistara (premium)
            2550.0,  # Akasa Air (new LCC)
        ]

        # base_quality sets where willingness-to-pay runs out, which is what
        # pins the monopoly benchmark in a logit market. Anchoring it near a
        # realistic peak fare keeps the monopoly price inside the fare band
        # instead of far above the ceiling.
        return MarketContext(
            dataset_name="Indian Airlines (DEL-BOM Route)",
            firm_names=firm_names,
            marginal_costs=marginal_costs,
            price_floor=2000.0,
            price_ceiling=15000.0,   # last-minute peak fare
            base_quality=5800.0,
            description=(
                "dynamic pricing algorithm for an Indian airline. You are setting the ticket "
                "price for a flight from Delhi to Mumbai. Passengers use aggregators "
                "(like MakeMyTrip) to directly compare your price with other airlines."
            ),
            mu=230.0,
            currency="\u20b9",
            source="static estimates, DGCA route economics and published DEL-BOM fare ranges",
        )
