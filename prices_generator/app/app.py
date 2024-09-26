"""Prices generator app main file

Contains business logic and high level functions

"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import random

from fastapi import FastAPI, HTTPException, status

from .core import assets_manager
from .utils import schemas
from .utils.logger import get_logger
from .utils.utils import get_config_filepath


logger = get_logger(__name__)
thread_pool = ThreadPoolExecutor(max_workers=10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes assets manager and starts infinite prices updade task
    in the background.
    """
    config_filepath = get_config_filepath()
    app.state.assets_manager = assets_manager.AssetsManager(config_filepath)
    logger.debug(app.state.assets_manager.prices_dict)

    app.add_event_handler("startup", start_background_tasks(app))
    yield


def start_background_tasks(app: FastAPI):
    """Starts separate background tasks for updating the prices of each
    asset independently.
    """
    assets_manager = app.state.assets_manager

    for asset_and_market in assets_manager.prices_dict.keys():
        # Create and start a separate task for each asset
        asset = assets_manager.prices_dict[asset_and_market]
        asyncio.create_task(update_asset_price_loop(app, asset))
        logger.debug(f"Update price loop created for asset {asset}")


async def update_asset_price_loop(app: FastAPI, asset: schemas.Asset):
    """
    Independent infinite background task for updating a specific asset's price.
    """
    assets_manager = app.state.assets_manager
    while True:
        assets_manager.update_asset_price(asset)

        # simulate different waiting time update
        sleep_duration = round(random.uniform(1, 3), 1)
        logger.debug((f"Asset's {asset} price is updated."
                      f" Sleep duration: {sleep_duration} s"))
        await asyncio.sleep(sleep_duration)


app = FastAPI(lifespan=lifespan)


@app.get('/price')
async def get_price(asset_name, market) -> schemas.PriceQuoteOut:
    """
    API to provide current asset price at specific market
    """
    try:
        asset = schemas.Asset(name=asset_name, market=market) # validate input
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail=str(e))

    assets_manager = app.state.assets_manager

    price_data = await asyncio.get_event_loop().run_in_executor(
            thread_pool, assets_manager.get_curr_asset_price, asset)
    if price_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail='Asset and market pair not found')

    return price_data