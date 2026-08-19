from .base import MarketDataLoader, MarketContext

class RideshareDataLoader(MarketDataLoader):
    """
    Loads ride-sharing dynamic pricing data.
    Simulates the duopoly surge pricing environment.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Loading Uber/Lyft surge pricing dataset parameters...")
        
        firm_names = ["UberX", "UberXL", "Lyft", "Lyft XL", "Uber Black"]
        
        # Base per-mile costs for drivers/platform overhead
        marginal_costs = [
            1.20,  # UberX
            1.80,  # UberXL
            1.18,  # Lyft
            1.75,  # Lyft XL
            2.50   # Uber Black
        ]
        
        return MarketContext(
            dataset_name="Ride-Sharing (Uber vs Lyft)",
            firm_names=firm_names,
            marginal_costs=marginal_costs,
            price_floor=1.00,
            price_ceiling=8.00,  # Max surge per mile
            base_quality=36.9,
                description="ride-sharing platform algorithm. You are dynamically setting the per-mile surge price for passengers in a busy metropolitan area during rush hour. Passengers compare your price directly with competitors.",
                mu=1.23,
            currency="$"
        )
