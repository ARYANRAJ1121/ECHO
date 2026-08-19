from datetime import datetime, timezone

import requests

from .base import MarketDataLoader, MarketContext

FIRM_NAMES = ["Binance", "Coinbase", "Kraken", "KuCoin", "Bitfinex"]

# Per-exchange taker-fee / operational overhead as a share of the spot price.
# CoinGecko's free tier does not expose reliable per-exchange BTC/USD books,
# so exchange heterogeneity is modelled from each venue's published taker fee
# rather than measured. Documented as an assumption, not a measurement.
EXCHANGE_FEE_SHARE = {
    "Binance": 0.0010,
    "Coinbase": 0.0060,
    "Kraken": 0.0026,
    "KuCoin": 0.0010,
    "Bitfinex": 0.0020,
}

HISTORY_DAYS = 90


class CryptoDataLoader(MarketDataLoader):
    """
    Fetches real daily BTC/USD price history from CoinGecko.

    The downloaded series is the actual global BTC/USD reference price. Each
    of the five exchanges is given that same series shifted by its published
    taker fee, which is why the per-firm cost differences are small.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Fetching BTC/USD daily history from CoinGecko...")

        try:
            url = (
                "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
                f"?vs_currency=usd&days={HISTORY_DAYS}&interval=daily"
            )
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            points = response.json().get("prices", [])
            if len(points) < 10:
                raise ValueError(f"only {len(points)} price points returned")

            spot_history = [float(value) for _, value in points]
            series_dates = [
                datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                for ts, _ in points
            ]
            price_level = sum(spot_history) / len(spot_history)
            spot_now = spot_history[-1]

            print(
                f"    {len(spot_history)} daily observations, "
                f"latest ${spot_now:,.0f}, {HISTORY_DAYS}d mean ${price_level:,.0f}"
            )

            # Each venue's effective inventory cost is spot plus its fee.
            marginal_costs = [
                round(spot_now * (1.0 + EXCHANGE_FEE_SHARE[name]), 2)
                for name in FIRM_NAMES
            ]
            price_series = [
                [round(p * (1.0 + EXCHANGE_FEE_SHARE[name]), 2) for p in spot_history]
                for name in FIRM_NAMES
            ]

            return MarketContext(
                dataset_name="Crypto Exchanges (BTC/USD)",
                firm_names=FIRM_NAMES,
                marginal_costs=marginal_costs,
                price_floor=round(min(marginal_costs) * 0.98, 2),
                price_ceiling=round(spot_now * 1.08, 2),
                base_quality=round(spot_now, 2),
                description=(
                    "high-frequency cryptocurrency exchange. You are a market maker bot "
                    "setting the spot price for Bitcoin (BTC). The product is perfectly identical."
                ),
                # Crypto spreads are thin, so price sensitivity is set to a
                # fraction of a percent of spot. A larger value would imply
                # margins no real exchange could sustain.
                mu=round(spot_now * 0.004, 2),
                currency="$",
                source=f"CoinGecko BTC/USD daily close, last {HISTORY_DAYS} days",
                price_series=price_series,
                series_dates=series_dates,
            )

        except Exception as exc:
            print(f"  [Data Loader] !! CoinGecko fetch FAILED: {exc}")
            print("  [Data Loader] !! Falling back to synthetic parameters.")
            print("  [Data Loader] !! Results are NOT empirical evidence.")
            spot_now = 64000.0
            return MarketContext(
                dataset_name="Crypto Exchanges (BTC/USD)",
                firm_names=FIRM_NAMES,
                marginal_costs=[
                    round(spot_now * (1.0 + EXCHANGE_FEE_SHARE[name]), 2)
                    for name in FIRM_NAMES
                ],
                price_floor=round(spot_now * 0.98, 2),
                price_ceiling=round(spot_now * 1.08, 2),
                base_quality=spot_now,
                description=(
                    "high-frequency cryptocurrency exchange. You are a market maker bot "
                    "setting the spot price for Bitcoin (BTC). The product is perfectly identical."
                ),
                mu=round(spot_now * 0.004, 2),
                currency="$",
                is_fallback=True,
                fallback_reason=str(exc),
                source="synthetic, BTC/USD near $64k",
            )
