import requests

from .base import MarketDataLoader, MarketContext

# BLS Average Price Data -- "Gasoline, unleaded regular, per gallon" -- served
# through FRED as monthly series. These five US census divisions are spatially
# separated retail markets that do not overlap, which is the setup Eckert
# (2013) studies for spatially dispersed gasoline price coordination.
#
# The previous revision used EIA PADD series IDs (GASREGMWVW and friends).
# Four of those five now return HTTP 404 from FRED, so gasoline silently fell
# back to hardcoded numbers on every run. Verified live before use.
SERIES_IDS = {
    "New England": "APUS12B74714",
    "East North Central": "APUS23B74714",
    "South Atlantic": "APUS35B74714",
    "East South Central": "APUS35C74714",
    "Mountain": "APUS49B74714",
}

# Months of history to average when deriving cost and quality parameters.
LOOKBACK_MONTHS = 60

# Retail margin over wholesale/rack cost, as a share of the pump price.
# US retail gasoline margins run roughly 10-15% of the pump price once
# taxes and dealer margin are separated out.
RETAIL_MARGIN_SHARE = 0.12


class GasolineDataLoader(MarketDataLoader):
    """
    Fetches monthly retail gasoline prices for five US census divisions from
    the BLS average-price series hosted on FRED.

    Each division is treated as one competing firm. The full downloaded price
    history is kept on the MarketContext so it can be plotted against the
    simulated trajectory.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Fetching US regional gasoline prices (BLS via FRED)...")

        firm_names = list(SERIES_IDS.keys())
        price_series: list[list[float]] = []
        series_dates: list[str] | None = None

        try:
            for region, series_id in SERIES_IDS.items():
                dates, values = self._fetch_series(series_id)
                if not values:
                    raise ValueError(f"{region} ({series_id}) returned no usable observations")
                price_series.append(values)
                if series_dates is None or len(dates) < len(series_dates):
                    series_dates = dates
                print(f"    {region:20} {len(values):4} obs, latest ${values[-1]:.3f}")

            mean_prices = [
                sum(s[-LOOKBACK_MONTHS:]) / len(s[-LOOKBACK_MONTHS:])
                for s in price_series
            ]

            # Wholesale cost per region, backed out of the observed pump price.
            marginal_costs = [round(p * (1.0 - RETAIL_MARGIN_SHARE), 3) for p in mean_prices]
            price_level = sum(mean_prices) / len(mean_prices)

            return MarketContext(
                dataset_name="US Regional Gasoline",
                firm_names=[f"{name} Retail" for name in firm_names],
                marginal_costs=marginal_costs,
                price_floor=round(min(marginal_costs) * 0.95, 2),
                price_ceiling=round(price_level * 2.0, 2),
                # Quality is anchored to the observed price level so the logit
                # utility (quality - price) stays near zero at realistic
                # prices. Without this the monopoly benchmark drifts far
                # outside any plausible price band.
                base_quality=round(price_level, 3),
                description=(
                    "retail gasoline market. Prices are posted on roadside signs and "
                    "products are completely identical (homogeneous)."
                ),
                mu=round(price_level * 0.08, 4),
                currency="$",
                source="BLS Average Price Data via FRED, monthly, 5 US census divisions",
                price_series=price_series,
                series_dates=series_dates,
            )

        except Exception as exc:
            print(f"  [Data Loader] !! FRED fetch FAILED: {exc}")
            print("  [Data Loader] !! Falling back to synthetic parameters.")
            print("  [Data Loader] !! Results are NOT empirical evidence.")
            return MarketContext(
                dataset_name="US Regional Gasoline",
                firm_names=[
                    "New England Retail", "East North Central Retail",
                    "South Atlantic Retail", "East South Central Retail",
                    "Mountain Retail",
                ],
                marginal_costs=[3.56, 3.58, 3.44, 3.27, 4.88],
                price_floor=3.10,
                price_ceiling=8.30,
                base_quality=4.15,
                description=(
                    "retail gasoline market. Prices are posted on roadside signs and "
                    "products are completely identical (homogeneous)."
                ),
                mu=0.332,
                currency="$",
                is_fallback=True,
                fallback_reason=str(exc),
                source="synthetic, calibrated to 2021-2026 BLS regional averages",
            )

    @staticmethod
    def _fetch_series(series_id: str) -> tuple[list[str], list[float]]:
        """Download one FRED CSV series. Returns (dates, values), oldest first."""
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        # A bad series ID returns an HTML error page with HTTP 200 in some
        # cases, so check the payload actually looks like CSV.
        text = response.text.lstrip()
        if text.startswith("<"):
            raise ValueError(f"{series_id} returned HTML, not CSV (bad series ID)")

        dates: list[str] = []
        values: list[float] = []
        for line in text.strip().splitlines()[1:]:
            parts = line.split(",")
            if len(parts) != 2:
                continue
            raw = parts[1].strip()
            if raw in (".", ""):
                continue
            try:
                values.append(float(raw))
                dates.append(parts[0].strip())
            except ValueError:
                continue
        return dates, values
