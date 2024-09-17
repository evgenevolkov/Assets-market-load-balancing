from concurrent.futures import ThreadPoolExecutor
import os
from pydantic import ValidationError
import random
from typing import List, Tuple, Dict, Set

from ..utils.logger import get_logger
from ..utils import schemas
from ..utils.utils import load_yaml_file


logger = get_logger(__name__)


RANDOM = 42
random.seed(RANDOM)


class AssetsManager:
    """
    Manages assets.
    
    Functionality:
    - Reads price config. This includes min and max prices, max spread size etc.
    - Initializes prices
    - Updates prices
    - Return prices 
    """
    price_config: schemas.PriceConfig = None
    prices_dict: Dict[Tuple[str, str], schemas.AssetPrice] = {}


    def __init__(self, price_config_file: str):
        self.price_config = self._get_price_config(price_config_file)
        self.prices_dict = self._construct_prices_dict()
        pass


    def _get_price_config(self, config_file: str) -> schemas.PriceConfig:
        """Helper function to read price config from config file"""
        config_data = load_yaml_file(config_file)
        base_dir = os.path.dirname(config_file) # to get assets and markets location

        assets_file = config_data.get('assets_file')
        markets_file = config_data.get('markets_file')

        assets_file_path = os.path.join(base_dir, assets_file)
        markets_file_path = os.path.join(base_dir, markets_file)
        
        assets_data = load_yaml_file(assets_file_path)
        markets_data = load_yaml_file(markets_file_path)
        
        try:
            price_config = schemas.PriceConfig(
                assets=set(assets_data),#, .get('assets', [])),
                markets=set(markets_data),#.get('markets', [])),
                **config_data.get('price_config', {})
            )
        
        except ValidationError as ve:
            logger.error(f"Validation error when creating PriceConfig: {ve}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error when creating PriceConfig: {e}")
            raise
        
        return price_config


    def _create_base_price(self):
        """Generates random price within allowed range"""
        price_min = self.price_config.price_min
        price_max = self.price_config.price_max
        price = round(
            number = (price_min 
                        + (price_max - price_min) * random.random()),
            ndigits = 4)
        return price
    

    def _set_asset_initial_prices(self, asset_name, max_diff=0.03):
        """Generates asset price for each market. 
        Done in 2 steps:
        1. Generate random base price within range
        2. Iterate over markets and modify base price by market 
           coefficient
        """
        base_price = self._create_base_price()
        markets = self.price_config.markets
        asset_prices = {}
        for market in markets:

            market_coef = random.uniform(-max_diff, max_diff)
            asset_market_price = base_price * (1 + market_coef)
            spread = self._get_new_spread(
                self.price_config.spread_min,
                self.price_config.spread_max
            )

            asset_price = schemas.AssetPrice(
                name=asset_name, 
                market=market, 
                price=asset_market_price, 
                spread=spread
            )

            asset_prices[asset_name, market] = asset_price

        return asset_prices


    def _construct_prices_dict(
            self
            ) -> Dict[Tuple[str, str], schemas.AssetPrice]:
        """Generate price for each asset for each market"""

        config = self.price_config

        assets_price_dict = {}

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._set_asset_initial_prices, 
                                asset_name=asset_name) 
                    for asset_name in config.assets
            ]

            for future in futures:
                asset_price_dict = future.result()
                assets_price_dict.update(asset_price_dict)
                
        return assets_price_dict


    def _get_new_price(self, curr_price: float, price_change_max: float) -> float:
        """Modify provided price by coeficinet randomly defined within 
        range. If resulting price less or equal to 0, recalculates applying  
        maximum allowed positive coefficient instead of randomly selected.
        """
        new_price_coef = random.uniform(- price_change_max, price_change_max)
        new_price = curr_price * (1 + new_price_coef)
        new_price = round(new_price, 4)

        if new_price <= 0:
            new_price = curr_price * (1 + price_change_max)

        return new_price


    def _get_new_spread(self, spread_min, spread_max):
        """Return spread randomly generated within privoded range."""
        new_spread = random.uniform(spread_min, spread_max)
        new_spread = round(new_spread, 1)

        return new_spread


    def update_asset_price(self, asset: schemas.AssetPrice) -> schemas.AssetPrice:
        """High level method to perform price update"""
        asset.price = self._get_new_price(asset.price, self.price_config.price_change_max)
        asset.spread = self._get_new_spread(
            self.price_config.spread_max, self.price_config.spread_min
            )

        self.prices_dict[(asset.name, asset.market)] = asset

        return asset
    

    def get_curr_asset_price(self, asset: schemas.Asset) -> schemas.AssetPrice:
        asset_name = asset.name
        market = asset.market

        asset_price = self.prices_dict.get(tuple([asset_name, market]), None)

        return asset_price
    

    def get_assets_list(self):
        return self.price_config.assets
    

    def get_markets_list(self):
        return self.price_config.markets