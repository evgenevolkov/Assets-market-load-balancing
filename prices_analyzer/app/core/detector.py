"""
Core Arbitrage Detector Module

Consists of a class, responsible for keeping track of highest and lowest
detected prices and performing arbitrage detection
"""
import asyncio
from typing import Dict, List, Optional

from ..utils import schemas
from ..utils.logger import get_logger


logger = get_logger(__name__)


class ArbitrageDetector:
    """
    Implements arbitrage detector.

    Functionality:
    - Tracks lowest buying and highest selling prices detected,
        including market where price was detected.
    - Provided a new price for an asset, detect arbitrage opportunity
    """

    def __init__(self) -> None:
        self.prices_dict: Dict[str, schemas.AssetData] = {}
        self.assets_list: Optional[List[str]] = None
        self.markets_list: Optional[List[str]] = None
        self.lock = asyncio.Lock()
        self._set_assets_list()
        self._set_markets_list()
        self._initialize_prices()

    def _set_assets_list(self) -> None:
        """Mocks getting and storing a list of assets to track"""
        self.assets_list = ["Copper", "Oil"]

    def _set_markets_list(self) -> None:
        """Mocks getting and storing a list of markets to track"""
        self.markets_list = ["US", "UK"]

    def _initialize_prices(self) -> None:
        """Mocks getting initial prices for each asset"""
        if not self.assets_list:
            raise ValueError("No assets provided")
        for asset in self.assets_list:
            self.prices_dict[asset] = schemas.AssetData(
                price_buy=float('inf'),
                price_sell=0.0,
                location_buy="US",
                location_sell="US")

    async def check_for_arbitrage(
            self,
            asset_price: schemas.AssetPriceFromApi
            ) -> schemas.ArbitrageDetectorResponse:
        """Compares provided asset price with current stored price and
        provides a response indicating if an arbitrage opportunity is
        detected
        """

        response = schemas.ArbitrageDetectorResponse()

        async with self.lock:
            asset_data = self.prices_dict.get(asset_price.name, None)
            if not asset_data:
                return response

            curr_price_buy = asset_data.price_buy
            curr_price_sell = asset_data.price_sell

            new_price_buy = round(
                asset_price.price * (1 + asset_price.spread / 100),
                4)
            new_price_sell = round(
                asset_price.price * (1 - asset_price.spread / 100),
                4)
            new_location = asset_price.market

            if (new_price_buy < curr_price_sell
                    and asset_data.location_sell != new_location):
                message = (
                    "Arbitrage possibility detected:"
                    f" Buy {asset_price.name} from {new_location}"
                    f" for {new_price_buy}"
                    f", sell at {asset_data.location_sell}"
                    f" for {curr_price_sell}, margin:"
                    f" {round(curr_price_sell - new_price_buy, 4)}")
                logger.info(message)
                response.details.append({"message": message})
                response.arbitrage_found = True

            if (new_price_sell > curr_price_buy
                    and asset_data.location_buy != new_location):
                message = (
                    "Arbitrage possibility detected:"
                    f" Buy {asset_price.name} from {asset_data.location_buy}"
                    f" for {curr_price_buy},"
                    f" sell at {new_location} for {new_price_sell},"
                    f" margin: {round(new_price_sell - curr_price_buy, 4)}")
                logger.info(message)
                response.details.append({"message": message})
                response.arbitrage_found = True

        return response

    async def price_update(self,
                           asset_data: schemas.AssetPriceFromApi
                           ) -> None:
        """Asyncroneous wrapper over function implementation. Adds
        timeout functionality to drop execution if takes much longer
        than expected"""
        try:
            # timeout to to prevent long wait time
            await asyncio.wait_for(self._price_update_internal(asset_data),
                                   timeout=2.0)
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout during price update for {asset_data.name}"
                f" in {asset_data.market}")

        return

    async def _price_update_internal(
            self,
            asset_data: schemas.AssetPriceFromApi
            ) -> None:
        """Implementation of price update.
        A price is updated in any of these cases:
        1) the new price comes from the same market as currently stored
            value
        2) the new buying price is lower than the stored one
        3) the new selling price is lower than the stored one
        """
        async with self.lock:
            curr_entry = self.prices_dict.get(asset_data.name, None)

            if not curr_entry:
                logger.error(
                    f"Asset {asset_data.name} not found in prices_dict.")
                return

            new_price_buy = round(
                asset_data.price * (1 + asset_data.spread / 100),
                4)
            new_price_sell = round(
                asset_data.price * (1 - asset_data.spread / 100),
                4)
            new_location = asset_data.market

            logger.debug((
                f"Asset: {asset_data.name}, market: {asset_data.market}"
                f" curr_price_buy: {curr_entry.price_buy}"
                f" new_price_buy: {new_price_buy}"
                f" curr_price_sell: {curr_entry.price_sell}"
                f" new_price_sell: {new_price_sell}"))

            if (new_price_buy < curr_entry.price_buy
                    or new_location == curr_entry.location_buy):
                logger.debug(
                    f"Updating buying price for asset: {asset_data.name}"
                    f", market: {asset_data.market} to {new_price_buy}")
                curr_entry.price_buy = new_price_buy
                curr_entry.location_buy = new_location

            if (new_price_sell > curr_entry.price_sell
                    or new_location == curr_entry.location_sell):
                logger.debug(
                    f"Updating selling price for asset: {asset_data.name}"
                    f", market: {asset_data.market} to {new_price_sell}")
                curr_entry.price_sell = new_price_sell
                curr_entry.location_sell = new_location

            self.prices_dict[asset_data.name] = curr_entry
