import requests
import pandas as pd
import io
from .base import MarketDataLoader, MarketContext

class GasolineDataLoader(MarketDataLoader):
    """
    Fetches LIVE retail gasoline prices from the US Energy Information Administration
    via the FRED (Federal Reserve Economic Data) API.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Fetching live US Gasoline data from FRED API...")
        # FRED series IDs for the 5 PADD districts (Regular All Formulations Retail Gasoline)
        series_ids = {
            "East_Coast": "GASREGCOVW",
            "Midwest": "GASREGMWVW",
            "Gulf_Coast": "GASREGGCVW",
            "Rocky_Mtn": "GASREGRMVW",
            "West_Coast": "GASREGWCVW",
        }
        
        firm_names = list(series_ids.keys())
        mean_prices = []

        try:
            for region, sid in series_ids.items():
                url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.strip().split('\n')
                    region_data = []
                    for line in lines:
                        parts = line.split(',')
                        if len(parts) == 2 and parts[1] != '.' and parts[0] != 'DATE':
                            try:
                                region_data.append(float(parts[1].strip()))
                            except ValueError:
                                pass
                    if region_data:
                        # Average of last 52 weeks
                        recent_avg = sum(region_data[-52:]) / min(len(region_data), 52)
                        mean_prices.append(recent_avg)
                    else:
                        raise ValueError(f"No valid data for {region}")
                else:
                    raise ValueError(f"Failed to fetch {region}")
            
            # Assume marginal cost is a fixed margin below the historical mean
            # E.g., retail margin is typically around $0.30 - $0.50
            marginal_costs = [round(p - 0.40, 2) for p in mean_prices]
            
            # Global min/max bounds based on typical gas prices
            min_cost = min(marginal_costs)
            max_price = max(mean_prices) + 2.00
            
            return MarketContext(
                dataset_name="US Regional Gasoline",
                firm_names=[f"{name} Gas Supplier" for name in firm_names],
                marginal_costs=marginal_costs,
                price_floor=round(min_cost * 0.9, 2),
                price_ceiling=round(max_price, 2),
                base_quality=3.93,
                description="retail gasoline market. Prices are heavily visible and products are completely identical (homogeneous).",
                mu=0.131,
                currency="$"
            )
        except Exception as e:
            print(f"  [Data Loader] Failed to fetch FRED data: {e}")
            # Fallback to realistic standard params
            return MarketContext(
                dataset_name="US Regional Gasoline (Fallback)",
                firm_names=["East Coast Gas", "Midwest Gas", "Gulf Coast Gas", "Rocky Mtn Gas", "West Coast Gas"],
                marginal_costs=[2.50, 2.45, 2.40, 2.65, 3.10],
                price_floor=2.00,
                price_ceiling=6.00,
                base_quality=3.93,
                description="retail gasoline market. Prices are heavily visible and products are completely identical (homogeneous).",
                mu=0.131,
                currency="$"
            )
