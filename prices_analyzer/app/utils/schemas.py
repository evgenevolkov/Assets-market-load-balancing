from pydantic import BaseModel, Field
from typing import List
from uuid import UUID, uuid4

class Asset(BaseModel):
    name: str
    market: str


class PriceBase(BaseModel):
    price_buy: float = Field(gt=0)
    price_sell: float = Field(gt=0)


class PriceBaseAPI(BaseModel):
    price: float = Field(gt=0)
    spread: float = Field(gt=0)


class AssetPrice(Asset, PriceBase):
    pass


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


class AssetData(BaseModel):
    price_buy: float
    price_sell: float
    location_buy: str
    location_sell: str


class checkResponse(AssetData):
    message: str