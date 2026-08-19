from .base import MarketContext
from .gasoline import GasolineDataLoader
from .crypto import CryptoDataLoader
from .amazon import AmazonDataLoader
from .rideshare import RideshareDataLoader
from .airlines import AirlinesDataLoader

def get_data_loader(dataset: str):
    loaders = {
        "gasoline": GasolineDataLoader,
        "crypto": CryptoDataLoader,
        "amazon": AmazonDataLoader,
        "rideshare": RideshareDataLoader,
        "airlines": AirlinesDataLoader,
    }
    
    if dataset not in loaders:
        raise ValueError(f"Unknown dataset '{dataset}'. Choose from: {list(loaders.keys())}")
        
    return loaders[dataset]()
