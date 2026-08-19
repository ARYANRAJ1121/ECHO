import os

import pandas as pd

from .base import MarketDataLoader, MarketContext

CSV_PATH = os.path.join("analysis", "data", "amazon_products.csv")
CATEGORY = "Wireless_Earbuds"
N_FIRMS = 5

# Share of the listed price that is seller cost of goods. Third-party
# electronics resellers on Amazon typically run 20-30% gross margin once
# referral fees and FBA fulfilment are deducted.
COST_SHARE = 0.75


class AmazonDataLoader(MarketDataLoader):
    """
    Loads Amazon Marketplace listings from the local CSV.

    Firms are the five sellers with the widest ASIN coverage in the chosen
    category, and each firm's observed price history is its actual listed
    price across the ASINs it competes on. Previously this loader read the
    CSV only to average one column and then discarded every row.
    """

    def load(self) -> MarketContext:
        print(f"  [Data Loader] Loading Amazon {CATEGORY} listings from CSV...")

        try:
            if not os.path.exists(CSV_PATH):
                raise FileNotFoundError(f"{CSV_PATH} not found")

            frame = pd.read_csv(CSV_PATH)
            category = frame[frame["category"] == CATEGORY]
            if category.empty:
                raise ValueError(f"no rows for category {CATEGORY}")

            # Five sellers with the most listings, so every firm has a
            # comparable price history.
            top_sellers = (
                category["seller"].value_counts().head(N_FIRMS).index.tolist()
            )
            if len(top_sellers) < N_FIRMS:
                raise ValueError(f"only {len(top_sellers)} sellers in {CATEGORY}")

            firm_names = sorted(top_sellers)
            price_series: list[list[float]] = []
            marginal_costs: list[float] = []

            for seller in firm_names:
                rows = category[category["seller"] == seller].sort_values("product_id")
                prices = [round(float(p), 2) for p in rows["discount_price"] if p > 0]
                if not prices:
                    raise ValueError(f"seller {seller} has no valid prices")
                price_series.append(prices)
                marginal_costs.append(round(sum(prices) / len(prices) * COST_SHARE, 2))
                print(f"    {seller:12} {len(prices):3} listings, mean ${sum(prices)/len(prices):.2f}")

            all_prices = [p for s in price_series for p in s]
            price_level = sum(all_prices) / len(all_prices)

            return MarketContext(
                dataset_name=f"Amazon Marketplace ({CATEGORY.replace('_', ' ')})",
                firm_names=firm_names,
                marginal_costs=marginal_costs,
                price_floor=round(min(marginal_costs) * 0.95, 2),
                price_ceiling=round(max(all_prices) * 1.6, 2),
                base_quality=round(price_level, 2),
                description=(
                    "third-party seller on Amazon. You are running an algorithmic repricer bot "
                    "competing for the Buy Box on a popular Wireless Earbuds ASIN. "
                    "The product is identical across all sellers."
                ),
                mu=round(price_level * 0.08, 3),
                currency="$",
                source=f"local Amazon listings CSV, {CATEGORY}, {len(all_prices)} observations",
                price_series=price_series,
            )

        except Exception as exc:
            print(f"  [Data Loader] !! Amazon CSV load FAILED: {exc}")
            print("  [Data Loader] !! Falling back to synthetic parameters.")
            print("  [Data Loader] !! Results are NOT empirical evidence.")
            return MarketContext(
                dataset_name="Amazon Marketplace (Wireless Earbuds)",
                firm_names=["AudioKing", "MegaDeals", "PrimeElec", "QuickShip", "SoundWave"],
                marginal_costs=[18.34, 17.55, 16.93, 18.73, 19.53],
                price_floor=16.08,
                price_ceiling=53.98,
                base_quality=24.20,
                description=(
                    "third-party seller on Amazon. You are running an algorithmic repricer bot "
                    "competing for the Buy Box on a popular Wireless Earbuds ASIN. "
                    "The product is identical across all sellers."
                ),
                mu=1.936,
                currency="$",
                is_fallback=True,
                fallback_reason=str(exc),
                source="synthetic, calibrated to the Wireless Earbuds CSV",
            )
