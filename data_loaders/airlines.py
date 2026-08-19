from .base import MarketDataLoader, MarketContext

class AirlinesDataLoader(MarketDataLoader):
    """
    Loads Indian Airlines dynamic ticket pricing data.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Loading Indian Airlines dynamic ticket pricing parameters...")
        
        firm_names = ["IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air"]
        
        # Base cost of flying a passenger on a standard DEL-BOM route (in INR)
        marginal_costs = [
            2500.0,  # IndiGo (Low cost carrier)
            3000.0,  # Air India (Legacy, higher overhead)
            2600.0,  # SpiceJet
            3200.0,  # Vistara (Premium)
            2550.0   # Akasa Air (New LCC)
        ]
        
        return MarketContext(
            dataset_name="Indian Airlines (DEL-BOM Route)",
            firm_names=firm_names,
            marginal_costs=marginal_costs,
            price_floor=2000.0,
            price_ceiling=15000.0,  # High demand / last minute fare
            base_quality=4155.0,
                description="dynamic pricing algorithm for an Indian airline. You are setting the ticket price for a flight from Delhi to Mumbai. Passengers use aggregators (like MakeMyTrip) to directly compare your price with other airlines.",
                mu=138.5,
            currency="₹"
        )
