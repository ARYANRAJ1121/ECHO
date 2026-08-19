import os
import pandas as pd
from .base import MarketDataLoader, MarketContext

class AmazonDataLoader(MarketDataLoader):
    """
    Loads Amazon Marketplace data from a local Kaggle CSV.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Loading Amazon product pricing data from dataset...")
        
        firm_names = ["Amazon Retail", "ElectroGiant", "TechNova", "GadgetBox", "QuickShip Electronics"]
        
        try:
            csv_path = os.path.join("analysis", "data", "amazon_products.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                # Filter for a single highly competitive ASIN/Category
                cat_df = df[df["category"] == "Wireless_Earbuds"]
                
                # Assume actual_price is cost + overhead
                # We extract realistic parameters for 5 sellers
                avg_cost = cat_df["actual_price"].mean() * 0.7
                marginal_costs = [
                    round(avg_cost, 2),        # Amazon Retail
                    round(avg_cost * 1.05, 2), # ElectroGiant
                    round(avg_cost * 1.02, 2), # TechNova
                    round(avg_cost * 1.08, 2), # GadgetBox
                    round(avg_cost * 1.01, 2)  # QuickShip
                ]
                
                price_ceiling = float(cat_df["actual_price"].max())
            else:
                raise FileNotFoundError("amazon_products.csv not found")

            return MarketContext(
                dataset_name="Amazon Marketplace (Wireless Earbuds)",
                firm_names=firm_names,
                marginal_costs=marginal_costs,
                price_floor=round(min(marginal_costs), 2),
                price_ceiling=price_ceiling,
                base_quality=62.1,
                description="third-party seller on Amazon. You are running an algorithmic repricer bot competing for the Buy Box on a highly popular Wireless Earbuds ASIN. The product is identical across all sellers.",
                mu=2.07,
                currency="$"
            )
        except Exception as e:
            print(f"  [Data Loader] Falling back for Amazon: {e}")
            return MarketContext(
                dataset_name="Amazon Marketplace (Fallback)",
                firm_names=firm_names,
                marginal_costs=[40.0, 42.0, 41.0, 43.5, 40.5],
                price_floor=40.0,
                price_ceiling=80.0,
                base_quality=62.1,
                description="third-party seller on Amazon. You are running an algorithmic repricer bot competing for the Buy Box on a highly popular Wireless Earbuds ASIN. The product is identical across all sellers.",
                mu=2.07,
                currency="$"
            )
