from pydantic import BaseModel, Field, field_validator
from typing import List
"""Pydantic data validation schemas"""


class Asset(BaseModel):
    """base Asset properties. Used as foundation for construction more
    compound data schemas, e.g. asset price, etc."""
    name: str
    market: str

    class Config:  # pylint: disable=R0903
        """Make name and market immutable, trim whitespaces, prevent
        empty or too lengthy values
        """
        frozen = True
        str_strip_whitespace = True
        str_min_length = 1
        str_max_length = 64


class PriceBase(BaseModel):
    """base price data; relies on exact buy and sell values;
    validates values to be above zero and selling price below bying;
    This data schema is expected in API response.
    """
    price_buy: float = Field(gt=0)
    price_sell: float = Field(gt=0)

    @field_validator('price_sell')
    @classmethod
    def validate_sell_price(
            cls, price_sell: float, validation_info
            ) -> float:
        """Ensure that selling price is higher that buying price"""
        if price_sell >= validation_info.data['price_buy']:
            raise ValueError('price_sell must be lower than price_buy')
        return price_sell


class PriceBaseAPI(BaseModel):
    """base price data; relies on mid price value and spread;
    validates `price` and `spread` to be greater than zero.
    This data schema is expected in API response
    """
    price: float = Field(gt=0)
    spread: float = Field(gt=0)


class AssetPrice(Asset, PriceBase):
    """Asset price data schema used by Arbitrage detector module"""


class AssetPriceFromApi(Asset, PriceBaseAPI):
    pass


class PriceConfig(BaseModel):
    assets: List[str]
    markets: List[str]
    price_min: float = Field(gt=0)
    price_max: float = Field(gt=0)
    spread_min: float = Field(ge=0)
    spread_max: float = Field(gt=0)
    price_change_max: float = Field(gt=0)
    """Asset price data schema provided by API sources"""


class AssetData(BaseModel):
    """Asset data used by Arbitrage detector to track prices tied to
    locations
    """
    price_buy: float
    price_sell: float
    location_buy: str
    location_sell: str


class ArbitrageDetectorResponse(BaseModel):
    """Arbitrage detector response data model"""
    arbitrage_found: bool = False
    details: list[dict[str, str]] = []
