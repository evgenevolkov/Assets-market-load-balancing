"""
Price Analyzer Application

This application tracks prices of assets on different markets and seeks
for arbitrage opportunities.

It relies on two components:

1. PriceFetcher - responsible for performing a request and getting
    current asset price data.

2. ArbitrageDetector - responsible for:
    - tracking lowest purchase and highest sell price of an asset across
    all markets
    - given a current price update for an asset, detects an arbitrage
    possibility by comparing it to stored prices

To achieve this, the application instantiates an asyncroneous task for
each asset and market combination to run infinite loop of price request
and arbitrage detection jobs.

Configurations:

MAX_CONCURRENT_TASKS (environment variable) - number of tasks to be
    executed concurrently
PRICES_REQUEST_INTERVAL_S (environment variable) - min timeout since
    succesfull request. Applies for each asset and market combination
    separately
"""
import asyncio
from decouple import config

from .utils.fetch_requests import PriceFetcher
from .utils.logger import get_logger
from .core.detector import ArbitrageDetector


logger = get_logger(__name__)
semaphore = asyncio.Semaphore(int(config('MAX_CONCURRENT_TASKS')))
prices_request_interval_s = float(config('PRICES_REQUEST_INTERVAL_S'))


async def fetch_and_process_price(
        price_fetcher: PriceFetcher, 
        detector: ArbitrageDetector, asset: str, market: str):
    """High-level function that runs infinite loop to fetch new price of
    an asset on specific market and check for arbitrage opportunity
    """
    while True:
        asset_data = await price_fetcher.fetch_price(asset=asset, market=market)
        if asset_data:
            await detector.check_for_arbitrage(asset_data)
            async with semaphore:
                asyncio.create_task(detector.price_update(asset_data))
                await asyncio.sleep(delay=prices_request_interval_s)


async def main():
    """Initializes application and launches an asynchronous task for
    each asset and market combination
    """
    detector = ArbitrageDetector()
    price_fetcher = PriceFetcher()

    # initialize task for each asset / market pair
    tasks = [
        fetch_and_process_price(price_fetcher, detector, asset, market)
        for asset in detector.assets_list
        for market in detector.markets_list
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
