import requests
from .base import MarketDataLoader, MarketContext

class CryptoDataLoader(MarketDataLoader):
    """
    Fetches LIVE Bitcoin (BTC/USD) prices across different crypto exchanges using the CoinGecko API.
    """

    def load(self) -> MarketContext:
        print("  [Data Loader] Fetching live BTC pricing data from CoinGecko API...")
        
        firm_names = ["Binance", "Coinbase", "Kraken", "KuCoin", "Bitfinex"]
        
        try:
            # We fetch the global average BTC price
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            btc_price = float(data["bitcoin"]["usd"])
            
            # In crypto, "marginal cost" is effectively the market acquisition cost / inventory basis.
            # We will set the marginal cost slightly below the current spot price.
            # We inject slight heterogeneous costs to represent different exchange operational overheads.
            base_cost = btc_price * 0.99
            
            marginal_costs = [
                round(base_cost * 1.000, 2), # Binance (Lowest fee/cost)
                round(base_cost * 1.002, 2), # Coinbase (Higher overhead)
                round(base_cost * 1.001, 2), # Kraken
                round(base_cost * 1.000, 2), # KuCoin
                round(base_cost * 1.001, 2)  # Bitfinex
            ]
            
            return MarketContext(
                dataset_name="Crypto Exchanges (BTC/USD)",
                firm_names=firm_names,
                marginal_costs=marginal_costs,
                price_floor=round(btc_price * 0.95, 2),
                price_ceiling=round(btc_price * 1.05, 2),
                base_quality=90000.0,
                description="high-frequency cryptocurrency exchange. You are a market maker bot setting the spot price for Bitcoin (BTC). The product is perfectly identical.",
                mu=3000.0,
                currency="USD"
            )
        except Exception as e:
            print(f"  [Data Loader] Failed to fetch CoinGecko data: {e}")
            # Fallback
            return MarketContext(
                dataset_name="Crypto Exchanges (Fallback)",
                firm_names=firm_names,
                marginal_costs=[65000, 65100, 65050, 65000, 65050],
                price_floor=60000.0,
                price_ceiling=70000.0,
                base_quality=90000.0,
                description="high-frequency cryptocurrency exchange. You are a market maker bot setting the spot price for Bitcoin (BTC). The product is perfectly identical.",
                mu=3000.0,
                currency="USD"
            )
