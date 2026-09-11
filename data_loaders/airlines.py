from .base import MarketDataLoader, MarketContext


class AirlinesDataLoader(MarketDataLoader):
    """
    Indian domestic airline pricing on the Delhi-Mumbai trunk route.

    There is no free live fare API, so these are static published-parameter
    estimates rather than a measured feed.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Loading Indian Airlines DEL-BOM parameters (static)...")

        firm_names = ["IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air"]

        # Cost per seat on a DEL-BOM narrowbody rotation, in INR. Legacy and
        # premium carriers carry higher overhead than the low-cost carriers.
        marginal_costs = [
            2700.0,  # IndiGo
            2850.0,  # Air India
            2720.0,  # SpiceJet
            2900.0,  # Vistara
            2710.0,  # Akasa Air
        ]

        return MarketContext(
            dataset_name="Indian Airlines (DEL-BOM Route)",
            firm_names=firm_names,
            marginal_costs=marginal_costs,
            price_floor=2000.0,
            price_ceiling=15000.0,
            base_quality=8500.0,
            description=(
                "dynamic pricing algorithm for an Indian airline. You are setting the ticket "
                "price for a flight from Delhi to Mumbai."
            ),
            mu=720.0,
            currency="\u20b9",
            source="DGCA route economics and published DEL-BOM fare ranges",
        )
