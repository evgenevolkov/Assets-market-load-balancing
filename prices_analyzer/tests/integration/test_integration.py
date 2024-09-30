"""Integration tests file"""
import asyncio
import logging
from typing import Any, Union
from unittest.mock import AsyncMock, patch, call, Mock

import pytest
from pydantic import BaseModel

from app.core.detector import ArbitrageDetector
from app.utils.fetch_requests import PriceFetcher
import app.app as app_
main = app_.main


# App executes in infinite loop, thus set an execution timeout for test
# purpose.
MAX_APP_EXECUTION_TIME = 3  # sec
# max test overall execution time
TEST_TIMEOUT = 4  # sec

logger = logging.getLogger(__name__)


class Asset(BaseModel):
    """Asset data schema"""
    name: str
    market: str
    price: float
    spread: float


def check_method_called_with_args(
        mocked_object_method: Mock,
        expected_arguments: Union[dict, Any],
        mocked_object_name: str
) -> None:
    """Helper to make check if a mocked object's method was called with
    expected arguments.
    Arguments can be a dict or any expected obect.
    """
    expected_call = (call(**expected_arguments)
                     if isinstance(expected_arguments, dict)
                     else call(expected_arguments))

    assert (
        expected_call in mocked_object_method.call_args_list
    ), (
        f"\nExpected {mocked_object_name} to be called with arguments: "
        f"{expected_arguments},"
        "\n but actually called with:"
        f"\n {mocked_object_method.call_args_list}"
        "\n Number of calls performed:"
        f" {len(mocked_object_method.call_args_list)}"
    )


mock_price_fetcher = AsyncMock(spec=PriceFetcher)
mock_arbitrage_detector = AsyncMock(spec=ArbitrageDetector)


@pytest.fixture(name="mocked_asset")
def fixture_mocked_asset():
    """mock asset"""

    return Asset(
            asset='Oil',
            market='US',
            price=1000,
            name='Oil',
            spread=0.02
        )


@pytest.mark.asyncio(loop_scope='function')
@pytest.mark.timeout(TEST_TIMEOUT)  # hard timeout for async test
async def test_price_fetching_method_called_at_least_once(
    mocked_asset
):
    """High-level behavior test that runs app for predefined time and
    checks if the app made an attempt to fetch price and check for
    arbitrage in expected manner.

    This test checks that both attempts are done
    and arbitrage detector detectmethod is called in predefined time since
    app is started.
    """

    with (
        patch('app.app.PriceFetcher', return_value=mock_price_fetcher),
        patch('app.app.ArbitrageDetector',
              return_value=mock_arbitrage_detector)
    ):
        mock_price_fetcher.fetch_price.return_value = mocked_asset

        mock_arbitrage_detector.assets_list = ['Oil']
        mock_arbitrage_detector.markets_list = ['UK']

        # to test app behavior while keeping control on execution, start
        # app as an async task and wait predefined time to provide app
        # an opportunity to make expected calls
        main_task = asyncio.create_task(main())
        await asyncio.sleep(MAX_APP_EXECUTION_TIME)
        main_task.cancel()

        # handle main_task cancellation gracefully
        try:
            await main_task
        except asyncio.CancelledError:
            logger.debug("Main function execution terminated as part of the "
                         "test suit.")

    # tests
    mock_price_fetcher.fetch_price.assert_called()
    check_method_called_with_args(
        mocked_object_method=mock_arbitrage_detector.check_for_arbitrage,
        expected_arguments=mocked_asset,
        mocked_object_name='arbitrage_detector'
    )

    mock_arbitrage_detector.check_for_arbitrage.assert_called()
    check_method_called_with_args(
        mocked_object_method=mock_price_fetcher.fetch_price,
        expected_arguments={'asset': 'Oil', 'market': 'UK'},
        mocked_object_name='fetch_price'
    )
